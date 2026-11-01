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


def test_consulta_rechaza_preguntas_vacias_o_muy_largas():
    from app.main import obtener_conexion, obtener_embeddings

    app.dependency_overrides[obtener_conexion] = lambda: None
    app.dependency_overrides[obtener_embeddings] = lambda: None
    try:
        assert cliente.post("/consulta", json={"pregunta": ""}).status_code == 422
        assert cliente.post("/consulta", json={"pregunta": "x" * 501}).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_ollama_sin_el_modelo_descargado_cuenta_como_falla(monkeypatch):
    class RespuestaFalsa:
        def raise_for_status(self):
            pass

        def json(self):
            return {"models": [{"name": "otro:1b"}]}

    monkeypatch.setattr(salud.httpx, "get", lambda *a, **k: RespuestaFalsa())
    resultado = salud.revisar_ollama(Configuracion(llm_modelo="qwen2.5:1.5b"))
    assert resultado["estado"] == "error"
    assert "qwen2.5:1.5b" in resultado["detalle"]
