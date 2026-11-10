"""Preguntas por los materiales de un curso ("¿qué módulos veremos en Sistemas Integrados?").

Ningún documento trae esa lista cuando el curso no tiene temario cargado, y la búsqueda devolvía el temario de otro
curso (demo del 10/11/2026). Se responde con los títulos de los documentos vigentes de ese curso, sin modelo: es
lo que el CEE cargó, no una lista del plan de estudios (el curso puede tener más módulos). Si el curso tiene
temario, no se toca: la pregunta sigue el camino normal y la responde el temario.
"""
import re

import psycopg

from app.conversacion import _normalizar

_PIDE_LISTA = re.compile(
    r"\b(que|cuales|cuantos|cuantas|lista\w*|dime|muestra\w*|enumera\w*)\b.*"
    r"\b(modulos?|materiales?|documentos?|separatas?|temas|contenidos?|unidades)\b")
_SIN_PESO = {"curso", "cursos", "gestion", "para", "con", "los", "las", "del"}


def _palabras(texto: str) -> set[str]:
    return {p for p in _normalizar(texto).split() if len(p) >= 4 and p not in _SIN_PESO}


def _curso_nombrado(pregunta: str, cursos: list[str]) -> str | None:
    """El curso cuyas palabras propias aparecen en la pregunta (al menos 2, o todas si tiene menos)."""
    dichas = _palabras(pregunta)
    mejor, aciertos = None, 0
    for curso in cursos:
        propias = _palabras(curso)
        comunes = len(propias & dichas)
        if comunes >= min(2, len(propias)) and comunes > aciertos:
            mejor, aciertos = curso, comunes
    return mejor


def materiales_del_curso(conexion: psycopg.Connection, pregunta: str) -> tuple[str, list[str]] | None:
    """(texto de la respuesta, títulos) si la pregunta pide los materiales de un curso sin temario; si no, None."""
    if not _PIDE_LISTA.search(_normalizar(pregunta)):
        return None
    filas = conexion.execute(
        "SELECT DISTINCT documento_id, titulo, curso, tipo FROM fragmentos_vigentes WHERE curso IS NOT NULL "
        "ORDER BY documento_id").fetchall()
    curso = _curso_nombrado(pregunta, sorted({f[2] for f in filas}))
    if curso is None:
        return None
    del_curso = [f for f in filas if f[2] == curso]
    if any(f[3] == "temario" for f in del_curso):
        return None
    # Un módulo puede tener más de un documento ("Módulo de Marketing: el proceso…" y "…: apuntes de clase"):
    # se nombra una vez, por lo que va antes de ":" o "(".
    nombres: dict[str, str] = {}
    for fila in del_curso:
        corto = re.sub(rf"^{re.escape(curso)}\s*[–—:-]\s*", "", fila[1])
        nombres.setdefault(re.split(r"[:(]", corto)[0].strip(), fila[1])
    lista = "\n".join(f"- {nombre}" for nombre in nombres)
    texto = (f"Del curso {curso} tengo cargados estos materiales:\n{lista}\n"
             "El curso puede tener más contenidos que todavía no están cargados. "
             "Puedes preguntarme por cualquiera de estos.")
    return texto, list(nombres.values())
