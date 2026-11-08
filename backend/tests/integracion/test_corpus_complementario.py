"""El corpus complementario se carga junto al de prueba y se puede retirar sin borrar nada."""

from pathlib import Path

from app.ingesta import cargar_corpus, estado, retirar_corpus
from app.rag.embeddings import EmbeddingsHash

CORPUS = Path(__file__).resolve().parents[3] / "corpus" / "prueba"


def test_el_corpus_complementario_se_carga_junto_al_de_prueba_y_se_puede_retirar(db):
    # 08/11/2026: material de los 3 cursos redactado con fuentes públicas; se retira cuando llegue el del CEE.
    complementario = CORPUS.parent / "complementario"
    cargar_corpus(db, EmbeddingsHash(), CORPUS)
    antes = int(estado(db)[0].split(": ")[1])
    mensajes = cargar_corpus(db, EmbeddingsHash(), complementario)
    assert len(mensajes) == 12 and all("cargada" in m for m in mensajes)
    assert estado(db)[0] == f"Documentos vigentes: {antes + 12}"
    assert db.execute("SELECT count(*) FROM fragmentos_vigentes WHERE curso = 'Lean Six Sigma Green Belt'").fetchone()[0] > 30

    retirados = retirar_corpus(db, complementario)
    assert all("retirada" in m for m in retirados)
    assert estado(db)[0] == f"Documentos vigentes: {antes}"
    assert retirar_corpus(db, complementario)[0].endswith("no estaba vigente.")

    # Volver a cargarlo crea una versión nueva y vigente (el mismo archivo no se rechaza).
    assert all("versión 2 cargada" in m for m in cargar_corpus(db, EmbeddingsHash(), complementario))
    assert estado(db)[0] == f"Documentos vigentes: {antes + 12}"
