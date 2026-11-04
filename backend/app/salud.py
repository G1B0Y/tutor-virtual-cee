"""Revisión del estado de los servicios de los que depende el tutor."""

import httpx
import psycopg

from app.config import Configuracion


def revisar_base(config: Configuracion) -> dict:
    """Comprueba que PostgreSQL responde y que la extensión pgvector está instalada."""
    try:
        with psycopg.connect(config.database_url, connect_timeout=int(config.timeout_salud)) as conexion:
            fila = conexion.execute(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
            ).fetchone()
        if fila is None:
            return {"estado": "error", "detalle": "pgvector no está instalado"}
        return {"estado": "ok", "pgvector": fila[0]}
    except psycopg.Error as error:
        return {"estado": "error", "detalle": type(error).__name__}


def revisar_ollama(config: Configuracion) -> dict:
    """Comprueba que Ollama responde y lista los modelos descargados."""
    try:
        respuesta = httpx.get(f"{config.ollama_url}/api/tags", timeout=config.timeout_salud)
        respuesta.raise_for_status()
        modelos = [m["name"] for m in respuesta.json().get("models", [])]
        if config.llm_modelo not in modelos:
            return {"estado": "error", "detalle": f"falta descargar el modelo {config.llm_modelo}", "modelos": modelos}
        return {"estado": "ok", "modelos": modelos}
    except (httpx.HTTPError, ValueError, KeyError) as error:
        return {"estado": "error", "detalle": type(error).__name__}


def resumen_salud(config: Configuracion) -> dict:
    servicios = {"base": revisar_base(config), "ollama": revisar_ollama(config)}
    todo_ok = all(s["estado"] == "ok" for s in servicios.values())
    return {"estado": "ok" if todo_ok else "degradado", "servicios": servicios}
