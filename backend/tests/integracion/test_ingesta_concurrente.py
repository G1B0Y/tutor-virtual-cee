"""Dos ingestas del mismo documento a la vez no deben crear dos documentos (pasó el 01/11/2026 en la PC de Alfredo).

No usa la transacción que se deshace del fixture `db`: necesita dos conexiones que confirmen de verdad.
Borra lo que crea al final.
"""

import threading
import uuid
from pathlib import Path

import psycopg
import pytest

from app.ingesta import cargar_documento
from app.rag.embeddings import EmbeddingsHash

from .conftest import URL

PDF = Path(__file__).resolve().parents[3] / "corpus" / "prueba" / "reglamento_academico_cee.pdf"


@pytest.fixture
def titulo():
    if not URL:
        pytest.skip("TEST_DATABASE_URL no está definida")
    titulo = f"Prueba concurrente {uuid.uuid4()}"
    yield titulo
    with psycopg.connect(URL) as conexion:
        conexion.execute("DELETE FROM documentos WHERE titulo = %s", (titulo,))


def test_dos_ingestas_a_la_vez_dejan_un_solo_documento(titulo):
    with psycopg.connect(URL) as primera, psycopg.connect(URL) as segunda:
        resultado = {}
        # La primera ingesta queda con su transacción abierta (y el candado tomado)...
        primera_tx = primera.transaction()
        primera_tx.__enter__()
        cargar_documento(primera, EmbeddingsHash(), PDF, titulo, "reglamento")

        # ...mientras la segunda intenta cargar el mismo documento en otro hilo.
        def segunda_ingesta():
            resultado["mensaje"] = cargar_documento(segunda, EmbeddingsHash(), PDF, titulo, "reglamento")

        hilo = threading.Thread(target=segunda_ingesta)
        hilo.start()
        hilo.join(timeout=1)
        assert hilo.is_alive(), "la segunda ingesta debería esperar el candado de la primera"

        primera_tx.__exit__(None, None, None)
        primera.commit()
        hilo.join(timeout=10)
        segunda.commit()

        assert "sin cambios" in resultado["mensaje"]
        cantidad = primera.execute("SELECT count(*) FROM documentos WHERE titulo = %s", (titulo,)).fetchone()[0]
        assert cantidad == 1
