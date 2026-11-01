"""Configuración leída de variables de entorno (archivo .env en local)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Cadena de conexión a PostgreSQL + pgvector.
    database_url: str = "postgresql://tutor:tutor@localhost:5432/tutor"
    # Ollama corre en la red interna; nunca se usa un servicio en la nube.
    ollama_url: str = "http://localhost:11434"
    # Orígenes que pueden llamar a la API desde el navegador (widget y campus simulado).
    origenes_permitidos: list[str] = ["http://localhost:5173"]
    # Segundos máximos que se espera a cada servicio en /salud.
    timeout_salud: float = 3.0


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
