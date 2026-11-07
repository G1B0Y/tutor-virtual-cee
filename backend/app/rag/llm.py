"""Acceso al modelo de lenguaje detrás de una interfaz (RF-31: cambiar de modelo o motor sin reescribir)."""

import json
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
        if final.get("done_reason") == "length":
            # Llegó al tope: una respuesta del tutor nunca es tan larga, lo más probable es un bucle.
            raise ErrorLLM(f"La respuesta llegó al tope de {self.max_tokens} tokens (posible bucle) y se descartó")
        return "".join(partes).strip()
