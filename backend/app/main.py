"""API del Tutor Virtual 24/7 del CEE FIIS-UNI."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Configuracion, obtener_configuracion
from app.salud import resumen_salud

app = FastAPI(
    title="Tutor Virtual 24/7 – CEE FIIS-UNI",
    description="API del tutor: consulta RAG local, salud y consultas pendientes.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=obtener_configuracion().origenes_permitidos,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/salud", tags=["operación"], summary="Estado de la API, la base y Ollama")
def salud(config: Configuracion = Depends(obtener_configuracion)) -> dict:
    """Siempre responde 200 si la API está viva; `estado` es `degradado` si falla un servicio."""
    return resumen_salud(config)
