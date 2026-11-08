"""El corpus complementario (material de prueba con fuentes públicas) está completo y bien marcado."""

import json
import re
from pathlib import Path

import pytest
from pypdf import PdfReader

RAIZ = Path(__file__).resolve().parents[2]
CARPETA = RAIZ / "corpus" / "complementario"
MANIFIESTO = json.loads((CARPETA / "corpus.json").read_text(encoding="utf-8"))
DOCUMENTOS = MANIFIESTO["documentos"]


def test_tiene_los_3_cursos_con_4_documentos_cada_uno():
    cursos = {}
    for d in DOCUMENTOS:
        cursos[d["curso"]] = cursos.get(d["curso"], 0) + 1
    assert cursos == {"Gestión de la Cadena de Suministro": 4, "Lean Six Sigma Green Belt": 4,
                      "Gestión de Proyectos con el PMBOK": 4}


def test_los_titulos_no_chocan_con_el_corpus_de_prueba():
    # La ingesta reconoce un documento por su título: si coincidiera, reemplazaría al del benchmark.
    prueba = {d["titulo"] for d in json.loads((RAIZ / "corpus" / "prueba" / "corpus.json").read_text("utf-8"))["documentos"]}
    titulos = [d["titulo"] for d in DOCUMENTOS]
    assert len(set(titulos)) == len(titulos)
    assert not prueba & set(titulos)
    assert all(t.endswith("(material complementario)") for t in titulos)


@pytest.mark.parametrize("doc", DOCUMENTOS, ids=lambda d: d["archivo"])
def test_cada_fuente_tiene_su_bibliografia_y_su_pdf(doc):
    fuente = CARPETA / "fuentes" / doc["archivo"].replace(".pdf", ".md")
    texto = fuente.read_text(encoding="utf-8")
    assert doc["titulo"].startswith(texto.splitlines()[0].removeprefix("# ").strip())
    bibliografia = texto.split("## Fuentes", 1)
    assert len(bibliografia) == 2 and len(re.findall(r"^- ", bibliografia[1], re.M)) >= 2
    assert (CARPETA / doc["archivo"]).is_file()


@pytest.mark.parametrize("doc", DOCUMENTOS, ids=lambda d: d["archivo"])
def test_cada_pagina_avisa_que_no_es_material_del_cee(doc):
    paginas = [p.extract_text() or "" for p in PdfReader(CARPETA / doc["archivo"]).pages]
    assert paginas
    for texto in paginas:
        assert "MATERIAL DE PRUEBA" in texto and "no es material oficial ni validado por el CEE" in texto


def test_las_listas_numeradas_quedan_en_una_linea_y_en_una_sola_pagina():
    # Antes el número salía en una línea aparte y los 8 desperdicios se partían entre dos páginas.
    paginas = [p.extract_text() for p in PdfReader(CARPETA / "lean_u1_pensamiento_lean.pdf").pages]
    con_lista = [t for t in paginas if "1. Defectos" in t]
    assert len(con_lista) == 1
    assert "8. Sobreprocesamiento" in con_lista[0]
