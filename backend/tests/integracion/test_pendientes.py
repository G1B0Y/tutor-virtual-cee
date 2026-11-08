"""Listado de consultas pendientes para el CEE (RF-M04), contra la base real."""

from fastapi.testclient import TestClient

from app import main, pendientes
from app.config import Configuracion, obtener_configuracion


def _nueva(db, pregunta: str) -> int:
    return db.execute(
        "INSERT INTO consultas_pendientes (pregunta, motivo) VALUES (%s, 'sin_evidencia') RETURNING id", (pregunta,)
    ).fetchone()[0]


def test_listar_y_marcar_atendida(db):
    primera, segunda = _nueva(db, "¿Cuáles son los 8 desperdicios?"), _nueva(db, "¿Quién dicta Lean?")
    ids = [c.id for c in pendientes.listar(db)]
    assert primera in ids and segunda in ids
    assert pendientes.marcar_atendida(db, primera, "Se agregó la separata de la Unidad 1")
    assert not pendientes.marcar_atendida(db, primera, "otra vez")  # ya estaba atendida
    assert primera not in [c.id for c in pendientes.listar(db)]
    atendida = next(c for c in pendientes.listar(db, incluir_atendidas=True) if c.id == primera)
    assert atendida.nota_atencion == "Se agregó la separata de la Unidad 1" and atendida.atendida_en


def test_endpoints_con_la_clave(db):
    id_consulta = _nueva(db, "¿Cuándo empieza PMBOK?")
    main.app.dependency_overrides = {
        obtener_configuracion: lambda: Configuracion(clave_cee="clave-larga-de-prueba"),
        main.obtener_conexion: lambda: db,
    }
    try:
        cliente = TestClient(main.app)
        clave = {"X-Clave-CEE": "clave-larga-de-prueba"}
        lista = cliente.get("/consultas-pendientes", headers=clave).json()
        assert {"id": id_consulta, "pregunta": "¿Cuándo empieza PMBOK?", "motivo": "sin_evidencia"}.items() <= next(
            c for c in lista if c["id"] == id_consulta).items()
        respuesta = cliente.post(f"/consultas-pendientes/{id_consulta}/atendida", headers=clave, json={"nota": "FAQ"})
        assert respuesta.json() == {"id": id_consulta, "atendida": True}
        assert cliente.post(f"/consultas-pendientes/{id_consulta}/atendida", headers=clave, json={}).status_code == 404
    finally:
        main.app.dependency_overrides = {}
