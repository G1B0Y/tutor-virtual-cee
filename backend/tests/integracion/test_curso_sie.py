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
    assert len(mensajes) == 18 and all("versión 1 cargada" in m for m in mensajes)
    assert estado(db)[0] == f"Documentos vigentes: {antes + 18}"
    por_curso = db.execute("SELECT count(*) FROM fragmentos_vigentes WHERE curso = 'Sistemas Integrados Empresariales'"
                           ).fetchone()[0]
    assert 110 <= por_curso <= 160  # 3 módulos originales (~35) + apuntes de los 14 módulos (~94)
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


def test_las_cuatro_funciones_del_crm_llegan_completas_al_modelo(db):
    """09/11/2026: las funciones A–D del CRM ocupan 5 fragmentos de dos páginas; granite veía A y B, inventaba dos y el
    control descartaba la lista. Ahora al mejor fragmento se le pegan los siguientes."""
    from app.consulta import _con_lista_pedida
    from app.rag.busqueda import buscar_fragmentos

    emb = EmbeddingsHash()
    cargar_corpus(db, emb, CORPUS / "sie")
    pregunta = "¿Cuáles son las cuatro funciones del CRM?"
    vector = emb.codificar([pregunta], es_consulta=True)[0]
    titulo = next(t for (t,) in db.execute("SELECT DISTINCT titulo FROM fragmentos_vigentes").fetchall()
                  if "CRM: gestión" in t)
    primero = next(f for f in buscar_fragmentos(db, vector, 50, titulo, pregunta, 2.0)
                   if "A continuación, se detallan" in f.texto)
    juntos = _con_lista_pedida(db, vector, pregunta, [primero], CONFIG.fragmentos_lista)
    texto = juntos[0].texto
    for funcion in ("A. Almacenamiento de Data", "B. Recepción y Registro de Reclamos", "C. Atención Post-Venta",
                    "D. Evaluación de la Satisfacción del Cliente"):
        assert funcion in texto
    assert len(texto) <= 4000
    # Sin una cantidad en la pregunta no se pega nada.
    assert _con_lista_pedida(db, vector, "¿Qué es el CRM?", [primero], CONFIG.fragmentos_lista) == [primero]


class LLMQueSeAbstieneUnaVez(LLMQueCopia):
    def generar(self, mensajes):
        self.llamadas.append(mensajes)
        if len(self.llamadas) == 1:
            return "SIN_EVIDENCIA"
        self.llamadas.pop()  # LLMQueCopia.generar la vuelve a anotar
        return super().generar(mensajes)


def test_con_razonamiento_el_segundo_intento_lleva_su_aviso(db):
    from app.rag.prompt import REINTENTO_RAZONAMIENTO

    emb = EmbeddingsHash()
    cargar_corpus(db, emb, CORPUS / "sie")
    llm = LLMQueSeAbstieneUnaVez()
    config = CONFIG.model_copy(update={"puntaje_reintento_razonamiento": 0.0})
    r = responder("¿Qué pasaría si una carpintería empieza a fabricar una silla sin tener la orden de pedido?",
                  db, emb, llm, Turno(3), config)
    assert len(llm.llamadas) == 2 and llm.llamadas[1][-1]["content"].endswith(REINTENTO_RAZONAMIENTO)
    assert r.estado == RESPONDIDA


def test_que_modulos_veremos_en_el_curso_lista_los_documentos_cargados(db):
    # Demo del 10/11/2026: "¿Qué módulos veremos en el curso de Sistemas integrados?" → "no encontré…, lo más
    # cercano: Temario – Gestión de la Cadena de Suministro". El curso no tiene temario: se listan sus documentos.
    emb = EmbeddingsHash()
    cargar_corpus(db, emb, CORPUS / "prueba")
    cargar_corpus(db, emb, CORPUS / "sie")
    llm = LLMQueCopia()
    r = responder("¿Qué módulos veremos en el curso de Sistemas integrados?", db, emb, llm, Turno(3), CONFIG)
    assert r.estado == RESPONDIDA and not llm.llamadas  # sin modelo
    assert "Sistemas Integrados Empresariales" in r.respuesta
    for modulo in ("Módulo de Marketing", "Módulo de Ventas", "Módulo de CRM", "Módulo de Producción",
                   "Módulo de Almacenes", "Módulo de Recursos Humanos", "Módulo de Finanzas"):
        assert r.respuesta.count(f"- {modulo}\n") == 1  # una vez, aunque el módulo tenga dos documentos
    assert r.respuesta.count("\n- ") == 15  # 14 módulos y la visión general
    assert len(r.fuentes) == 15 and "todavía no están cargados" in r.respuesta
    # Un curso con temario sigue el camino normal (lo responde su temario, con el modelo).
    from app.catalogo import materiales_del_curso
    assert materiales_del_curso(db, "¿Qué temas veremos en el curso de Lean Six Sigma Green Belt?") is None
    assert materiales_del_curso(db, "¿Cuáles son las 4 funciones del CRM?") is None
    assert materiales_del_curso(db, "¿Qué es el marketing en Sistemas Integrados Empresariales?") is None
