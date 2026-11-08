"""Recorrido completo con la base real: ingesta del corpus de prueba → búsqueda → respuesta.

Usa embeddings "hash" (sin descargar modelos) y un LLM falso: prueban la tubería, no la calidad.
La calidad real se mide en el benchmark (Fase 2) con el modelo de embeddings y Ollama.
"""

import json
from pathlib import Path

import pytest

from app.config import Configuracion
from app.consulta import FAQ, OCUPADO, RESPONDIDA, SIN_EVIDENCIA, SIN_LLM, Turno, responder
from app.ingesta import ErrorDeIngesta, cargar_corpus, cargar_documento, estado
from app.rag.embeddings import EmbeddingsHash
from app.rag.llm import ErrorLLM

CORPUS = Path(__file__).resolve().parents[3] / "corpus" / "prueba"
CONFIG = Configuracion(embeddings_proveedor="hash", umbral_distancia=0.9, umbral_faq=0.2)


class LLMFalso:
    nombre = "falso"

    def __init__(self, texto="Respuesta redactada.", falla=False):
        self.texto, self.falla, self.recibido = texto, falla, None

    def generar(self, mensajes):
        self.recibido = mensajes
        if self.falla:
            raise ErrorLLM("Ollama apagado")
        return self.texto


@pytest.fixture
def con_corpus(db):
    cargar_corpus(db, EmbeddingsHash(), CORPUS)
    return db


def _documentos_del_corpus() -> int:
    return len(json.loads((CORPUS / "corpus.json").read_text(encoding="utf-8"))["documentos"])


def test_el_corpus_de_prueba_se_carga_completo(con_corpus):
    resumen = estado(con_corpus)
    assert _documentos_del_corpus() == 6
    assert resumen[0] == f"Documentos vigentes: {_documentos_del_corpus()}"
    assert resumen[-1] == "FAQs activas: 5"


def test_volver_a_cargar_el_mismo_corpus_no_duplica(con_corpus):
    mensajes = cargar_corpus(con_corpus, EmbeddingsHash(), CORPUS)
    assert all("sin cambios" in m for m in mensajes[:-1])
    assert estado(con_corpus)[0] == f"Documentos vigentes: {_documentos_del_corpus()}"


def test_pdf_sin_texto_se_rechaza(db, tmp_path):
    from pypdf import PdfWriter

    vacio = tmp_path / "escaneado.pdf"
    escritor = PdfWriter()
    escritor.add_blank_page(width=200, height=200)
    escritor.write(vacio)
    with pytest.raises(ErrorDeIngesta, match="no tiene texto"):
        cargar_documento(db, EmbeddingsHash(), vacio, "Escaneado", "otro")


def test_pregunta_con_evidencia_pasa_por_el_llm_y_cita_fuentes(con_corpus):
    llm = LLMFalso()
    r = responder("¿Cómo se calcula el inventario de seguridad?", con_corpus, EmbeddingsHash(), llm, Turno(3), CONFIG)
    assert r.estado == RESPONDIDA
    assert r.respuesta == "Respuesta redactada."
    assert any("Gestión de Inventarios" in f.titulo for f in r.fuentes)
    assert "inventario de seguridad" in llm.recibido[1]["content"].lower()


def test_faq_responde_sin_llm(con_corpus):
    llm = LLMFalso()
    r = responder("¿Cuál es la nota mínima para aprobar?", con_corpus, EmbeddingsHash(), llm, Turno(3), CONFIG)
    assert r.estado == FAQ
    assert "14" in r.respuesta
    assert llm.recibido is None


def test_sin_evidencia_se_abstiene_y_registra_la_consulta(con_corpus):
    estricta = CONFIG.model_copy(update={"umbral_distancia": 0.01})
    r = responder("¿Quién ganó el mundial de fútbol?", con_corpus, EmbeddingsHash(), LLMFalso(), Turno(3), estricta)
    assert r.estado == SIN_EVIDENCIA
    assert r.fuentes == []
    pendiente = con_corpus.execute(
        "SELECT motivo FROM consultas_pendientes WHERE pregunta = '¿Quién ganó el mundial de fútbol?'"
    ).fetchone()
    assert pendiente == ("sin_evidencia",)


def test_si_el_modelo_dice_sin_evidencia_no_se_inventa(con_corpus):
    r = responder("¿Cuánto cuesta el programa?", con_corpus, EmbeddingsHash(), LLMFalso("SIN_EVIDENCIA"), Turno(3), CONFIG)
    assert r.estado == SIN_EVIDENCIA


def test_ollama_caido_muestra_el_fragmento_mas_relevante(con_corpus):
    r = responder("¿Qué es el método ABC de inventarios?", con_corpus, EmbeddingsHash(), LLMFalso(falla=True),
                  Turno(3), CONFIG)
    assert r.estado == SIN_LLM
    assert "«" in r.respuesta and len(r.fuentes) == 1


def test_cola_llena_responde_ocupado(con_corpus):
    turno = Turno(cola_maxima=0)
    assert turno.tomar()  # otra consulta está generando
    r = responder("¿Qué es el método ABC de inventarios?", con_corpus, EmbeddingsHash(), LLMFalso(), turno, CONFIG)
    turno.liberar()
    assert r.estado == OCUPADO


