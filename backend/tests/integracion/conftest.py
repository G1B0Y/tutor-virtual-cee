"""Pruebas contra una base real (PostgreSQL + pgvector con los SQL de infra/db aplicados).

Se ejecutan solo si TEST_DATABASE_URL está definida, por ejemplo con el docker compose levantado:
    TEST_DATABASE_URL=postgresql://tutor:<contraseña>@localhost:5432/tutor pytest
Cada prueba corre dentro de una transacción que se deshace al final: no deja datos.
"""

import os

import psycopg
import pytest

URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture
def db():
    if not URL:
        pytest.skip("TEST_DATABASE_URL no está definida")
    with psycopg.connect(URL) as conexion:
        with conexion.transaction(force_rollback=True):
            yield conexion
