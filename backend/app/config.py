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
    # Búsqueda híbrida (app/rag/busqueda.py, 08/11/2026): puntaje = v (cercanía por significado, 0 a 1) +
    # PESO_LEXICO × L (palabras de la pregunta que tiene el fragmento, pesadas por lo raras que son, 0 a 1).
    peso_lexico: float = 1.0
    # Fuentes: solo los fragmentos con un puntaje casi tan alto como el mejor (mejor − este margen). Reemplaza a
    # MARGEN_FUENTES (en distancias de e5: 0.03), que ya no se usa. Provisional: falta calibrarlo con el benchmark.
    margen_puntaje: float = 0.4
    # Si el modelo se abstiene (o el control descarta su respuesta) y el mejor fragmento tiene al menos este puntaje
    # (máx. 2: el más cercano y con todas las palabras de la pregunta), se le pide una segunda vez.
    puntaje_reintento: float = 1.6
    # Control de respaldo (app/rag/respaldo.py): parte mínima de las palabras con contenido de cada oración de la
    # respuesta que debe estar en los documentos o la pregunta; si no, la oración se quita. Los elementos de una lista
    # deben aparecer como frase en los documentos. Regla de Alfredo (08/11/2026): no inventar nada.
    minimo_respaldo: float = 0.6
    # Preguntas de razonamiento (app/rag/razonamiento.py, 09/11/2026: el profesor de Sistemas Integrados
    # Empresariales pregunta casos, porqués y comparaciones): más fragmentos y más margen para juntar ideas de varios
    # módulos, un umbral algo más amplio (el caso usa otras palabras que el documento) y un respaldo mínimo menor
    # (la respuesta usa las palabras del caso y conectores). Provisionales: calibrar con benchmark/preguntas_sie.json.
    fragmentos_razonamiento: int = 6
    margen_razonamiento: float = 0.8
    umbral_razonamiento: float = 0.20
    minimo_respaldo_razonamiento: float = 0.5
    # Con razonamiento, el segundo intento (REINTENTO_RAZONAMIENTO) se pide desde este puntaje: en la PC de Alfredo
    # granite se abstuvo en casos que los módulos sí cubren (09/11/2026). Provisional.
    puntaje_reintento_razonamiento: float = 1.0
    # Preguntas que piden una cantidad ("las cuatro funciones del CRM"): al mejor fragmento se le pegan hasta estos
    # fragmentos siguientes del mismo documento (también de la página siguiente), porque la lista se reparte en varios
    # y granite completaba con elementos inventados (09/11/2026).
    fragmentos_lista: int = 4
    # Preguntas por alumno y por minuto (RF-M06); 0 = sin límite. Con una sola generación a la vez, un alumno que
    # manda muchas seguidas deja esperando a los demás.
    limite_por_minuto: int = 8
    # true solo si la API está detrás de un proxy propio (Nginx en el servidor): entonces la IP del alumno sale de
    # X-Forwarded-For. En local, false (si no, cualquiera podría saltarse el límite inventando la cabecera).
    confiar_en_proxy: bool = False
    # Clave para que el CEE vea las consultas pendientes (cabecera X-Clave-CEE). Vacía = listado desactivado.
    # Va solo en .env, nunca en el repo.
    clave_cee: str = ""
    # Canal humano: lo define el CEE (pendiente). Se muestra cuando el bot no puede responder.
    mensaje_derivacion: str = (
        "Dejé registrada tu consulta para que el equipo del CEE la revise. "
        "También puedes comunicarte con la coordinación académica del CEE."
    )


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
