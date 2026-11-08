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
    # Los que no tienen la sigla quedan después de los que sí (el Cp de Lean ya no sale primero).
    con_cpi = ["CPI" in f.texto for f in top]
    assert con_cpi == sorted(con_cpi, reverse=True)

    retirar_corpus(db, complementario)  # el índice de palabras se rehace solo
    assert all("(material complementario)" not in f.titulo
               for f in buscar_fragmentos(db, vector, 4, texto=pregunta, umbral=2.0))


class LLMQueDudaUnaVez:
    """Se abstiene la primera vez y responde copiando los documentos la segunda (como granite con el OEE)."""
    nombre = "falso"

    def __init__(self):
        self.llamadas = []

    def generar(self, mensajes):
        self.llamadas.append(mensajes)
        if len(self.llamadas) == 1:
            return "SIN_EVIDENCIA"
        return mensajes[-1]["content"].split("<documentos>")[1].split("</documentos>")[0].strip()


def _con_los_dos_corpus(db):
    emb = EmbeddingsHash()
    cargar_corpus(db, emb, CORPUS)
    cargar_corpus(db, emb, CORPUS.parent / "complementario")
    return emb


def test_con_evidencia_fuerte_se_pide_una_segunda_vez(db):
    from app.config import Configuracion
    from app.consulta import RESPONDIDA, SIN_EVIDENCIA, Turno, responder
    from app.rag.prompt import REINTENTO

    emb = _con_los_dos_corpus(db)
    # Con los embeddings "hash" de las pruebas el mejor puntaje del OEE es ~1,3 (con e5 en la PC de Alfredo, 1,96).
    config = Configuracion(embeddings_proveedor="hash", umbral_distancia=0.9, umbral_faq=0.0, puntaje_reintento=1.2)
    llm = LLMQueDudaUnaVez()
    r = responder("¿Cómo se calcula el OEE?", db, emb, llm, Turno(3), config)
    assert r.estado == RESPONDIDA and len(llm.llamadas) == 2
    assert REINTENTO in llm.llamadas[1][-1]["content"]

    # Sin evidencia fuerte no se insiste: la abstención queda.
    llm = LLMQueDudaUnaVez()
    r = responder("¿Cómo se calcula el OEE?", db, emb, llm, Turno(3),
                  config.model_copy(update={"puntaje_reintento": 2.5}))
    assert r.estado == SIN_EVIDENCIA and len(llm.llamadas) == 1


def test_si_el_mejor_fragmento_termina_en_el_tema_va_tambien_el_siguiente(db):
    """"Principios del PMBOK 8.ª edición": el fragmento terminaba en "Octava edición (noviembre de 2025):" y la lista
    de principios estaba en el siguiente (08/11/2026)."""
    from app.consulta import _con_continuacion
    from app.rag.busqueda import buscar_fragmentos

    emb = _con_los_dos_corpus(db)
    pregunta = "¿Cuáles son los principios del PMBOK 8.ª edición?"
    vector = emb.codificar([pregunta], es_consulta=True)[0]
    titulo = next(t for (t,) in db.execute("SELECT DISTINCT titulo FROM fragmentos_vigentes").fetchall()
                  if t.startswith("Gestión de Proyectos con el PMBOK – Unidad 1"))
    termina_en_octava = next(f for f in buscar_fragmentos(db, vector, 50, titulo, pregunta, 2.0)
                             if f.texto.rstrip().endswith("Octava edición (noviembre de 2025):"))
    juntos = _con_continuacion(db, vector, pregunta, [termina_en_octava])
    # Un solo texto: la lista de la octava edición queda justo después de "Octava edición (noviembre de 2025):".
    assert len(juntos) == 1 and juntos[0].pagina == termina_en_octava.pagina
    texto = juntos[0].texto
    assert texto.startswith(termina_en_octava.texto)
    assert "Adoptar una visión holística" in texto
    assert texto.count("Octava edición (noviembre de 2025):") == 1  # sin la oración repetida del solape
