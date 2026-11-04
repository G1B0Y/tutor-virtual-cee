"""Acceso al modelo de lenguaje detrás de una interfaz (RF-31: cambiar de modelo o motor sin reescribir)."""

from typing import Protocol

import httpx


class ErrorLLM(Exception):
    pass


class LLM(Protocol):
    nombre: str

    def generar(self, mensajes: list[dict[str, str]]) -> str: ...


class LLMOllama:
    """Ollama local. Una sola generación a la vez la controla app.consulta, no esta clase."""

    def __init__(self, url: str, modelo: str, timeout: float):
        self.url = url.rstrip("/")
        self.nombre = modelo
        self.timeout = timeout

    def precargar(self, timeout: float = 600.0) -> bool:
        """Carga el modelo en memoria sin generar nada. La primera carga puede tardar minutos en CPU;
        así la primera pregunta del día no se pasa del timeout. Devuelve False si no se pudo."""
        try:
            respuesta = httpx.post(f"{self.url}/api/generate", json={"model": self.nombre}, timeout=timeout)
            return respuesta.status_code == 200
        except httpx.HTTPError:
            return False

    def generar(self, mensajes: list[dict[str, str]]) -> str:
        try:
            respuesta = httpx.post(
                f"{self.url}/api/chat",
                json={
                    "model": self.nombre,
                    "messages": mensajes,
                    "stream": False,
                    # Respuestas sobrias y contexto acotado para caber en el equipo del CEE (RNF-M03).
                    "options": {"temperature": 0.1, "num_ctx": 4096},
                },
                timeout=self.timeout,
            )
            if respuesta.status_code == 404:
                raise ErrorLLM(f"El modelo {self.nombre} no está descargado en Ollama")
            respuesta.raise_for_status()
            return respuesta.json()["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, ValueError) as error:
            raise ErrorLLM(f"{type(error).__name__}: {error}") from error
