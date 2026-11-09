"""Responde una pregunta del alumno: FAQ → búsqueda → LLM, con abstención y degradación controlada."""

import logging
import re
import threading
import time
from dataclasses import dataclass, field, replace

import psycopg

from app.config import Configuracion
from app.conversacion import respuesta_de_conversacion
from app.rag.busqueda import (FragmentoEncontrado, buscar_faq, buscar_fragmentos, fragmentos_que_dicen,
                               siguiente_fragmento, terminos)
from app.rag.embeddings import Embeddings
from app.rag.llm import LLM, ErrorLLM
from app.rag.prompt import SIN_EVIDENCIA as SIN_EVIDENCIA_DEL_MODELO
from app.rag.razonamiento import es_razonamiento
from app.rag.prompt import (REINTENTO, REINTENTO_RAZONAMIENTO, armar_mensajes, es_sin_evidencia, limpiar_respuesta,
                            mensajes_de_reintento)
from app.rag.respaldo import cantidad_pedida, revisar

registro = logging.getLogger("tutor")

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


_NUMEROS = {"uno": "1", "primer": "1", "primero": "1", "primera": "1", "dos": "2", "segundo": "2", "segunda": "2",
            "tres": "3", "tercer": "3", "tercero": "3", "tercera": "3", "cuatro": "4", "cuarto": "4", "cuarta": "4",
            "cinco": "5", "quinto": "5", "quinta": "5", "seis": "6", "sexto": "6", "sexta": "6"}
_N = "|".join(sorted(_NUMEROS, key=len, reverse=True)) + r"|\d+"
_TEMA_N = re.compile(rf"\b(tema|unidad|m[oó]dulo|cap[ií]tulo)\s+({_N})\b", re.IGNORECASE)
_N_TEMA = re.compile(rf"\b({_N})\s+(tema|unidad|m[oó]dulo|cap[ií]tulo)\b", re.IGNORECASE)


def _numero(palabra: str) -> str:
    return _NUMEROS.get(palabra.lower(), palabra)


def texto_para_buscar(texto: str) -> str:
    """Ajusta la pregunta solo para el embedding (al modelo le llega tal cual):
    - Casi todo en MAYÚSCULAS (pasa mucho desde el celular) → minúsculas: con e5-small "DAME UN RESUMEN DEL TEMA UNO"
      quedaba a 0,216 del temario y en minúsculas, a 0,16 (08/11/2026). Las siglas sueltas (PMBOK, EOQ) se dejan.
    - "tema uno", "primer tema", "módulo dos" → "unidad 1", "unidad 2"…: los temarios dicen "Unidad 1" y "tema uno"
      se parecía más a otras unidades."""
    letras = [c for c in texto if c.isalpha()]
    if len(letras) >= 8 and sum(c.isupper() for c in letras) / len(letras) > 0.6:
        texto = texto.lower()
    texto = _TEMA_N.sub(lambda m: f"{'unidad' if m[1].lower() == 'tema' else m[1]} {_numero(m[2])}", texto)
    return _N_TEMA.sub(lambda m: f"{'unidad' if m[2].lower() == 'tema' else m[2]} {_numero(m[1])}", texto)


_SEGUIMIENTO = re.compile(
    r"\b(ese|esa|eso|esos|esas|aquel|aquella|dicho|dicha|mismo|misma)\b"
    r"|\b(este|esta|estos|estas) (curso|cursos|programa|tema|temas|modulo|unidad|separata|temario|documento)\b"
    r"|^(y|e|entonces|osea|o sea)\b"
)
_UNIDAD_N = re.compile(r"\bunidad (\d+)\b")


def es_seguimiento(pregunta: str) -> bool:
    """La pregunta depende de la anterior: "ese curso", "¿y el tema dos?", "explícame eso"."""
    from app.conversacion import _normalizar

    return bool(_SEGUIMIENTO.search(_normalizar(pregunta)))


