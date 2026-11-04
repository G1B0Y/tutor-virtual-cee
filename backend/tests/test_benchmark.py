"""Reglas puras del benchmark (app/benchmark.py)."""

import json
from pathlib import Path

from app.benchmark import cumple_claves, normalizar, percentil, umbral_que_separa

RAIZ = Path(__file__).resolve().parents[2]


def test_normalizar_quita_tildes_y_conserva_simbolos():
    assert normalizar("  Estadística   y MEDICIÓN ") == "estadistica y medicion"
    assert normalizar("EOQ = √(2 × D)") == "eoq = √(2 × d)"
    assert normalizar("σd") == "σd"


def test_cumple_claves_pide_una_alternativa_de_cada_grupo():
    claves = [["definir"], ["medir"], ["controlar"]]
    assert cumple_claves("DMAIC: Definir, Medir, Analizar, Mejorar y Controlar.", claves)
    assert not cumple_claves("Definir y medir.", claves)
    assert cumple_claves("Necesitas estadística básica y Excel.", [["estadistica"], ["excel"]])
    assert cumple_claves("Cpk ≥ 1.33", [["1,33", "1.33"]])
    # La alternativa debe empezar una palabra
    assert not cumple_claves("Se calcula con la evaluación", [["ac"]])
    assert not cumple_claves("Son 130 horas", [["30"]])
    assert cumple_claves("Promedios móviles", [["promedio"]])
    assert cumple_claves("CPI = EV / AC", [["valor ganado", "ev"], ["costo real", "ac"]])


def test_umbral_que_separa_toma_el_medio_del_hueco():
    umbral, dentro, fuera = umbral_que_separa([0.20, 0.30, 0.40], [0.60, 0.70])
    assert 0.40 <= umbral < 0.60
    assert 0.45 <= umbral <= 0.55
    assert (dentro, fuera) == (3, 0)


def test_umbral_que_separa_con_grupos_mezclados():
    # Una pregunta de fuera (0.35) queda entre las de dentro: el mejor puntaje deja pasar todas las de dentro.
    umbral, dentro, fuera = umbral_que_separa([0.20, 0.30, 0.40, 0.45], [0.35, 0.80])
    assert dentro == 4 and fuera == 1
    assert 0.45 <= umbral < 0.80


def test_percentil():
    assert percentil([], 95) == 0
    assert percentil([5, 1, 3], 50) == 3
    assert percentil(list(range(1, 21)), 95) == 19


def test_set_de_preguntas_esta_completo():
    preguntas = json.loads((RAIZ / "benchmark" / "preguntas.json").read_text(encoding="utf-8"))
    corpus = json.loads((RAIZ / "corpus" / "prueba" / "corpus.json").read_text(encoding="utf-8"))
    archivos = {d["archivo"] for d in corpus["documentos"]}
    assert len(preguntas["dentro"]) == 20 and len(preguntas["fuera"]) == 10
    ids = [p["id"] for p in preguntas["dentro"] + preguntas["fuera"]]
    assert len(ids) == len(set(ids))
    for p in preguntas["dentro"]:
        assert p["archivo"] in archivos, p["id"]
        assert p["pagina"] >= 1 and p["claves"] and all(p["claves"]), p["id"]
    # Cada documento del corpus tiene al menos una pregunta
    assert archivos == {p["archivo"] for p in preguntas["dentro"]}
