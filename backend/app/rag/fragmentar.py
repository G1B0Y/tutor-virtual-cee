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
    return [limpiar(_texto_de(p)) for p in lector.pages]


def _texto_de(pagina) -> str:
    """Los PDF exportados de Google Docs salen con una palabra por línea en la extracción normal de pypdf
    (09/11/2026, módulos de Sistemas Integrados Empresariales): sin líneas no hay oraciones ni viñetas y los
    fragmentos se cortan en cualquier palabra. En ese caso se usa el modo "layout", que respeta las líneas."""
    texto = pagina.extract_text() or ""
    if palabra_por_linea(texto):
        texto = pagina.extract_text(extraction_mode="layout") or texto
    return texto


def palabra_por_linea(texto: str) -> bool:
    """Más del 80 % de las líneas con texto tienen una sola palabra (y hay al menos 20)."""
    lineas = [linea.split() for linea in texto.splitlines() if linea.strip()]
    return len(lineas) >= 20 and sum(len(l) == 1 for l in lineas) / len(lineas) > 0.8


def limpiar(texto: str) -> str:
    texto = texto.replace("\u00ad", "").replace("\u200b", "")  # guiones invisibles y espacios de ancho cero
    texto = re.sub(r"-\n(\w)", r"\1", texto)  # palabras cortadas al final de línea
    lineas = [re.sub(r"\s+", " ", linea).strip() for linea in texto.splitlines()]
    return "\n".join(linea for linea in lineas if linea)


_ABREVIATURA = re.compile(r"(?:^|[\s(])(?:ej|p|etc|art|n|núm|pág|págs|vs|aprox|sr|sra|dr|dra|ing)\.$", re.IGNORECASE)


_FIN = (".", "!", "?", ":", "»", '"', ")")


def _oraciones(texto: str, largo_maximo: int = 400) -> list[str]:
    """Parte en oraciones. Dos cuidados (módulo de Marketing del curso SIE, R03, 10/11/2026: "3. Clientes
    Preferidos…: Compran / poco (ej. / piden solo un cuarto de pollo…" quedaba en otro fragmento que el nombre de
    su categoría y los modelos la confundían):
    - un salto de línea en medio de una oración (la línea no termina en puntuación) no la corta, salvo que la
      oración ya pase de `largo_maximo` (tablas y listas sin puntos);
    - un punto de abreviatura ("ej.", "p. ej.", "etc.") seguido de minúscula o número tampoco."""
    oraciones: list[str] = []
    abierta = False  # la oración anterior quedó sin terminar (fin de línea o abreviatura)
    for linea in texto.split("\n"):
        for trozo in re.split(r"(?<=[.!?:])\s+", linea):
            trozo = trozo.strip()
            if not trozo:
                continue
            sigue = trozo[0].islower() or trozo[0].isdigit()
            if abierta and sigue and len(oraciones[-1]) + len(trozo) < largo_maximo:
                oraciones[-1] += " " + trozo
            else:
                oraciones.append(trozo)
            abierta = bool(_ABREVIATURA.search(oraciones[-1]))
        if oraciones and not oraciones[-1].endswith(_FIN):
            abierta = True
    return oraciones


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
