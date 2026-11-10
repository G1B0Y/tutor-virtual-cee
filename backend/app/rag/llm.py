"""Acceso al modelo de lenguaje detrás de una interfaz (RF-31: cambiar de modelo o motor sin reescribir)."""

import json
import re
import time
from typing import Protocol

import httpx


class ErrorLLM(Exception):
    pass


class LLM(Protocol):
    nombre: str

    def generar(self, mensajes: list[dict[str, str]]) -> str: ...


class LLMOllama:
    """Ollama local. Una sola generación a la vez la controla app.consulta, no esta clase.

    Pide la respuesta en streaming para poder cortarla: con `max_tokens` (num_predict) y con un plazo total.
    Sin eso, qwen2.5:1.5b entró en bucle en el benchmark del 07/11/2026 y escribió 35 000 tokens en 23 min:
    el timeout de httpx solo cuenta la espera entre fragmentos, y Ollama mandaba fragmentos sin parar."""

    def __init__(self, url: str, modelo: str, timeout: float, max_tokens: int = 512):
        self.url = url.rstrip("/")
        self.nombre = modelo
        self.timeout = timeout          # plazo total de una respuesta, en segundos
        self.max_tokens = max_tokens    # tope de largo de la respuesta
        self.ultima: dict | None = None  # mediciones de la última respuesta (las usa el benchmark)

    def precargar(self, timeout: float = 600.0) -> bool:
        """Carga el modelo en memoria sin generar nada. La primera carga puede tardar minutos en CPU;
        así la primera pregunta del día no se pasa del timeout. Devuelve False si no se pudo."""
        try:
            respuesta = httpx.post(f"{self.url}/api/generate", json={"model": self.nombre}, timeout=timeout)
            return respuesta.status_code == 200
        except httpx.HTTPError:
            return False

    def _sin_pensar(self) -> dict:
        """qwen3 "piensa" antes de responder si no se le dice lo contrario: en CPU tarda el doble y el pensamiento
        gasta el tope de tokens. A los demás modelos no se les manda nada (algunos rechazan el campo)."""
        return {"think": False} if self.nombre.startswith("qwen3") else {}

    def generar(self, mensajes: list[dict[str, str]]) -> str:
        inicio = time.monotonic()
        primer_token = None
        partes: list[str] = []
        final: dict = {}
        try:
            with httpx.stream(
                "POST", f"{self.url}/api/chat",
                json={
                    "model": self.nombre,
                    "messages": mensajes,
                    "stream": True,
                    # Respuestas sobrias, cortas y con contexto acotado para caber en el equipo del CEE (RNF-M03).
                    "options": {"temperature": 0.1, "num_ctx": 4096, "num_predict": self.max_tokens},
                    **self._sin_pensar(),
                },
                timeout=self.timeout,
            ) as respuesta:
                if respuesta.status_code == 404:
                    raise ErrorLLM(f"El modelo {self.nombre} no está descargado en Ollama")
                respuesta.raise_for_status()
                for linea in respuesta.iter_lines():
                    if time.monotonic() - inicio > self.timeout:
                        # Cerrar la conexión hace que Ollama deje de generar.
                        raise ErrorLLM(f"La respuesta pasó de {self.timeout:.0f} s y se cortó")
                    if not linea.strip():
                        continue
                    trozo = json.loads(linea)
                    texto = trozo.get("message", {}).get("content", "")
                    if texto and primer_token is None:
                        primer_token = time.monotonic()
                    partes.append(texto)
                    if trozo.get("done"):
                        final = trozo
                        break
        except (httpx.HTTPError, ValueError) as error:
            raise ErrorLLM(f"{type(error).__name__}: {error}") from error
        fin = time.monotonic()
        self.ultima = {
            "ttft_ms": int(((primer_token or fin) - inicio) * 1000),
            "ms_llm": int((fin - inicio) * 1000),
            "tokens": final.get("eval_count", 0),
        }
        texto = sin_pensamiento("".join(partes))
        if final.get("done_reason") == "length":
            # Llegó al tope. Si es un bucle se descarta; si es una respuesta larga (granite razonando sobre el CRM y el
            # marketing, 09/11/2026), se queda hasta la última oración completa y el control de respaldo la revisa.
            recortado = recortar_al_tope(texto)
            if recortado is None:
                raise ErrorLLM(f"La respuesta llegó al tope de {self.max_tokens} tokens (posible bucle) y se descartó")
            return recortado
        return texto


_FIN_DE_ORACION = re.compile(r"[.!?»\"](?=\s|$)")


def es_bucle(texto: str) -> bool:
    """Una oración (de más de 20 caracteres) repetida 3 veces o más, o muy pocas palabras distintas al final."""
    oraciones = [" ".join(o.lower().split()) for o in re.split(r"(?<=[.!?])\s+", texto) if len(o.strip()) > 20]
    if any(oraciones.count(o) >= 3 for o in set(oraciones)):
        return True
    palabras = texto.lower().split()[-200:]
    return len(palabras) >= 60 and len(set(palabras)) / len(palabras) < 0.25


def recortar_al_tope(texto: str, minimo: int = 40) -> str | None:
    """Una respuesta cortada por el tope de tokens: hasta su última oración completa. None si es un bucle o si
    no queda ni una oración completa."""
    if es_bucle(texto):
        return None
    finales = list(_FIN_DE_ORACION.finditer(texto))
    if not finales:
        return None
    recortado = texto[: finales[-1].end()].strip()
    return recortado if len(recortado) >= minimo else None


_PENSAMIENTO = re.compile(r"<think>.*?(</think>|$)", re.DOTALL | re.IGNORECASE)


def sin_pensamiento(texto: str) -> str:
    """qwen3 puede escribir su razonamiento entre <think> y </think> dentro de la respuesta (según la versión de
    Ollama, aunque se le pida no pensar). El control de respaldo lo tomaba como la primera oración y descartaba
    respuestas buenas (benchmark del curso SIE, 09/11/2026). Un <think> sin cerrar (cortado por el tope) se quita
    entero."""
    return _PENSAMIENTO.sub("", texto).strip()
