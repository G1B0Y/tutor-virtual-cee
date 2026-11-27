"""Cambiar de modelo de embeddings: `reindexar` recalcula los vectores de fragmentos y FAQs."""

from pathlib import Path

from app.config import Configuracion
from app.consulta import FAQ, RESPONDIDA, Turno, responder
from app.ingesta import cargar_corpus, reindexar
from app.rag.embeddings import EmbeddingsHash

CORPUS = Path(__file__).resolve().parents[3] / "corpus" / "prueba"
CONFIG = Configuracion(embeddings_proveedor="hash", umbral_distancia=0.5, umbral_faq=0.2)


class OtroModelo(EmbeddingsHash):
    """Simula un modelo distinto: mismos vectores, pero con las casillas en otro orden."""

    def codificar(self, textos, es_consulta=False):
        return [v[1:] + v[:1] for v in super().codificar(textos, es_consulta)]


class LLMFalso:
    nombre = "falso"

    def generar(self, mensajes):
        return mensajes[-1]["content"].split("<documentos>")[1].split("</documentos>")[0].strip()


def _vectores(db, tabla):
    return db.execute(f"SELECT id, embedding::text FROM {tabla} ORDER BY id").fetchall()


def test_reindexar_cambia_todos_los_vectores_al_modelo_nuevo(db):
    cargar_corpus(db, EmbeddingsHash(), CORPUS)
    antes = {t: _vectores(db, t) for t in ("fragmentos", "faqs")}

    mensaje = reindexar(db, OtroModelo())

    n_frag, n_faq = len(antes["fragmentos"]), len(antes["faqs"])
    assert f"{n_frag} fragmentos y {n_faq} FAQs" in mensaje
    for tabla in ("fragmentos", "faqs"):
        despues = _vectores(db, tabla)
        assert [i for i, _ in despues] == [i for i, _ in antes[tabla]]  # mismas filas, nada duplicado
        assert all(a != d for (_, a), (_, d) in zip(antes[tabla], despues))
    assert db.execute("SELECT count(*) FROM eventos WHERE estado = 'reindexar'").fetchone()[0] == 1


def test_sin_reindexar_el_modelo_nuevo_no_encuentra_y_despues_si(db):
    """El defecto que evita: cambiar de modelo sin recalcular deja la base con vectores incomparables."""
    cargar_corpus(db, EmbeddingsHash(), CORPUS)
    pregunta = "¿Cuál es la nota mínima para aprobar?"

    sin_reindexar = responder(pregunta, db, OtroModelo(), LLMFalso(), Turno(3), CONFIG)
    assert sin_reindexar.estado not in (FAQ, RESPONDIDA)

    reindexar(db, OtroModelo())
    con_reindexar = responder(pregunta, db, OtroModelo(), LLMFalso(), Turno(3), CONFIG)
    assert con_reindexar.estado in (FAQ, RESPONDIDA)


def test_reindexar_una_base_vacia_no_falla(db):
    db.execute("DELETE FROM faqs")
    db.execute("DELETE FROM documentos")
    assert "0 fragmentos y 0 FAQs" in reindexar(db, EmbeddingsHash())
