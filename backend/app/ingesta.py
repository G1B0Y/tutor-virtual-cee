"""Carga de documentos y FAQs a la base de conocimiento (RF-M05).

Uso (dentro del contenedor de la API, con el corpus montado en /corpus):
    docker compose exec api python -m app.ingesta corpus /corpus/prueba
    docker compose exec api python -m app.ingesta documento /corpus/x.pdf --titulo "..." --tipo temario [--curso "..."]
    docker compose exec api python -m app.ingesta faqs /corpus/prueba/faqs.csv
    docker compose exec api python -m app.ingesta estado
"""

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import psycopg

from app.config import obtener_configuracion
from app.rag.embeddings import Embeddings, como_vector, crear_embeddings
from app.rag.fragmentar import extraer_paginas, fragmentar


class ErrorDeIngesta(Exception):
    pass


def cargar_documento(conexion: psycopg.Connection, emb: Embeddings, ruta: Path, titulo: str,
                     tipo: str, curso: str | None = None) -> str:
    """Carga un PDF como versión vigente de su documento. Devuelve un mensaje para la persona."""
    inicio = time.monotonic()
    datos = ruta.read_bytes()
    hash_ = hashlib.sha256(datos).hexdigest()

    paginas = extraer_paginas(ruta)
    fragmentos = fragmentar(paginas)
    if not fragmentos:
        raise ErrorDeIngesta(f"{ruta.name}: no tiene texto que se pueda leer (¿es un PDF escaneado?). No se cargó.")

    with conexion.transaction():
        fila = conexion.execute("SELECT id FROM documentos WHERE titulo = %s", (titulo,)).fetchone()
        if fila:
            documento_id = fila[0]
            conexion.execute("UPDATE documentos SET curso = %s, tipo = %s WHERE id = %s", (curso, tipo, documento_id))
            ya_vigente = conexion.execute(
                "SELECT 1 FROM versiones_documento WHERE documento_id = %s AND estado = 'vigente' AND hash_sha256 = %s",
                (documento_id, hash_),
            ).fetchone()
            if ya_vigente:
                return f"{ruta.name}: sin cambios (ya es la versión vigente)."
        else:
            documento_id = conexion.execute(
                "INSERT INTO documentos (titulo, curso, tipo) VALUES (%s, %s, %s) RETURNING id", (titulo, curso, tipo)
            ).fetchone()[0]

        version_id = conexion.execute(
            "SELECT registrar_version(%s, %s, %s, %s)", (documento_id, ruta.name, hash_, len(paginas))
        ).fetchone()[0]
        vectores = emb.codificar([f.texto for f in fragmentos])
        with conexion.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO fragmentos (version_id, orden, pagina, texto, embedding) VALUES (%s, %s, %s, %s, %s)",
                [(version_id, f.orden, f.pagina, f.texto, como_vector(v)) for f, v in zip(fragmentos, vectores)],
            )
        version = conexion.execute("SELECT version FROM versiones_documento WHERE id = %s", (version_id,)).fetchone()[0]
        conexion.execute(
            "INSERT INTO eventos (tipo, estado, ms_total) VALUES ('ingesta', 'ok', %s)",
            (int((time.monotonic() - inicio) * 1000),),
        )
    return f"{ruta.name}: versión {version} cargada ({_cantidad(len(paginas), 'página')}, {_cantidad(len(fragmentos), 'fragmento')})."


def _cantidad(n: int, palabra: str) -> str:
    return f"{n} {palabra}" + ("" if n == 1 else "s")


