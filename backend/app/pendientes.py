"""Consultas que el tutor no pudo responder, para que el equipo del CEE las atienda (RF-M04).

Se guarda solo el texto de la pregunta, el motivo y la fecha (Ley 29733): nada que identifique al alumno.
"""

from dataclasses import dataclass
from datetime import datetime

import psycopg


@dataclass(frozen=True)
class ConsultaPendiente:
    id: int
    pregunta: str
    motivo: str
    creada_en: datetime
    atendida_en: datetime | None
    nota_atencion: str | None


def listar(conexion: psycopg.Connection, incluir_atendidas: bool = False, limite: int = 200) -> list[ConsultaPendiente]:
    filas = conexion.execute(
        """SELECT id, pregunta, motivo, creada_en, atendida_en, nota_atencion
             FROM consultas_pendientes
            WHERE %s OR atendida_en IS NULL
            ORDER BY creada_en DESC
            LIMIT %s""",
        (incluir_atendidas, limite),
    ).fetchall()
    return [ConsultaPendiente(*fila) for fila in filas]


def marcar_atendida(conexion: psycopg.Connection, id_consulta: int, nota: str | None) -> bool:
    """Devuelve False si la consulta no existe o ya estaba atendida."""
    fila = conexion.execute(
        """UPDATE consultas_pendientes SET atendida_en = now(), nota_atencion = %s
            WHERE id = %s AND atendida_en IS NULL RETURNING id""",
        (nota, id_consulta),
    ).fetchone()
    return fila is not None
