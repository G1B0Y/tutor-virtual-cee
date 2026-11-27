"""Genera los PDF del corpus complementario desde los textos en Markdown de corpus/complementario/fuentes/.

Material de PRUEBA más completo que corpus/prueba: contenido académico redactado a partir de fuentes públicas
(ASCM, PMI, NIST, Lean Enterprise Institute, libros de texto), con su bibliografía al final de cada documento.
NO es material del CEE ni está validado por el CEE: cada página lo dice. Cuando el CEE entregue sus documentos,
este corpus se retira con: python -m app.ingesta retirar /corpus/complementario

Uso (desde la raíz del repo):  python scripts/generar_corpus_complementario.py
Necesita reportlab (solo para generar):  pip install reportlab
Formato de los .md: "# Título" (primera línea), "## Sección", "### Subsección", párrafos, "- viñeta",
"1. numerada", **negrita**. Cada archivo fuentes/X.md genera X.pdf; corpus.json lista título, curso y tipo.
"""

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer

CARPETA = Path(__file__).resolve().parent.parent / "corpus" / "complementario"
AVISO = "MATERIAL DE PRUEBA – elaborado con fuentes públicas; no es material oficial ni validado por el CEE."


def _en_linea(texto: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escape(texto))


def _bloques(lineas: list[str], estilos) -> list:
    """Cada sección "##" va junta en una página si cabe: el tutor cita por página y un fragmento nunca cruza páginas,
    así una lista (los 8 desperdicios, las 5S) no queda partida. Los números y viñetas van como texto ("3. …"),
    para que la extracción del PDF los conserve en la misma línea."""
    vineta = ParagraphStyle("vineta", parent=estilos["BodyText"], leftIndent=16, firstLineIndent=-10, spaceAfter=3)
    secciones: list[list] = [[]]
    for linea in lineas:
        linea = linea.strip()  # las viñetas con sangría se aplanan
        if not linea:
            continue
        if linea.startswith("## "):
            secciones.append([Paragraph(_en_linea(linea[3:]), estilos["Heading2"])])
        elif linea.startswith("### "):
            secciones[-1].append(Paragraph(_en_linea(linea[4:]), estilos["Heading3"]))
        elif linea.startswith("- "):
            secciones[-1].append(Paragraph("• " + _en_linea(linea[2:]), vineta))
        elif re.match(r"^\d+\. ", linea):
            secciones[-1].append(Paragraph(_en_linea(linea), vineta))
        else:
            secciones[-1].append(Paragraph(_en_linea(linea), estilos["BodyText"]))
    return [KeepTogether(s) for s in secciones if s]


def generar_pdf(origen: Path, destino: Path) -> str:
    lineas = origen.read_text(encoding="utf-8").splitlines()
    titulo = lineas[0].removeprefix("# ").strip()
    estilos = getSampleStyleSheet()
    estilos["BodyText"].spaceAfter = 5
    estilos["BodyText"].leading = 14
    aviso = ParagraphStyle("aviso", fontSize=8, textColor="#8a1c1c")

    def pie(lienzo, doc):
        lienzo.saveState()
        lienzo.setFont("Helvetica", 8)
        lienzo.setFillColorRGB(0.54, 0.11, 0.11)
        lienzo.drawString(2 * cm, 1.2 * cm, AVISO)
        lienzo.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Pág. {doc.page}")
        lienzo.restoreState()

    doc = SimpleDocTemplate(str(destino), pagesize=A4, title=titulo, author="Grupo 5 – material de prueba",
                            leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    contenido = [Paragraph(escape(titulo), estilos["Title"]), Paragraph(escape(AVISO), aviso), Spacer(1, 8)]
    contenido += _bloques(lineas[1:], estilos)
    doc.build(contenido, onFirstPage=pie, onLaterPages=pie)
    return titulo


def generar() -> None:
    manifiesto = json.loads((CARPETA / "corpus.json").read_text(encoding="utf-8"))
    for doc in manifiesto["documentos"]:
        origen = CARPETA / "fuentes" / doc["archivo"].replace(".pdf", ".md")
        titulo = generar_pdf(origen, CARPETA / doc["archivo"])
        print("Generado:", doc["archivo"], "–", titulo)


if __name__ == "__main__":
    generar()
