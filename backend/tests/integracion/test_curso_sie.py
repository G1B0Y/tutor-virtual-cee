"""Curso Sistemas Integrados Empresariales (09/11/2026): sus 3 módulos se cargan junto a los otros corpus y las
preguntas de razonamiento llevan más fragmentos y la regla 14 al modelo."""

from pathlib import Path

from app.config import Configuracion
from app.consulta import RESPONDIDA, Turno, responder
from app.ingesta import cargar_corpus, estado
from app.rag.embeddings import EmbeddingsHash
from app.rag.prompt import RAZONAMIENTO

CORPUS = Path(__file__).resolve().parents[3] / "corpus"
CONFIG = Configuracion(embeddings_proveedor="hash", umbral_distancia=0.9, umbral_faq=0.0, margen_puntaje=2.0,
                       margen_razonamiento=2.0)


class LLMQueCopia:
    """Responde con la primera oración del primer documento que recibe."""
    nombre = "falso"

    def __init__(self):
        self.llamadas = []

    def generar(self, mensajes):
        self.llamadas.append(mensajes)
        documentos = mensajes[-1]["content"].split("<documentos>")[1].split("</documentos>")[0]
        return documentos.strip().split("\n", 1)[1].split(". ")[0] + "."


def test_los_3_modulos_se_cargan_junto_a_los_otros_corpus(db):
    emb = EmbeddingsHash()
    cargar_corpus(db, emb, CORPUS / "prueba")
    antes = int(estado(db)[0].split(": ")[1])
    mensajes = cargar_corpus(db, emb, CORPUS / "sie")
    assert len(mensajes) == 3 and all("versión 1 cargada" in m for m in mensajes)
    assert estado(db)[0] == f"Documentos vigentes: {antes + 3}"
    por_curso = db.execute("SELECT count(*) FROM fragmentos_vigentes WHERE curso = 'Sistemas Integrados Empresariales'"
                           ).fetchone()[0]
    assert 25 <= por_curso <= 50  # 12 páginas; con una palabra por línea (el error) salían otros cortes
    # Cargarlos otra vez no duplica nada.
    assert all("sin cambios" in m for m in cargar_corpus(db, emb, CORPUS / "sie"))


def test_una_pregunta_de_razonamiento_lleva_mas_fragmentos_y_la_regla_14(db):
    emb = EmbeddingsHash()
    cargar_corpus(db, emb, CORPUS / "sie")
    llm = LLMQueCopia()
    r = responder("Una pollería recibe la queja de un cliente porque su pedido llegó tarde, ¿qué área debe atenderlo?",
                  db, emb, llm, Turno(3), CONFIG)
    assert r.estado == RESPONDIDA
    sistema, usuario = llm.llamadas[0]
    assert sistema["content"].endswith(RAZONAMIENTO)
    # Hasta 6 (FRAGMENTOS_RAZONAMIENTO); uno menos si el fragmento siguiente se pegó al mejor (_con_continuacion).
    assert CONFIG.fragmentos_por_consulta < usuario["content"].count("Sistemas Integrados Empresariales –") \
        <= CONFIG.fragmentos_razonamiento

    llm = LLMQueCopia()
    responder("¿Qué es el CRM?", db, emb, llm, Turno(3), CONFIG)
    sistema, usuario = llm.llamadas[0]
    assert RAZONAMIENTO not in sistema["content"]
    assert usuario["content"].count("Sistemas Integrados Empresariales –") <= CONFIG.fragmentos_por_consulta
