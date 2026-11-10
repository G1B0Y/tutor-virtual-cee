"""Genera los PDF de apuntes del curso Sistemas Integrados Empresariales desde corpus/sie/fuentes/*.md.

Los textos salen del recopilado de apuntes del curso que entregó el equipo (10/11/2026, 31 páginas, todos los
módulos), ordenados módulo por módulo. Solo contienen lo que dicen esos apuntes: se corrigieron erratas, se
ordenaron las listas y se agregaron oraciones resumen ("Los tres tipos de mantenimiento son: …") para que el
tutor encuentre y cite mejor. No se agregó contenido de otras fuentes.

Uso (desde la raíz del repo):  python scripts/generar_apuntes_sie.py     (necesita reportlab)
Rehacer un PDF cambia su hash: la ingesta lo carga como versión nueva.
"""
from pathlib import Path

import generar_corpus_complementario as base

CARPETA = Path(__file__).resolve().parent.parent / "corpus" / "sie"
AVISO = "Apuntes de clase del curso Sistemas Integrados Empresariales – recopilados por el Grupo 5."


def generar() -> None:
    base.AVISO = AVISO
    for origen in sorted((CARPETA / "fuentes").glob("apuntes_*.md")):
        destino = CARPETA / f"sie_{origen.stem}.pdf"
        print("Generado:", destino.name, "–", base.generar_pdf(origen, destino))


if __name__ == "__main__":
    generar()