def cargar_faqs(conexion: psycopg.Connection, emb: Embeddings, ruta: Path) -> str:
    """Reemplaza las FAQs activas por las del CSV (columnas: pregunta, respuesta, fuente)."""
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        filas = [f for f in csv.DictReader(archivo) if (f.get("pregunta") or "").strip()]
    faltan = [n for n, f in enumerate(filas, start=2) if not (f.get("respuesta") or "").strip()]
    if faltan:
        raise ErrorDeIngesta(f"{ruta.name}: filas sin respuesta: {faltan}. No se cargó nada.")
    vectores = emb.codificar([f["pregunta"] for f in filas], es_consulta=True)
    with conexion.transaction():
        conexion.execute("UPDATE faqs SET activa = false WHERE activa")
        with conexion.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO faqs (pregunta, respuesta, fuente, embedding) VALUES (%s, %s, %s, %s)",
                [(f["pregunta"].strip(), f["respuesta"].strip(), (f.get("fuente") or "").strip() or None, como_vector(v))
                 for f, v in zip(filas, vectores)],
            )
    return f"{ruta.name}: {len(filas)} FAQs activas."


def cargar_corpus(conexion: psycopg.Connection, emb: Embeddings, carpeta: Path) -> list[str]:
    """Carga todo lo que lista carpeta/corpus.json."""
    manifiesto = json.loads((carpeta / "corpus.json").read_text(encoding="utf-8"))
    mensajes = [
        cargar_documento(conexion, emb, carpeta / d["archivo"], d["titulo"], d["tipo"], d.get("curso"))
        for d in manifiesto["documentos"]
    ]
    if manifiesto.get("faqs"):
        mensajes.append(cargar_faqs(conexion, emb, carpeta / manifiesto["faqs"]))
    return mensajes


def estado(conexion: psycopg.Connection) -> list[str]:
    filas = conexion.execute(
        """SELECT d.titulo, v.version, v.paginas, count(f.id)
             FROM documentos d
             JOIN versiones_documento v ON v.documento_id = d.id AND v.estado = 'vigente'
             LEFT JOIN fragmentos f ON f.version_id = v.id
            GROUP BY d.titulo, v.version, v.paginas ORDER BY d.titulo"""
    ).fetchall()
    faqs = conexion.execute("SELECT count(*) FROM faqs WHERE activa").fetchone()[0]
    lineas = [f"- {t} (versión {v}, {_cantidad(p, 'página')}, {_cantidad(n, 'fragmento')})" for t, v, p, n in filas]
    return [f"Documentos vigentes: {len(filas)}", *lineas, f"FAQs activas: {faqs}"]


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.ingesta", description="Carga la base de conocimiento.")
    sub = parser.add_subparsers(dest="accion", required=True)
    p_corpus = sub.add_parser("corpus", help="Carga todo lo que lista corpus.json de una carpeta")
    p_corpus.add_argument("carpeta", type=Path)
    p_doc = sub.add_parser("documento", help="Carga o reemplaza un PDF")
    p_doc.add_argument("pdf", type=Path)
    p_doc.add_argument("--titulo", required=True)
    p_doc.add_argument("--tipo", required=True,
                       choices=["temario", "separata", "presentacion", "manual", "reglamento", "otro"])
    p_doc.add_argument("--curso")
    p_faqs = sub.add_parser("faqs", help="Reemplaza las FAQs por las de un CSV")
    p_faqs.add_argument("csv", type=Path)
    sub.add_parser("estado", help="Muestra qué hay cargado")
    args = parser.parse_args(argumentos)

    config = obtener_configuracion()
    try:
        with psycopg.connect(config.database_url) as conexion:
            if args.accion == "estado":
                mensajes = estado(conexion)
            else:
                print("Preparando el modelo de embeddings (la primera vez se descarga)...", flush=True)
                emb = crear_embeddings(config.embeddings_proveedor, config.embeddings_modelo)
                if args.accion == "corpus":
                    mensajes = cargar_corpus(conexion, emb, args.carpeta)
                elif args.accion == "documento":
                    mensajes = [cargar_documento(conexion, emb, args.pdf, args.titulo, args.tipo, args.curso)]
                else:
                    mensajes = [cargar_faqs(conexion, emb, args.csv)]
    except (ErrorDeIngesta, FileNotFoundError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print("\n".join(mensajes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
