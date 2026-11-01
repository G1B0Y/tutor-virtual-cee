import psycopg
import pytest

DIM = 384


def vector(*inicio: float) -> str:
    """Vector de 384 dimensiones con los primeros valores dados y el resto en 0."""
    valores = list(inicio) + [0.0] * (DIM - len(inicio))
    return "[" + ",".join(str(v) for v in valores) + "]"


def crear_documento(db, titulo="Temario de prueba") -> int:
    return db.execute(
        "INSERT INTO documentos (titulo, curso, tipo) VALUES (%s, 'PRUEBA', 'temario') RETURNING id",
        (titulo,),
    ).fetchone()[0]


def registrar(db, documento_id: int, hash_: str) -> int:
    return db.execute(
        "SELECT registrar_version(%s, 'temario.pdf', %s, 3)", (documento_id, hash_ * 64)
    ).fetchone()[0]


def agregar_fragmento(db, version_id: int, orden: int, texto: str, emb: str) -> None:
    db.execute(
        "INSERT INTO fragmentos (version_id, orden, pagina, texto, embedding) VALUES (%s, %s, 1, %s, %s)",
        (version_id, orden, texto, emb),
    )


def test_la_primera_carga_queda_vigente(db):
    doc = crear_documento(db)
    v1 = registrar(db, doc, "a")
    fila = db.execute("SELECT version, estado FROM versiones_documento WHERE id = %s", (v1,)).fetchone()
    assert fila == (1, "vigente")


def test_una_version_nueva_retira_la_anterior_y_sus_fragmentos(db):
    doc = crear_documento(db)
    v1 = registrar(db, doc, "a")
    agregar_fragmento(db, v1, 0, "Texto viejo", vector(1.0))
    v2 = registrar(db, doc, "b")
    agregar_fragmento(db, v2, 0, "Texto nuevo", vector(1.0))

    estados = db.execute(
        "SELECT version, estado, retirado_en IS NOT NULL FROM versiones_documento WHERE documento_id = %s ORDER BY version",
        (doc,),
    ).fetchall()
    assert estados == [(1, "retirado", True), (2, "vigente", False)]

    textos = db.execute("SELECT texto FROM fragmentos_vigentes WHERE documento_id = %s", (doc,)).fetchall()
    assert textos == [("Texto nuevo",)]


def test_no_se_carga_dos_veces_el_mismo_archivo(db):
    doc = crear_documento(db)
    registrar(db, doc, "a")
    with pytest.raises(psycopg.errors.RaiseException, match="ya es la versión vigente"):
        registrar(db, doc, "a")


def test_no_puede_haber_dos_versiones_vigentes(db):
    doc = crear_documento(db)
    registrar(db, doc, "a")
    with pytest.raises(psycopg.errors.UniqueViolation):
        db.execute(
            "INSERT INTO versiones_documento (documento_id, version, archivo, hash_sha256) VALUES (%s, 9, 'x.pdf', %s)",
            (doc, "c" * 64),
        )


def test_la_busqueda_devuelve_el_fragmento_mas_parecido(db):
    doc = crear_documento(db)
    v1 = registrar(db, doc, "a")
    agregar_fragmento(db, v1, 0, "Inventario de seguridad", vector(1.0, 0.0))
    agregar_fragmento(db, v1, 1, "Método ABC", vector(0.0, 1.0))

    texto, distancia = db.execute(
        """SELECT texto, embedding <=> %s AS distancia
             FROM fragmentos_vigentes WHERE documento_id = %s
            ORDER BY distancia LIMIT 1""",
        (vector(0.1, 0.9), doc),
    ).fetchone()
    assert texto == "Método ABC"
    assert distancia < 0.1


def test_consulta_pendiente_limita_el_largo_de_la_pregunta(db):
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute(
            "INSERT INTO consultas_pendientes (pregunta, motivo) VALUES (%s, 'sin_evidencia')", ("x" * 1001,)
        )
