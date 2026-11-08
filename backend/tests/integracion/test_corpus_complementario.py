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


def test_la_busqueda_hibrida_distingue_cpi_de_cp_y_se_actualiza_al_retirar(db):
    """08/11/2026: con los 18 documentos, "¿Qué indica un CPI menor que 1?" traía el Cp de Lean y el modelo respondió
    mal. Las palabras raras de la pregunta (cpi) ahora pesan en el orden."""
    from app.rag.busqueda import buscar_fragmentos

    complementario = CORPUS.parent / "complementario"
    emb = EmbeddingsHash()
    cargar_corpus(db, emb, CORPUS)
    cargar_corpus(db, emb, complementario)
    pregunta = "¿Qué indica un CPI menor que 1?"
    vector = emb.codificar([pregunta], es_consulta=True)[0]
    top = buscar_fragmentos(db, vector, 4, texto=pregunta, umbral=2.0)
    # El temario de prueba de PMBOK también lo explica ("Un CPI menor que 1 indica que el proyecto gasta más…").
    assert "PMBOK" in top[0].titulo and "CPI" in top[0].texto
    assert any(f.titulo.startswith("Gestión de Proyectos con el PMBOK – Unidad 3") for f in top)
    assert [f.puntaje for f in top] == sorted((f.puntaje for f in top), reverse=True)

    retirar_corpus(db, complementario)  # el índice de palabras se rehace solo
    assert all("(material complementario)" not in f.titulo
               for f in buscar_fragmentos(db, vector, 4, texto=pregunta, umbral=2.0))