def test_cada_consulta_deja_un_evento_sin_la_pregunta(con_corpus):
    responder("¿Cuál es la nota mínima para aprobar?", con_corpus, EmbeddingsHash(), LLMFalso(), Turno(3), CONFIG)
    fila = con_corpus.execute("SELECT tipo, estado FROM eventos WHERE tipo = 'consulta' ORDER BY id DESC").fetchone()
    assert fila == ("consulta", "faq")


def test_saludo_responde_sin_buscar_ni_dejar_pendiente(con_corpus):
    """"¿en qué me puedes ayudar?" se abstenía y quedaba como consulta pendiente para el CEE (07/11/2026)."""
    from app.consulta import ORIENTACION

    class EmbeddingsQueNoSeUsan(EmbeddingsHash):
        def codificar(self, textos, es_consulta=False):
            raise AssertionError("no debía buscar")

    pendientes = con_corpus.execute("SELECT count(*) FROM consultas_pendientes").fetchone()[0]
    llm = LLMFalso()
    r = responder("en que me puedes ayudar?", con_corpus, EmbeddingsQueNoSeUsan(), llm, Turno(3), CONFIG)
    assert r.estado == ORIENTACION
    assert "temarios" in r.respuesta and r.fuentes == []
    assert llm.recibido is None
    assert con_corpus.execute("SELECT count(*) FROM consultas_pendientes").fetchone()[0] == pendientes
    assert con_corpus.execute(
        "SELECT estado FROM eventos WHERE tipo = 'consulta' ORDER BY id DESC LIMIT 1").fetchone()[0] == ORIENTACION


SEGUIMIENTO = "ESTOY LLEVANDO ESE CURSO, DAME UN RESUMEN DEL TEMA UNO"
ANTERIOR = "¿Qué temas tiene el curso de Gestión de Proyectos con el PMBOK?"


def test_seguimiento_usa_la_pregunta_anterior_para_entender_ese_curso(con_corpus):
    """Alfredo preguntó por el temario de PMBOK y luego "ese curso … tema uno": se abstenía (08/11/2026)."""
    config = CONFIG.model_copy(update={"umbral_distancia": 0.65})
    sola = responder(SEGUIMIENTO, con_corpus, EmbeddingsHash(), LLMFalso(), Turno(3), config)
    assert sola.estado == SIN_EVIDENCIA

    llm = LLMFalso()
    r = responder(SEGUIMIENTO, con_corpus, EmbeddingsHash(), llm, Turno(3), config, anterior=ANTERIOR)
    assert r.estado == RESPONDIDA
    assert r.fuentes and all("PMBOK" in f.titulo for f in r.fuentes)  # solo el curso de la pregunta anterior
    usuario = llm.recibido[-1]["content"]
    assert f"<pregunta_anterior>\n{ANTERIOR}\n</pregunta_anterior>" in usuario
    assert f"<pregunta_del_alumno>\n{SEGUIMIENTO}\n</pregunta_del_alumno>" in usuario


def test_la_pregunta_anterior_no_se_usa_si_la_actual_se_entiende_sola(con_corpus):
    llm = LLMFalso()
    r = responder("¿Cómo se calcula el inventario de seguridad?", con_corpus, EmbeddingsHash(), llm, Turno(3), CONFIG,
                  anterior=ANTERIOR)
    assert r.estado == RESPONDIDA
    assert "<pregunta_anterior>" not in llm.recibido[-1]["content"]


def test_la_pregunta_anterior_no_se_guarda_en_pendientes(con_corpus):
    estricta = CONFIG.model_copy(update={"umbral_distancia": 0.01})
    responder("¿Y el tema dos?", con_corpus, EmbeddingsHash(), LLMFalso(), Turno(3), estricta,
              anterior="dato personal de prueba 12345")
    guardadas = [p for (p,) in con_corpus.execute("SELECT pregunta FROM consultas_pendientes").fetchall()]
    assert "¿Y el tema dos?" in guardadas
    assert not any("12345" in p for p in guardadas)


PMBOK = "Temario – Gestión de Proyectos con el PMBOK (PRUEBA)"


def test_seguimiento_se_detecta_aunque_la_pregunta_sola_encuentre_algo(con_corpus):
    """Con "tema uno" → "unidad 1" la pregunta sola pasaba el umbral y mezclaba 4 documentos (08/11/2026)."""
    llm = LLMFalso()
    r = responder(SEGUIMIENTO, con_corpus, EmbeddingsHash(), llm, Turno(3), CONFIG, anterior=ANTERIOR)
    assert r.estado == RESPONDIDA
    assert {f.titulo for f in r.fuentes} == {PMBOK}
    assert "Unidad 1" in llm.recibido[-1]["content"]


def test_seguimiento_encadenado_usa_el_documento_de_la_respuesta_anterior(con_corpus):
    """"¿y el tema dos?" después de "ese curso…": la pregunta anterior tampoco nombra el curso."""
    llm = LLMFalso()
    r = responder("¿y el tema dos?", con_corpus, EmbeddingsHash(), llm, Turno(3), CONFIG,
                  anterior=SEGUIMIENTO, documento_anterior=PMBOK)
    assert r.estado == RESPONDIDA
    assert {f.titulo for f in r.fuentes} == {PMBOK}
    assert "Unidad 2" in llm.recibido[-1]["content"]


def test_documento_anterior_que_no_existe_no_rompe_la_busqueda(con_corpus):
    r = responder("¿Cómo se calcula el inventario de seguridad?", con_corpus, EmbeddingsHash(), LLMFalso(), Turno(3),
                  CONFIG, documento_anterior="Reglamento Académico (FAQ)")
    assert r.estado == RESPONDIDA
