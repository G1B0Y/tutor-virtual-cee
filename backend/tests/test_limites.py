"""Límite de preguntas por minuto (RF-M06) y clave del CEE para las consultas pendientes (RF-M04)."""

from fastapi.testclient import TestClient

from app import main
from app.config import Configuracion, obtener_configuracion
from app.consulta import Respuesta
from app.limites import LimitePorMinuto, clave_del_alumno


class Reloj:
    def __init__(self):
        self.ahora = 1000.0

    def __call__(self):
        return self.ahora


def test_limite_por_minuto_con_ventana_deslizante():
    reloj = Reloj()
    limite = LimitePorMinuto(3, reloj=reloj)
    assert [limite.esperar("a") for _ in range(3)] == [0, 0, 0]
    reloj.ahora += 20
    assert limite.esperar("a") == 40  # el primero sale de la ventana a los 60 s
    assert limite.esperar("b") == 0  # otro alumno no se ve afectado
    reloj.ahora += 40
    assert limite.esperar("a") == 0


def test_limite_cero_es_sin_limite():
    limite = LimitePorMinuto(0)
    assert all(limite.esperar("a") == 0 for _ in range(100))


def test_las_claves_viejas_se_limpian():
    reloj = Reloj()
    limite = LimitePorMinuto(1, reloj=reloj)
    for n in range(1000):
        limite.esperar(f"ip{n}")
    reloj.ahora += 61
    limite.esperar("nueva")
    assert list(limite._pedidos) == ["nueva"]


def test_clave_del_alumno_solo_confia_en_el_proxy_si_se_configuro():
    assert clave_del_alumno("10.0.0.5", "1.2.3.4", confiar_en_proxy=False) == "10.0.0.5"
    assert clave_del_alumno("10.0.0.5", "1.2.3.4, 10.0.0.5", confiar_en_proxy=True) == "1.2.3.4"
    assert clave_del_alumno("10.0.0.5", None, confiar_en_proxy=True) == "10.0.0.5"


def _cliente(config: Configuracion, limite: LimitePorMinuto, monkeypatch) -> TestClient:
    monkeypatch.setattr(main, "responder", lambda *a, **k: Respuesta("faq", "Respuesta de prueba."))
    main.app.dependency_overrides = {
        obtener_configuracion: lambda: config,
        main.obtener_limite: lambda: limite,
        main.obtener_conexion: lambda: None,
        main.obtener_embeddings: lambda: None,
        main.obtener_llm: lambda: None,
    }
    return TestClient(main.app)


def test_consulta_responde_429_al_pasar_el_limite(monkeypatch):
    cliente = _cliente(Configuracion(), LimitePorMinuto(2), monkeypatch)
    try:
        estados = [cliente.post("/consulta", json={"pregunta": "¿Qué es el EOQ?"}).status_code for _ in range(3)]
        assert estados == [200, 200, 429]
        respuesta = cliente.post("/consulta", json={"pregunta": "¿Qué es el EOQ?"})
        assert respuesta.headers["retry-after"].isdigit()
        assert "Espera" in respuesta.json()["detail"]
    finally:
        main.app.dependency_overrides = {}


def test_consultas_pendientes_piden_la_clave_del_cee(monkeypatch):
    sin_clave = _cliente(Configuracion(clave_cee=""), LimitePorMinuto(0), monkeypatch)
    try:
        assert sin_clave.get("/consultas-pendientes", headers={"X-Clave-CEE": ""}).status_code == 503
        con_clave = _cliente(Configuracion(clave_cee="clave-larga-de-prueba"), LimitePorMinuto(0), monkeypatch)
        assert con_clave.get("/consultas-pendientes").status_code == 401
        assert con_clave.get("/consultas-pendientes", headers={"X-Clave-CEE": "otra"}).status_code == 401
        assert con_clave.post("/consultas-pendientes/1/atendida", json={}).status_code == 401
    finally:
        main.app.dependency_overrides = {}
