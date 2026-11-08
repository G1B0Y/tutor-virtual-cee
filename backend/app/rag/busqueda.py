"""Búsqueda en el material vigente: por significado (pgvector) y por las palabras de la pregunta (híbrida).

Con 18 documentos (08/11/2026, corpus complementario) la búsqueda por significado sola confundía siglas parecidas
("¿Qué indica un CPI menor que 1?" traía el Cp de capacidad de procesos y el modelo respondió mal) y dejaba el
fragmento correcto fuera de los 4 primeros ("project charter", "PERT"). Por eso cada fragmento recibe un puntaje que
suma las dos cosas:
- `v`: qué tan cerca está por significado, de 1 (el más cercano) a 0 (en el umbral).
- `L`: qué parte de las palabras de la pregunta tiene, pesadas por lo raras que son en el material (IDF): "cpi",
  "charter" u "oee" pesan mucho; "proceso" o "calidad", poco. Va de 0 a 1.
El umbral de distancia sigue siendo el mismo: un fragmento lejano por significado no entra aunque tenga las palabras
(así las preguntas de fuera siguen sin encontrar nada).
"""

import math
import re
import threading
import unicodedata
from dataclasses import dataclass

import psycopg

from app.rag.embeddings import como_vector


@dataclass(frozen=True)
class FragmentoEncontrado:
    texto: str
    titulo: str
    pagina: int | None
    distancia: float
    puntaje: float = 0.0
    orden: int | None = None  # posición en su documento (para traer el fragmento que sigue)


@dataclass(frozen=True)
class FaqEncontrada:
    pregunta: str
    respuesta: str
    fuente: str | None
    distancia: float


# Palabras que no ayudan a encontrar el fragmento (artículos, preposiciones, verbos de pregunta).
_VACIAS = set("""
    que qué cual cuales cuál cuáles como cómo cuando cuándo donde dónde quien quién quienes cuanto cuanta cuantos
    cuantas por para con sin sobre entre desde hasta los las del una uno unos unas este esta estos estas ese esa eso
    esos esas aquel son ser fue está estan están hay tiene tienen hace hacen puede pueden debe deben más mas menos
    muy pero porque también tambien según segun cada todo toda todos todas otro otra otros otras mismo misma
    explica explícame explicame dime dame decir significa significan define definir definición definicion
    calcula calcular calculo cálculo sirve sirven usa usan utiliza consiste llama llaman cuál curso cursos tema
    temas unidad módulo modulo hola gracias favor quiero saber podrías podrias puedes
""".split())


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))


def terminos(texto: str) -> list[str]:
    """Raíces (6 letras) de las palabras que sirven para buscar, sin tildes ni repetidas. Se quedan las siglas de 3
    letras o más ("cpi", "oee", "eoq") y las de 2 con un número ("5s"); "cp" no, así "CPI" no se confunde con "Cp"."""
    vistos: list[str] = []
    for palabra in re.findall(r"[a-zñ0-9]+", _sin_tildes(texto)):
        corta_con_numero = len(palabra) == 2 and re.fullmatch(r"\d[a-zñ]|[a-zñ]\d", palabra)  # "5s", "6m"
        if (len(palabra) < 3 and not corta_con_numero) or palabra.isdigit() or palabra in _VACIAS_SIN_TILDES:
            continue
        raiz = palabra[:6]
        if raiz not in vistos:
            vistos.append(raiz)
    return vistos


_VACIAS_SIN_TILDES = {_sin_tildes(p) for p in _VACIAS}


_EN_MAYUSCULAS = re.compile(r"\b(?=[A-ZÑ0-9]*[A-ZÑ])[A-ZÑ0-9]{2,6}\b")


