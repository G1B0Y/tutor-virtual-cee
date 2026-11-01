from fastapi.testclient import TestClient

from app import salud
from app.config import Configuracion, obtener_configuracion
from app.main import app

cliente = TestClient(app)


def test_salud_ok_cuando_todo_responde(monkeypatch):
    monkeypatch.setattr(salud, "revisar_base", lambda c: {"estado": "ok", "pgvector": "0.8.0"})
    monkeypatch.setattr(salud, "revisar_ollama", lambda c: {"estado": "ok", "modelos": []})
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ok"


def test_salud_degradado_si_ollama_cae(monkeypatch):
    monkeypatch.setattr(salud, "revisar_base", lambda c: {"estado": "ok", "pgvector": "0.8.0"})
    monkeypatch.setattr(salud, "revisar_ollama", lambda c: {"estado": "error", "detalle": "ConnectError"})
    cuerpo = cliente.get("/salud").json()
    assert cuerpo["estado"] == "degradado"
    assert cuerpo["servicios"]["ollama"]["estado"] == "error"


def test_salud_degradado_sin_servicios_reales():
    # Con la base y Ollama inalcanzables, la API sigue viva y lo informa (RNF-03 / RNF-04).
    sin_servicios = Configuracion(
        database_url="postgresql://x:x@127.0.0.1:1/x",
        ollama_url="http://127.0.0.1:1",
        timeout_salud=1,
    )
    app.dependency_overrides[obtener_configuracion] = lambda: sin_servicios
    try:
        cuerpo = cliente.get("/salud").json()
    finally:
        app.dependency_overrides.clear()
    assert cuerpo["estado"] == "degradado"
    assert cuerpo["servicios"]["base"]["estado"] == "error"
    assert cuerpo["servicios"]["ollama"]["estado"] == "error"