def seleccionar(encontrados: list[FragmentoEncontrado], umbral: float, margen: float) -> list[FragmentoEncontrado]:
    """Fragmentos bajo el umbral de distancia y con un puntaje casi tan alto como el mejor (búsqueda híbrida):
    son los que se dan al modelo y se citan."""
    utiles = [f for f in encontrados if f.distancia <= umbral]
    if not utiles:
        return []
    mejor = max(f.puntaje for f in utiles)
    return sorted([f for f in utiles if f.puntaje >= mejor - margen], key=lambda f: f.puntaje, reverse=True)


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


_SIGLA = re.compile(r"\b([A-Za-zÑñ]{3,5})\b")


def _por_sigla(conexion: psycopg.Connection, vector: list[float], pregunta: str) -> list[FragmentoEncontrado]:
    """"¿Qué es un VSM?" casi no tiene texto y la búsqueda por significado no llega al temario, que sí dice
    "mapa de flujo de valor (VSM)" (08/11/2026). Si una palabra corta de la pregunta aparece EN MAYÚSCULAS en un
    documento (una sigla), se toma el fragmento más cercano que la contiene."""
    for palabra in _SIGLA.findall(pregunta):
        sigla = palabra.upper()
        encontrados = fragmentos_que_dicen(conexion, vector, None, rf"\m{sigla}\M", 1, mayusculas=True)
        if encontrados:
            return encontrados
    return []


def _con_unidad_pedida(conexion: psycopg.Connection, vector: list[float], pregunta: str,
                       utiles: list[FragmentoEncontrado]) -> list[FragmentoEncontrado]:
    """Si piden "unidad N", asegura que vaya al modelo el fragmento del documento que dice "Unidad N": en el temario
    de PMBOK el que más se parecía era el de las unidades 3 y 4, y el modelo llamó "tema uno" a Costos (08/11/2026)."""
    pedida = _UNIDAD_N.search(texto_para_buscar(pregunta).lower())
    if not pedida or not utiles:
        return utiles
    titulo = utiles[0].titulo
    if any(re.search(rf"\bunidad\s+{pedida[1]}\b", f.texto, re.IGNORECASE) for f in utiles if f.titulo == titulo):
        return utiles
    extra = fragmentos_que_dicen(conexion, vector, titulo, rf"\munidad\s+{pedida[1]}\M", 1)
    return extra + [f for f in utiles if f not in extra]


def _unir(primero: str, segundo: str) -> str:
    """Junta dos fragmentos seguidos sin repetir la oración que comparten (los fragmentos se solapan en una)."""
    for k in range(min(len(primero), len(segundo), 400), 9, -1):
        if primero.endswith(segundo[:k]):
            return primero + segundo[k:]
    return f"{primero} {segundo}"


def _con_continuacion(conexion: psycopg.Connection, vector: list[float], pregunta: str,
                      utiles: list[FragmentoEncontrado]) -> list[FragmentoEncontrado]:
    """Si el mejor fragmento termina hablando de lo que se pregunta o en ":" (una lista cortada), el tema sigue en el
    fragmento siguiente: se le pega al mejor, como un solo texto. "Principios del PMBOK 8.ª edición": el fragmento
    terminaba en "Octava edición (noviembre de 2025):" y la lista estaba en el que sigue (08/11/2026). Primero iba
    como otro documento y granite igual respondía con los 12 principios de la séptima edición, que estaban en el
    primero; juntos, la lista queda justo después de "Octava edición"."""
    if not utiles:
        return utiles
    mejor = utiles[0]
    cola = mejor.texto[-200:]
    if not cola.rstrip().endswith(":") and not set(terminos(cola)) & set(terminos(pregunta)):
        return utiles
    siguiente = siguiente_fragmento(conexion, vector, mejor)
    if not siguiente:
        return utiles
    unido = replace(mejor, texto=_unir(mejor.texto, siguiente.texto))
    return [unido, *(f for f in utiles[1:] if (f.titulo, f.orden) != (siguiente.titulo, siguiente.orden))]