class IndiceLexico:
    """Raíces de cada fragmento vigente (con las del título de su documento: "los principios del PMBOK" también
    está en el fragmento que sigue y ya no dice "PMBOK") y en cuántos fragmentos aparece cada raíz (para el IDF).

    `siglas`: palabras que el material escribe en MAYÚSCULAS (CPI, OEE, 5S, DMAIC) y que no están en casi todos
    los fragmentos (como "CEE" o "PRUEBA" del aviso de cada página)."""

    def __init__(self, filas: list[tuple[int, str, str]]):
        self.titulos = {i: titulo for i, titulo, _ in filas}
        self.raices = {i: set(terminos(texto)) | set(terminos(titulo)) for i, titulo, texto in filas}
        self.frecuencia: dict[str, int] = {}
        for raices in self.raices.values():
            for r in raices:
                self.frecuencia[r] = self.frecuencia.get(r, 0) + 1
        mayusculas = {r for _, titulo, texto in filas for m in _EN_MAYUSCULAS.findall(f"{titulo} {texto}")
                      for r in terminos(m)}
        self.siglas = {r for r in mayusculas if self.frecuencia.get(r, 0) <= max(1, 0.3 * len(filas))}

    def siglas_de(self, consulta: list[str]) -> set[str]:
        return {r for r in consulta if r in self.siglas}

    def idf(self, raiz: str) -> float:
        n = len(self.raices)
        return math.log((n + 1) / (self.frecuencia.get(raiz, 0) + 0.5))

    def puntajes(self, consulta: list[str], titulo: str | None = None) -> dict[int, float]:
        """L de cada fragmento que tiene alguna palabra de la consulta (0 a 1)."""
        pesos = {r: self.idf(r) for r in consulta}
        total = sum(pesos.values())
        if not total:
            return {}
        resultado = {}
        for i, raices in self.raices.items():
            if titulo is not None and self.titulos[i] != titulo:
                continue
            suma = sum(p for r, p in pesos.items() if r in raices)
            if suma:
                resultado[i] = suma / total
        return resultado


# Lo que baja el puntaje de un fragmento que no tiene la sigla que nombra la pregunta (el puntaje va de 0 a 2):
# con MARGEN_PUNTAJE 0.4 queda fuera de las fuentes si otro fragmento sí la tiene.
PENALIZACION_SIN_SIGLA = 1.0

_indice: tuple[tuple, IndiceLexico] | None = None
_candado_indice = threading.Lock()


def indice_lexico(conexion: psycopg.Connection) -> IndiceLexico:
    """Se arma una vez y se rehace solo si cambió el material vigente (carga, reemplazo o retiro)."""
    global _indice
    firma = conexion.execute(
        "SELECT count(*), coalesce(max(id), 0), coalesce(sum(id), 0) FROM fragmentos_vigentes").fetchone()
    with _candado_indice:
        if _indice is None or _indice[0] != tuple(firma):
            filas = conexion.execute("SELECT id, titulo, texto FROM fragmentos_vigentes").fetchall()
            _indice = (tuple(firma), IndiceLexico(filas))
        return _indice[1]


def buscar_fragmentos(conexion: psycopg.Connection, vector: list[float], limite: int,
                      titulo: str | None = None, texto: str | None = None, umbral: float | None = None,
                      peso_lexico: float = 1.0, candidatos: int = 20) -> list[FragmentoEncontrado]:
    """`titulo`: solo fragmentos de ese documento (seguimientos: "ese curso" es el de la pregunta anterior).
    Con `texto` (la pregunta) y `umbral`, búsqueda híbrida: ordena por v + peso_lexico × L (ver arriba) los
    `candidatos` más cercanos por significado y los que más palabras de la pregunta tienen. Sin `texto`, solo por
    distancia (como antes)."""
    if texto is None or umbral is None:
        return _por_distancia(conexion, vector, limite, titulo)
    cercanos = conexion.execute(
        """SELECT id, texto, titulo, pagina, orden, embedding <=> %s::vector AS distancia
             FROM fragmentos_vigentes
            WHERE %s::text IS NULL OR titulo = %s
            ORDER BY distancia
            LIMIT %s""",
        (como_vector(vector), titulo, titulo, candidatos),
    ).fetchall()
    indice = indice_lexico(conexion)
    consulta = terminos(texto)
    lexicos = indice.puntajes(consulta, titulo)
    siglas = indice.siglas_de(consulta)
    mejores = sorted(lexicos, key=lexicos.get, reverse=True)[:candidatos]
    faltan = [i for i in mejores if i not in {f[0] for f in cercanos}]
    if faltan:
        cercanos += conexion.execute(
            """SELECT id, texto, titulo, pagina, orden, embedding <=> %s::vector AS distancia
                 FROM fragmentos_vigentes WHERE id = ANY(%s)""",
            (como_vector(vector), faltan),
        ).fetchall()
    dentro = [float(f[5]) for f in cercanos if float(f[5]) <= umbral]
    mas_cerca = min(dentro) if dentro else umbral
    escala = umbral - mas_cerca

    def puntaje(distancia: float, i: int) -> float:
        v = (umbral - distancia) / escala if escala > 0 else (1.0 if distancia <= umbral else 0.0)
        return v + peso_lexico * lexicos.get(i, 0.0)

    encontrados = [FragmentoEncontrado(t, ti, p, float(d), puntaje(float(d), i), o) for i, t, ti, p, o, d in cercanos]
    # Si la pregunta nombra una sigla del material (CPI, OEE, 5S) y hay fragmentos que la tienen, los que no la
    # tienen bajan: con "¿Qué indica un CPI menor que 1?" el Cp de Lean quedaba primero por "indica" y "menor".
    con_sigla = {i for i, *_ in cercanos if siglas & indice.raices.get(i, set())}
    if con_sigla and any(float(d) <= umbral for i, *_, d in cercanos if i in con_sigla):
        encontrados = [f if i in con_sigla else FragmentoEncontrado(f.texto, f.titulo, f.pagina, f.distancia,
                                                                    f.puntaje - PENALIZACION_SIN_SIGLA, f.orden)
                       for f, (i, *_) in zip(encontrados, cercanos)]
    # Primero los que pasan el umbral; entre ellos, por puntaje.
    encontrados.sort(key=lambda f: (f.distancia <= umbral, f.puntaje), reverse=True)
    return encontrados[:limite]


