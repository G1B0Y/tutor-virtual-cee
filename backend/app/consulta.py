"""Responde una pregunta del alumno: FAQ → búsqueda → LLM, con abstención y degradación controlada."""

import threading
import time
from dataclasses import dataclass, field

import psycopg

from app.config import Configuracion
from app.conversacion import respuesta_de_conversacion
from app.rag.busqueda import FragmentoEncontrado, buscar_faq, buscar_fragmentos
from app.rag.embeddings import Embeddings
from app.rag.llm import LLM, ErrorLLM
from app.rag.prompt import armar_mensajes, es_sin_evidencia, limpiar_respuesta

# Estados que entiende el chat.
RESPONDIDA = "respondida"          # el LLM redactó con los documentos
FAQ = "faq"                        # respuesta validada, sin LLM
SIN_EVIDENCIA = "sin_evidencia"    # no hay material suficiente: se abstiene y deriva (RF-M03)
SIN_LLM = "sin_llm"                # el modelo no está disponible: muestra el fragmento más relevante (RNF-04)
OCUPADO = "ocupado"                # la cola está llena (RF-M06)
ORIENTACION = "orientacion"        # saludo o pregunta sobre el tutor: texto fijo, sin buscar ni registrar pendiente


@dataclass
class Fuente:
    titulo: str
    pagina: int | None


@dataclass
class Respuesta:
    estado: str
    respuesta: str
    fuentes: list[Fuente] = field(default_factory=list)
    ms: int = 0


class Turno:
    """Una generación a la vez; hasta `cola_maxima` consultas esperando. Si no hay lugar: ocupado."""

    def __init__(self, cola_maxima: int):
        self._generando = threading.Semaphore(1)
        self._lugares = threading.Semaphore(cola_maxima + 1)

    def tomar(self) -> bool:
        if not self._lugares.acquire(blocking=False):
            return False
        self._generando.acquire()
        return True

    def liberar(self) -> None:
        self._generando.release()
        self._lugares.release()


def _fuentes(fragmentos: list[FragmentoEncontrado]) -> list[Fuente]:
    vistas: list[Fuente] = []
    for f in fragmentos:
        fuente = Fuente(f.titulo, f.pagina)
        if fuente not in vistas:
            vistas.append(fuente)
    return vistas


def texto_para_buscar(texto: str) -> str:
    """Si el alumno escribe casi todo en MAYÚSCULAS (pasa mucho desde el celular), lo pasa a minúsculas para el
    embedding: con e5-small "DAME UN RESUMEN DEL TEMA UNO" quedaba a 0,216 del temario y en minúsculas, a 0,16
    (08/11/2026). Las siglas sueltas en un texto normal (PMBOK, EOQ) se dejan."""
    letras = [c for c in texto if c.isalpha()]
    if len(letras) >= 8 and sum(c.isupper() for c in letras) / len(letras) > 0.6:
        return texto.lower()
    return texto


def seleccionar(encontrados: list[FragmentoEncontrado], umbral: float, margen: float) -> list[FragmentoEncontrado]:
    """Fragmentos bajo el umbral y casi tan cercanos como el mejor: son los que se dan al modelo y se citan."""
    utiles = [f for f in encontrados if f.distancia <= umbral]
    if not utiles:
        return []
    mejor = min(f.distancia for f in utiles)
    return [f for f in utiles if f.distancia <= mejor + margen]


def _registrar(conexion: psycopg.Connection, r: Respuesta, pregunta: str, modelo: str | None,
               config: Configuracion) -> None:
    conexion.execute(
        "INSERT INTO eventos (tipo, estado, ms_total, modelo) VALUES ('consulta', %s, %s, %s)", (r.estado, r.ms, modelo)
    )
    if r.estado == SIN_EVIDENCIA:
        conexion.execute(
            "INSERT INTO consultas_pendientes (pregunta, motivo) VALUES (%s, 'sin_evidencia')",
            (pregunta[: config.largo_maximo_pregunta],),
        )


def responder(pregunta: str, conexion: psycopg.Connection, emb: Embeddings, llm: LLM, turno: Turno,
              config: Configuracion, anterior: str | None = None) -> Respuesta:
    """`anterior`: la pregunta previa del alumno en el mismo chat (la manda el navegador; no se guarda). Se usa
    solo si la pregunta sola no encuentra nada, para entender seguimientos como "dame un resumen de ese curso"."""
    inicio = time.monotonic()
    pregunta = " ".join(pregunta.split())
    anterior = " ".join((anterior or "").split()) or None

    def terminar(r: Respuesta, modelo: str | None = None) -> Respuesta:
        r.ms = int((time.monotonic() - inicio) * 1000)
        _registrar(conexion, r, pregunta, modelo, config)
        return r

    fija = respuesta_de_conversacion(pregunta)
    if fija:
        return terminar(Respuesta(ORIENTACION, fija))

    vector = emb.codificar([texto_para_buscar(pregunta)], es_consulta=True)[0]

    faq = buscar_faq(conexion, vector)
    if faq and faq.distancia <= config.umbral_faq:
        return terminar(Respuesta(FAQ, faq.respuesta, [Fuente(faq.fuente or "Preguntas frecuentes del CEE", None)]))

    encontrados = buscar_fragmentos(conexion, vector, config.fragmentos_por_consulta)
    utiles = seleccionar(encontrados, config.umbral_distancia, config.margen_fuentes)
    contexto = None
    if not utiles and anterior and not respuesta_de_conversacion(anterior):
        # Seguimiento: "estoy llevando ese curso, dame un resumen del tema uno" no dice qué curso (08/11/2026).
        juntas = emb.codificar([f"{texto_para_buscar(anterior)}. {texto_para_buscar(pregunta)}"], es_consulta=True)[0]
        encontrados = buscar_fragmentos(conexion, juntas, config.fragmentos_por_consulta)
        utiles = seleccionar(encontrados, config.umbral_distancia, config.margen_fuentes)
        contexto = anterior if utiles else None
    if not utiles:
        return terminar(Respuesta(SIN_EVIDENCIA, "No encontré esa información en los materiales del CEE. "
                                  + config.mensaje_derivacion))

    if not turno.tomar():
        return terminar(Respuesta(OCUPADO, "Hay muchas consultas en este momento. Intenta de nuevo en un minuto."))
    try:
        texto = llm.generar(armar_mensajes(pregunta, utiles, contexto))
    except ErrorLLM:
        mejor = utiles[0]
        return terminar(Respuesta(
            SIN_LLM,
            "En este momento no puedo redactar una respuesta, pero encontré esto en los materiales del CEE:\n\n"
            f"«{mejor.texto}»",
            _fuentes([mejor]),
        ))
    finally:
        turno.liberar()

    if es_sin_evidencia(texto):
        return terminar(Respuesta(SIN_EVIDENCIA, "No encontré esa información en los materiales del CEE. "
                                  + config.mensaje_derivacion), llm.nombre)
    return terminar(Respuesta(RESPONDIDA, limpiar_respuesta(texto), _fuentes(utiles)), llm.nombre)