def _con_lista_pedida(conexion: psycopg.Connection, vector: list[float], pregunta: str,
                      utiles: list[FragmentoEncontrado], cuantos: int,
                      largo_maximo: int = 4000) -> list[FragmentoEncontrado]:
    """"¿Cuáles son las cuatro funciones del CRM?": en el módulo de CRM las funciones A–D ocupan 5 fragmentos de dos
    páginas y granite veía solo A y B y completaba con dos inventadas (el control descartó la lista, 09/11/2026). Si la
    pregunta pide una cantidad, se pegan al mejor fragmento los siguientes del mismo documento, como un solo texto."""
    if not utiles or not cantidad_pedida(pregunta) or cuantos <= 0:
        return utiles
    actual = unido = utiles[0]
    usados = {(actual.titulo, actual.orden)}
    for _ in range(cuantos):
        siguiente = siguiente_fragmento(conexion, vector, actual)
        if not siguiente or len(unido.texto) + len(siguiente.texto) > largo_maximo:
            break
        unido = replace(unido, texto=_unir(unido.texto, siguiente.texto))
        usados.add((siguiente.titulo, siguiente.orden))
        actual = siguiente
    if unido is utiles[0]:
        return utiles
    return [unido, *(f for f in utiles[1:] if (f.titulo, f.orden) not in usados)][:3]


