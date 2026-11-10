"""LLMOllama contra un Ollama falso (servidor HTTP local que responde en streaming como /api/chat).

Error del 07/11/2026: qwen2.5:1.5b entró en bucle y escribió 35 000 tokens en 23 min porque nada cortaba
la respuesta. Ahora se pide num_predict y hay un plazo total."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.rag.llm import ErrorLLM, LLMOllama

MENSAJES = [{"role": "user", "content": "hola"}]


class OllamaFalso(BaseHTTPRequestHandler):
    modo = "normal"
    pedido: dict = {}

    def log_message(self, *args):
        pass

    def _linea(self, datos: dict) -> None:
        self.wfile.write((json.dumps(datos) + "\n").encode())
        self.wfile.flush()

    def do_POST(self):
        largo = int(self.headers.get("Content-Length", 0))
        OllamaFalso.pedido = json.loads(self.rfile.read(largo))
        if self.modo == "sin_modelo":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        try:
            if self.modo == "bucle":  # nunca termina: un fragmento cada 20 ms
                while True:
                    self._linea({"message": {"content": "bla "}, "done": False})
                    time.sleep(0.02)
            palabras = ["La nota ", "mínima ", "es 14."]
            if self.modo == "tope_largo":  # respuesta buena pero larga, cortada a media oración
                palabras = ["Debe atenderlo el CRM, no el vendedor. ", "Según el módulo de CRM, el cliente se comunica ",
                            "con un área que conoce el producto. Por lo tanto, en este caso el"]
            if self.modo == "tope_bucle":
                palabras = ["El CRM registra el reclamo del cliente. "] * 10
            for palabra in palabras:
                self._linea({"message": {"content": palabra}, "done": False})
            motivo = "length" if self.modo.startswith("tope") else "stop"
            self._linea({"message": {"content": ""}, "done": True, "done_reason": motivo, "eval_count": 3})
        except (BrokenPipeError, ConnectionResetError):
            pass  # el cliente cortó


@pytest.fixture
def ollama():
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), OllamaFalso)
    servidor.daemon_threads = True
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}"
    servidor.shutdown()
    servidor.server_close()


def test_respuesta_normal_pide_tope_de_tokens_y_mide_tiempos(ollama):
    OllamaFalso.modo = "normal"
    llm = LLMOllama(ollama, "qwen2.5:1.5b", timeout=10, max_tokens=300)
    assert llm.generar(MENSAJES) == "La nota mínima es 14."
    assert OllamaFalso.pedido["options"]["num_predict"] == 300
    assert OllamaFalso.pedido["stream"] is True
    assert llm.ultima["tokens"] == 3 and llm.ultima["ttft_ms"] <= llm.ultima["ms_llm"]


def test_respuesta_que_llega_al_tope_sin_oracion_util_se_descarta(ollama):
    OllamaFalso.modo = "tope"  # "La nota mínima es 14." es muy corta para quedarse sola
    with pytest.raises(ErrorLLM, match="tope"):
        LLMOllama(ollama, "qwen2.5:1.5b", timeout=10).generar(MENSAJES)


def test_un_bucle_que_llega_al_tope_se_descarta(ollama):
    OllamaFalso.modo = "tope_bucle"
    with pytest.raises(ErrorLLM, match="bucle"):
        LLMOllama(ollama, "granite3.3:2b", timeout=10).generar(MENSAJES)


def test_una_respuesta_larga_que_llega_al_tope_se_corta_en_la_ultima_oracion(ollama):
    # Benchmark del curso SIE (09/11/2026): R08 y R09 llegaban al tope razonando y el alumno veía sin_llm.
    OllamaFalso.modo = "tope_largo"
    texto = LLMOllama(ollama, "granite3.3:2b", timeout=10).generar(MENSAJES)
    assert texto == ("Debe atenderlo el CRM, no el vendedor. Según el módulo de CRM, el cliente se comunica con un área "
                     "que conoce el producto.")


def test_a_qwen3_se_le_pide_no_pensar_y_a_los_demas_no_se_les_manda_nada(ollama):
    OllamaFalso.modo = "normal"
    LLMOllama(ollama, "qwen3:4b", timeout=10).generar(MENSAJES)
    assert OllamaFalso.pedido["think"] is False
    LLMOllama(ollama, "granite3.3:2b", timeout=10).generar(MENSAJES)
    assert "think" not in OllamaFalso.pedido


def test_respuesta_en_bucle_se_corta_por_el_plazo_total(ollama):
    OllamaFalso.modo = "bucle"
    inicio = time.monotonic()
    with pytest.raises(ErrorLLM, match="se cortó"):
        LLMOllama(ollama, "qwen2.5:1.5b", timeout=0.5).generar(MENSAJES)
    assert time.monotonic() - inicio < 3  # antes no cortaba nunca


def test_modelo_no_descargado(ollama):
    OllamaFalso.modo = "sin_modelo"
    with pytest.raises(ErrorLLM, match="no está descargado"):
        LLMOllama(ollama, "granite3.3:2b", timeout=5).generar(MENSAJES)
