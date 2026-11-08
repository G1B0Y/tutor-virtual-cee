"""API del Tutor Virtual 24/7 del CEE FIIS-UNI."""

import hmac
import logging
import threading
from datetime import datetime
from contextlib import asynccontextmanager
from functools import lru_cache

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import Configuracion, obtener_configuracion
from app import pendientes
from app.consulta import Respuesta, Turno, responder
from app.limites import LimitePorMinuto, clave_del_alumno
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
def obtener_limite() -> LimitePorMinuto:
    return LimitePorMinuto(obtener_configuracion().limite_por_minuto)


def revisar_limite(
    request: Request,
    limite: LimitePorMinuto = Depends(obtener_limite),
    config: Configuracion = Depends(obtener_configuracion),
) -> None:
    ip = request.client.host if request.client else None
    espera = limite.esperar(clave_del_alumno(ip, request.headers.get("x-forwarded-for"), config.confiar_en_proxy))
    if espera:
        segundos = max(1, round(espera))
        raise HTTPException(
            status_code=429,
            detail=f"Hiciste muchas preguntas seguidas. Espera {segundos} s y vuelve a intentarlo.",
            headers={"Retry-After": str(segundos)},
        )


def revisar_clave_cee(
    x_clave_cee: str | None = Header(default=None, description="Clave del equipo del CEE"),
    config: Configuracion = Depends(obtener_configuracion),
) -> None:
    if not config.clave_cee:
        raise HTTPException(status_code=503, detail="El listado de consultas pendientes no está activado (CLAVE_CEE).")
    if not x_clave_cee or not hmac.compare_digest(x_clave_cee.encode(), config.clave_cee.encode()):
        raise HTTPException(status_code=401, detail="Clave del CEE incorrecta.")


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
    anterior: str | None = Field(
        default=None, max_length=500,
        description="Pregunta previa del alumno en el mismo chat, para entender seguimientos. No se guarda.",
    )
    documento: str | None = Field(
        default=None, max_length=300,
        description="Documento de la respuesta previa (título de su primera fuente), para seguimientos. No se guarda.",
    )


class ConsultaPendiente(BaseModel):
    id: int
    pregunta: str
    motivo: str
    creada_en: datetime
    atendida_en: datetime | None
    nota_atencion: str | None


class Atencion(BaseModel):
    nota: str | None = Field(default=None, max_length=1000, description="Qué se hizo (p. ej. se agregó una FAQ)")


@app.get("/salud", tags=["operación"], summary="Estado de la API, la base y Ollama")
def salud(config: Configuracion = Depends(obtener_configuracion)) -> dict:
    """Siempre responde 200 si la API está viva; `estado` es `degradado` si falla un servicio."""
    return resumen_salud(config)


@app.post("/consulta", tags=["tutor"], summary="Responde una pregunta con los materiales del CEE")
def consulta(
    datos: Pregunta,
    _limite: None = Depends(revisar_limite),
    conexion: psycopg.Connection = Depends(obtener_conexion),
    emb: Embeddings = Depends(obtener_embeddings),
    llm: LLM = Depends(obtener_llm),
    turno: Turno = Depends(obtener_turno),
    config: Configuracion = Depends(obtener_configuracion),
) -> Respuesta:
    """`estado`: respondida, faq, orientacion (saludo o pregunta sobre el tutor), sin_evidencia (se abstiene y
    deriva), sin_llm (modelo caído) u ocupado. 429 si el alumno pasó el límite de preguntas por minuto."""
    return responder(datos.pregunta, conexion, emb, llm, turno, config, datos.anterior, datos.documento)


@app.get(
    "/consultas-pendientes",
    tags=["CEE"],
    summary="Consultas que el tutor no pudo responder",
    dependencies=[Depends(revisar_clave_cee)],
)
def consultas_pendientes(
    incluir_atendidas: bool = Query(default=False),
    conexion: psycopg.Connection = Depends(obtener_conexion),
) -> list[ConsultaPendiente]:
    """Solo para el equipo del CEE (cabecera `X-Clave-CEE`). Las más recientes primero; no hay datos del alumno."""
    return [ConsultaPendiente(**vars(c)) for c in pendientes.listar(conexion, incluir_atendidas)]


@app.post(
    "/consultas-pendientes/{id_consulta}/atendida",
    tags=["CEE"],
    summary="Marcar una consulta pendiente como atendida",
    dependencies=[Depends(revisar_clave_cee)],
)
def atender_consulta(
    id_consulta: int,
    datos: Atencion,
    conexion: psycopg.Connection = Depends(obtener_conexion),
) -> dict:
    if not pendientes.marcar_atendida(conexion, id_consulta, datos.nota):
        raise HTTPException(status_code=404, detail="No existe esa consulta pendiente o ya estaba atendida.")
    return {"id": id_consulta, "atendida": True}
