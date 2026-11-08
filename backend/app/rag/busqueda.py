"""Búsqueda por similitud en pgvector (solo material vigente)."""

from dataclasses import dataclass

import psycopg

from app.rag.embeddings import como_vector


@dataclass(frozen=True)
class FragmentoEncontrado:
    texto: str
    titulo: str
    pagina: int | None
    distancia: float


@dataclass(frozen=True)
class FaqEncontrada:
    pregunta: str
    respuesta: str
    fuente: str | None
    distancia: float


def buscar_fragmentos(conexion: psycopg.Connection, vector: list[float], limite: int,
                      titulo: str | None = None) -> list[FragmentoEncontrado]:
    """`titulo`: solo fragmentos de ese documento (seguimientos: "ese curso" es el de la pregunta anterior)."""
    filas = conexion.execute(
        """SELECT texto, titulo, pagina, embedding <=> %s::vector AS distancia
             FROM fragmentos_vigentes
            WHERE %s::text IS NULL OR titulo = %s
            ORDER BY distancia
            LIMIT %s""",
        (como_vector(vector), titulo, titulo, limite),
    ).fetchall()
    return [FragmentoEncontrado(t, ti, p, float(d)) for t, ti, p, d in filas]


def fragmentos_que_dicen(conexion: psycopg.Connection, vector: list[float], titulo: str, patron: str,
                         limite: int = 2) -> list[FragmentoEncontrado]:
    """Fragmentos de un documento cuyo texto calza con `patron` (regex de PostgreSQL, sin distinguir mayúsculas).
    Para "unidad 1": el fragmento que dice "Unidad 1" no siempre es el más cercano por significado."""
    filas = conexion.execute(
        """SELECT texto, titulo, pagina, embedding <=> %s::vector AS distancia
             FROM fragmentos_vigentes
            WHERE titulo = %s AND texto ~* %s
            ORDER BY distancia
            LIMIT %s""",
        (como_vector(vector), titulo, patron, limite),
    ).fetchall()
    return [FragmentoEncontrado(t, ti, p, float(d)) for t, ti, p, d in filas]


def buscar_faq(conexion: psycopg.Connection, vector: list[float]) -> FaqEncontrada | None:
    fila = conexion.execute(
        """SELECT pregunta, respuesta, fuente, embedding <=> %s::vector AS distancia
             FROM faqs WHERE activa
            ORDER BY distancia LIMIT 1""",
        (como_vector(vector),),
    ).fetchone()
    return FaqEncontrada(fila[0], fila[1], fila[2], float(fila[3])) if fila else None
