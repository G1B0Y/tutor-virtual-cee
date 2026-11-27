"""El benchmark corre de punta a punta (embeddings "hash" y un modelo falso) y no deja cambios en la base."""

import json
from pathlib import Path

import psycopg
import pytest

from app.benchmark import ejecutar, guardar
from app.config import Configuracion
from tests.integracion.conftest import URL

RAIZ = Path(__file__).resolve().parents[3]


class LLMFalso:
    """Rechaza lo que habla de profesores o de fechas de inicio; si no, copia el primer documento."""

    nombre = "falso"

    def generar(self, mensajes):
        usuario = mensajes[-1]["content"]
        if "profesor" in usuario or "próxima edición" in usuario:
            return "SIN_EVIDENCIA"
        return usuario.split("<documentos>")[1].split("</documentos>")[0]


def _conteo(url):
    with psycopg.connect(url) as c:
        return c.execute("SELECT (SELECT count(*) FROM documentos), (SELECT count(*) FROM faqs),"
                         " (SELECT count(*) FROM eventos), (SELECT count(*) FROM consultas_pendientes)").fetchone()


def test_benchmark_de_punta_a_punta(tmp_path):
    if not URL:
        pytest.skip("TEST_DATABASE_URL no está definida")
    preguntas = json.loads((RAIZ / "benchmark" / "preguntas.json").read_text(encoding="utf-8"))
    antes = _conteo(URL)
    inf = ejecutar(URL, RAIZ / "corpus" / "prueba", preguntas, ["hash"], ["falso"], Configuracion(),
                   proveedor="hash", crear_llm=lambda nombre: LLMFalso(), aviso=lambda m: None)
    assert _conteo(URL) == antes  # todo se deshizo

    assert len(inf.embeddings) == 1 and len(inf.llms) == 1
    e, r = inf.embeddings[0], inf.llms[0]
    assert 0 <= e.recall1 <= e.recall5 <= e.recall5_documento <= 1
    assert e.recall5 > 0  # "hash" encuentra por palabras repetidas
    assert len(inf.filas) == 30 * 2  # búsqueda + respuestas
    assert r.rechazos == r.rechazos_busqueda + r.rechazos_modelo
    assert r.rechazos_modelo >= 1  # el modelo falso rechaza la del profesor si pasa el umbral, o la búsqueda
    assert "NO miden la calidad" in inf.avisos[0]

    md, csv_ = guardar(inf, tmp_path)
    texto = md.read_text(encoding="utf-8")
    assert "recall@5" in texto and "Aciertos con fuente" in texto
    assert len(csv_.read_text(encoding="utf-8-sig").splitlines()) == 61


def test_benchmark_del_curso_sie(tmp_path):
    # 09/11/2026: el set del curso Sistemas Integrados Empresariales corre sobre su propia carpeta (sin FAQs).
    if not URL:
        pytest.skip("TEST_DATABASE_URL no está definida")
    preguntas = json.loads((RAIZ / "benchmark" / "preguntas_sie.json").read_text(encoding="utf-8"))
    antes = _conteo(URL)
    inf = ejecutar(URL, RAIZ / "corpus" / "sie", preguntas, ["hash"], ["falso"], Configuracion(),
                   proveedor="hash", crear_llm=lambda nombre: LLMFalso(), aviso=lambda m: None)
    assert _conteo(URL) == antes
    total = len(preguntas["dentro"]) + len(preguntas["fuera"])
    assert len(inf.filas) == total * 2
    assert inf.embeddings[0].recall5 > 0
