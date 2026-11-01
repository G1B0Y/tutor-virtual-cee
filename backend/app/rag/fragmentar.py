"""Extracción de texto de PDFs y división en fragmentos que conservan su página."""

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class Fragmento:
    pagina: int
    orden: int
    texto: str


def extraer_paginas(ruta: Path) -> list[str]:
    """Texto de cada página. Un PDF escaneado (sin texto) devuelve páginas vacías."""
    lector = PdfReader(str(ruta))
    return [limpiar(p.extract_text() or "") for p in lector.pages]


def limpiar(texto: str) -> str:
    texto = texto.replace("­", "")  # guiones invisibles
    texto = re.sub(r"-\n(\w)", r"\1", texto)  # palabras cortadas al final de línea
    lineas = [re.sub(r"\s+", " ", linea).strip() for linea in texto.splitlines()]
    return "\n".join(linea for linea in lineas if linea)


def _oraciones(texto: str) -> list[str]:
    return [o.strip() for o in re.split(r"(?<=[.!?:])\s+|\n", texto) if o.strip()]


def fragmentar(paginas: list[str], max_caracteres: int = 900, solape: int = 1) -> list[Fragmento]:
    """Agrupa oraciones de una misma página hasta `max_caracteres`.

    Un fragmento nunca cruza páginas (así la fuente cita la página exacta).
    `solape` = cuántas oraciones del final de un fragmento se repiten al inicio del siguiente,
    para no cortar una idea a la mitad.
    """
    fragmentos: list[Fragmento] = []
    for numero, texto in enumerate(paginas, start=1):
        actual: list[str] = []
        for oracion in _oraciones(texto):
            if actual and len(" ".join(actual + [oracion])) > max_caracteres:
                fragmentos.append(Fragmento(numero, len(fragmentos), " ".join(actual)))
                actual = actual[-solape:] if solape else []
            actual.append(oracion)
        if actual:
            fragmentos.append(Fragmento(numero, len(fragmentos), " ".join(actual)))
    return fragmentos
