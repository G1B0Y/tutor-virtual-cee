"""API del Tutor Virtual 24/7 del CEE FIIS-UNI."""

import logging
import threading
from contextlib import asynccontextmanager
from functools import lru_cache

import psycopg
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import Configuracion, obtener_configuracion
from app.consulta import Respuesta, Turno, responder
from app.rag.embeddings import Embeddings, crear_embeddings
from app.rag.llm import LLM, LLMOllama
from app.salud import resumen_salud

registro = logging.getLogger("tutor")
registro.setLevel(logging.INFO)
if not registro.handlers:  # sin handler propio, los INFO se perdían (solo salían los avisos)
    _salida = logging.StreamHandler()
    _salida.setFormatter(logging.Formatter("%(levelname)s:     %(message)s"))
    registro.addHandler(_salida)


def precargar_modelos(config: Configuracion, llm: LLMOllama) -> None:
    """Embeddings primero (los usa toda consulta, también las FAQ) y luego el modelo de lenguaje."""
    try:
        crear_embeddings(config.embeddings_proveedor, config.embeddings_modelo)
        registro.info("Modelo de embeddings listo: %s", config.embeddings_modelo)
    except Exception as error:  # noqa: BLE001 - la API debe arrancar igual y avisar
        registro.warning("No se pudo cargar el modelo de embeddings: %s", error)
    if llm.precargar():
        registro.info("Modelo %s cargado en memoria", llm.nombre)
    else:
        registro.warning("No se pudo precargar %s: la primera pregunta tardará más", llm.nombre)


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    config = obtener_configuracion()
    if config.precargar_llm:
        # En segundo plano: la API ya responde /salud mientras Ollama carga el modelo.
        llm = LLMOllama(config.ollama_url, config.llm_modelo, config.timeout_llm, config.max_tokens_respuesta)
        threading.Thread(target=precargar_modelos, args=(config, llm), daemon=True).start()
    yield


app = FastAPI(
    lifespan=ciclo_de_vida,
    title="Tutor Virtual 24/7 – CEE FIIS-UNI",
    description="API del tutor: consulta RAG local, salud y consultas pendientes.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=obtener_configuracion().origenes_permitidos,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@lru_cache
def obtener_turno() -> Turno:
    return Turno(obtener_configuracion().cola_maxima)


def obtener_embeddings(config: Configuracion = Depends(obtener_configuracion)) -> Embeddings:
    return crear_embeddings(config.embeddings_proveedor, config.embeddings_modelo)


def obtener_llm(config: Configuracion = Depends(obtener_configuracion)) -> LLM:
    return LLMOllama(config.ollama_url, config.llm_modelo, config.timeout_llm, config.max_tokens_respuesta)


def obtener_conexion(config: Configuracion = Depends(obtener_configuracion)):
    with psycopg.connect(config.database_url) as conexion:
        yield conexion


class Pregunta(BaseModel):
    pregunta: str = Field(min_length=2, max_length=500, description="Pregunta del alumno en español")


@app.get("/salud", tags=["operación"], summary="Estado de la API, la base y Ollama")
def salud(config: Configuracion = Depends(obtener_configuracion)) -> dict:
    """Siempre responde 200 si la API está viva; `estado` es `degradado` si falla un servicio."""
    return resumen_salud(config)


@app.post("/consulta", tags=["tutor"], summary="Responde una pregunta con los materiales del CEE")
def consulta(
    datos: Pregunta,
    conexion: psycopg.Connection = Depends(obtener_conexion),
    emb: Embeddings = Depends(obtener_embeddings),
    llm: LLM = Depends(obtener_llm),
    turno: Turno = Depends(obtener_turno),
    config: Configuracion = Depends(obtener_configuracion),
) -> Respuesta:
    """`estado`: respondida, faq, orientacion (saludo o pregunta sobre el tutor), sin_evidencia (se abstiene y
    deriva), sin_llm (modelo caído) u ocupado."""
    return responder(datos.pregunta, conexion, emb, llm, turno, config)