def siguiente_fragmento(conexion: psycopg.Connection, vector: list[float],
                        f: FragmentoEncontrado) -> FragmentoEncontrado | None:
    """El fragmento que sigue a `f` en su documento (misma página o la siguiente)."""
    if f.orden is None:
        return None
    fila = conexion.execute(
        """SELECT texto, titulo, pagina, embedding <=> %s::vector AS distancia, orden
             FROM fragmentos_vigentes
            WHERE titulo = %s AND orden = %s AND pagina BETWEEN %s AND %s + 1""",
        (como_vector(vector), f.titulo, f.orden + 1, f.pagina or 0, f.pagina or 0),
    ).fetchone()
    return FragmentoEncontrado(fila[0], fila[1], fila[2], float(fila[3]), 0.0, fila[4]) if fila else None


def _por_distancia(conexion: psycopg.Connection, vector: list[float], limite: int,
                   titulo: str | None) -> list[FragmentoEncontrado]:
    filas = conexion.execute(
        """SELECT texto, titulo, pagina, embedding <=> %s::vector AS distancia
             FROM fragmentos_vigentes
            WHERE %s::text IS NULL OR titulo = %s
            ORDER BY distancia
            LIMIT %s""",
        (como_vector(vector), titulo, titulo, limite),
    ).fetchall()
    return [FragmentoEncontrado(t, ti, p, float(d)) for t, ti, p, d in filas]


def fragmentos_que_dicen(conexion: psycopg.Connection, vector: list[float], titulo: str | None, patron: str,
                         limite: int = 2, mayusculas: bool = False) -> list[FragmentoEncontrado]:
    """Fragmentos (de un documento, o de todos si `titulo` es None) cuyo texto calza con `patron` (regex de
    PostgreSQL; sin distinguir mayúsculas salvo `mayusculas=True`, para siglas). Para "unidad 1": el fragmento que
    dice "Unidad 1" no siempre es el más cercano por significado."""
    operador = "~" if mayusculas else "~*"
    filas = conexion.execute(
        f"""SELECT texto, titulo, pagina, embedding <=> %s::vector AS distancia
             FROM fragmentos_vigentes
            WHERE (%s::text IS NULL OR titulo = %s) AND texto {operador} %s
            ORDER BY distancia
            LIMIT %s""",
        (como_vector(vector), titulo, titulo, patron, limite),
    ).fetchall()
    return [FragmentoEncontrado(t, ti, p, float(d)) for t, ti, p, d in filas]


def buscar_faq(conexion: psycopg.Connection, vector: list[float]) -> FaqEncontrada | None:
    fila = conexion.execute(
        """SELECT pregunta, respuesta, fuente, embedding <=> %s::vector AS distancia
             FROM faqs WHERE activa
            ORDER BY distancia LIMIT 1""",
        (como_vector(vector),),
    ).fetchone()
    return FaqEncontrada(fila[0], fila[1], fila[2], float(fila[3])) if fila else None