def responder(pregunta: str, conexion: psycopg.Connection, emb: Embeddings, llm: LLM, turno: Turno,
              config: Configuracion, anterior: str | None = None, documento_anterior: str | None = None) -> Respuesta:
    """Seguimientos (los manda el navegador; no se guardan): `anterior` es la pregunta previa del alumno en el mismo
    chat y `documento_anterior`, el documento de la respuesta previa. Se usan si la pregunta se refiere a algo
    anterior ("ese curso", "¿y el tema dos?") o si sola no encuentra nada."""
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

    # Casos, porqués y comparaciones (09/11/2026): más fragmentos y margen, umbral algo más amplio.
    razonar = es_razonamiento(pregunta)
    limite = config.fragmentos_razonamiento if razonar else config.fragmentos_por_consulta
    margen = config.margen_razonamiento if razonar else config.margen_puntaje
    umbral = max(config.umbral_razonamiento, config.umbral_distancia) if razonar else config.umbral_distancia

    def buscar(v: list[float], texto: str, limite: int, titulo: str | None = None) -> list[FragmentoEncontrado]:
        return buscar_fragmentos(conexion, v, limite, titulo, texto, umbral, config.peso_lexico)

    encontrados = buscar(vector, pregunta, limite)
    utiles = seleccionar(encontrados, umbral, margen)
    contexto = None
    if not utiles:
        utiles = _por_sigla(conexion, vector, pregunta)  # antes que el seguimiento: la sigla dice dónde buscar
    hay_anterior = bool(anterior or documento_anterior) and not (anterior and respuesta_de_conversacion(anterior))
    corta = len(pregunta.split()) <= 3  # "¿y el VSM?", "que es eso": casi siempre siguen la conversación
    if hay_anterior and (not utiles or es_seguimiento(pregunta) or (corta and documento_anterior)):
        # Seguimiento (08/11/2026): "estoy llevando ese curso, dame un resumen del tema uno" no dice qué curso.
        # "Ese curso" es el documento de la respuesta anterior (lo reenvía el chat) o, si no vino, el que encuentra
        # la pregunta anterior. Se busca solo en él para no mezclar cursos.
        documento = documento_anterior
        if not documento and anterior:
            previo = buscar(emb.codificar([texto_para_buscar(anterior)], es_consulta=True)[0], anterior, 1)
            documento = previo[0].titulo if previo and previo[0].distancia <= umbral else None
        texto = f"{texto_para_buscar(anterior)}. {texto_para_buscar(pregunta)}" if anterior else texto_para_buscar(pregunta)
        juntas = emb.codificar([texto], es_consulta=True)[0]
        en_documento = seleccionar(buscar(juntas, f"{anterior or ''} {pregunta}", limite,
                                          documento),
                                   umbral, margen) if documento else []
        if en_documento:
            utiles, contexto = en_documento, anterior
        elif not utiles:
            utiles = seleccionar(buscar(juntas, f"{anterior or ''} {pregunta}", limite), umbral, margen)
            contexto = anterior if utiles else None
    utiles = _con_unidad_pedida(conexion, vector, pregunta, utiles)
    if not utiles:
        return terminar(Respuesta(SIN_EVIDENCIA, "No encontré esa información en los materiales del CEE. "
                                  + config.mensaje_derivacion))

    lista = _con_lista_pedida(conexion, vector, pregunta, utiles, config.fragmentos_lista)
    utiles = lista if lista is not utiles else _con_continuacion(conexion, vector, pregunta, utiles)

    def revisado(texto: str) -> str:
        if es_sin_evidencia(texto):
            return texto
        # Lo mismo que vio el modelo: número, título y página de cada documento (puede citarlos) y su texto.
        vistos = [f"[{n}] {f.titulo}, página {f.pagina or ''}. {f.texto}" for n, f in enumerate(utiles, 1)]
        resultado, motivo = revisar(limpiar_respuesta(texto), vistos,
                                    f"{anterior or ''} {pregunta} {texto_para_buscar(pregunta)}",
                                    config.minimo_respaldo_razonamiento if razonar else config.minimo_respaldo)
        if resultado is None:
            registro.warning("Respuesta descartada: %s", motivo)
            return SIN_EVIDENCIA_DEL_MODELO
        if motivo:
            registro.info("Respuesta recortada: %s", motivo)
        return resultado

    if not turno.tomar():
        return terminar(Respuesta(OCUPADO, "Hay muchas consultas en este momento. Intenta de nuevo en un minuto."))
    try:
        mensajes = armar_mensajes(pregunta, utiles, contexto, razonar)
        if razonar:
            registro.info("Pregunta de razonamiento: %d fragmentos al modelo", len(utiles))
        texto = revisado(llm.generar(mensajes))
        reintento = config.puntaje_reintento_razonamiento if razonar else config.puntaje_reintento
        if es_sin_evidencia(texto) and utiles[0].puntaje >= reintento:
            # granite varía: con los mismos documentos respondió bien el OEE y el Cpk en una ronda y en otra se
            # abstuvo, o escribió las 5S con nombres y kanji inventados (08/11/2026). Si la evidencia es fuerte
            # (el fragmento tiene casi todas las palabras de la pregunta) se le pide una vez más.
            registro.info("Segundo intento: había evidencia fuerte (puntaje %.2f)", utiles[0].puntaje)
            aviso = REINTENTO_RAZONAMIENTO if razonar else REINTENTO
            texto = revisado(llm.generar(mensajes_de_reintento(mensajes, aviso)))
        elif es_sin_evidencia(texto):
            # Para calibrar PUNTAJE_REINTENTO: en la PC de Alfredo, OEE y 5S se descartaron sin reintento en una
            # ronda y con reintento en otra, según cómo estaba escrita la pregunta (08/11/2026).
            registro.info("Sin segundo intento: puntaje %.2f < %.2f", utiles[0].puntaje, reintento)
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
        # Los documentos se encontraron pero no traen la respuesta (p. ej. el temario nombra "los 8 desperdicios"
        # sin decir cuáles son): se dice qué se revisó, para que el alumno sepa dónde buscar (08/11/2026).
        revisados = "; ".join(f"{f.titulo}" + (f", pág. {f.pagina}" if f.pagina else "") for f in _fuentes(utiles)[:2])
        return terminar(Respuesta(SIN_EVIDENCIA, f"No encontré la respuesta en los materiales del CEE (lo más cercano "
                                  f"que revisé: {revisados}). " + config.mensaje_derivacion), llm.nombre)
    return terminar(Respuesta(RESPONDIDA, limpiar_respuesta(texto), _fuentes(utiles)), llm.nombre)
