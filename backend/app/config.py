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
    origenes_permitidos: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    # Segundos máximos que se espera a cada servicio en /salud.
    timeout_salud: float = 3.0

    # --- RAG (valores iniciales; se calibran en el benchmark de la Fase 2) ---
    # "sentence-transformers" (real) o "hash" (solo pruebas y CI: no entiende significado, solo palabras).
    embeddings_proveedor: str = "sentence-transformers"
    # Elegidos con el benchmark del 07/11/2026 (benchmark/resultados/): e5-small encontró 20/20 respuestas y
    # granite3.3:2b no inventó en ninguna de las 10 preguntas trampa (qwen2.5:1.5b inventó una fecha de inicio).
    embeddings_modelo: str = "intfloat/multilingual-e5-small"
    llm_modelo: str = "granite3.3:2b"
    # Distancia coseno máxima (0 = idéntico, 2 = opuesto) para considerar que un fragmento sirve.
    # Cada modelo de embeddings tiene su escala: estos valores son los que propuso el benchmark para e5-small
    # (con MiniLM eran 0.71 y 0.42). Si se cambia de modelo, se recalibran y se corre `ingesta reindexar`.
    umbral_distancia: float = 0.18
    # Distancia máxima para responder directo con una FAQ, sin LLM.
    umbral_faq: float = 0.10
    fragmentos_por_consulta: int = 4
    largo_maximo_pregunta: int = 500
    # Una sola generación a la vez (RNF-M02); cuántas consultas pueden esperar su turno.
    cola_maxima: int = 3
    # Plazo total de una respuesta (segundos) y tope de largo (tokens). Si se pasa, el chat muestra el fragmento
    # más cercano (sin_llm). Sin tope, qwen2.5:1.5b entró en bucle en el benchmark del 07/11/2026.
    timeout_llm: float = 120.0
    max_tokens_respuesta: int = 512
    # Al arrancar la API, cargar en segundo plano el modelo de embeddings y el de lenguaje
    # (la primera carga en CPU puede tardar minutos).
    precargar_llm: bool = True
    # Fuentes: solo los fragmentos casi tan cercanos como el mejor (mejor distancia + este margen).
    # Va en la escala del modelo de embeddings: con e5-small (dentro ~0,12, fuera ~0,18) 0.10 citaba 4 páginas
    # en vez de 1 o 2. 0.03 es provisional (proporcional al 0.10 que servía con MiniLM); falta calibrarlo.
    margen_fuentes: float = 0.03
    # Control de respaldo (app/rag/respaldo.py): parte mínima de las palabras con contenido de cada oración de la
    # respuesta que debe estar en los documentos o la pregunta; si no, la oración se quita. Los elementos de una lista
    # deben aparecer como frase en los documentos. Regla de Alfredo (08/11/2026): no inventar nada.
    minimo_respaldo: float = 0.6
    # Canal humano: lo define el CEE (pendiente). Se muestra cuando el bot no puede responder.
    mensaje_derivacion: str = (
        "Dejé registrada tu consulta para que el equipo del CEE la revise. "
        "También puedes comunicarte con la coordinación académica del CEE."
    )


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
