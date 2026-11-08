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


def buscar_faq(conexion: psycopg.Connection, vector: list[float]) -> FaqEncontrada | None:
    fila = conexion.execute(
        """SELECT pregunta, respuesta, fuente, embedding <=> %s::vector AS distancia
             FROM faqs WHERE activa
            ORDER BY distancia LIMIT 1""",
        (como_vector(vector),),
    ).fetchone()
    return FaqEncontrada(fila[0], fila[1], fila[2], float(fila[3])) if fila else None
