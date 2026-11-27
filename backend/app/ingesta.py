"""Carga de documentos y FAQs a la base de conocimiento (RF-M05).

Uso (dentro del contenedor de la API, con el corpus montado en /corpus):
    docker compose exec api python -m app.ingesta corpus /corpus/prueba
    docker compose exec api python -m app.ingesta documento /corpus/x.pdf --titulo "..." --tipo temario [--curso "..."]
    docker compose exec api python -m app.ingesta faqs /corpus/prueba/faqs.csv
    docker compose exec api python -m app.ingesta retirar /corpus/complementario   # deja de buscar en esos documentos
    docker compose exec api python -m app.ingesta estado
    docker compose exec api python -m app.ingesta reindexar      # al cambiar de modelo de embeddings
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
        # Candado por título hasta el fin de la transacción: si dos ingestas corren a la vez,
        # la segunda espera y ve el documento de la primera en vez de crear otro (01/11/2026).
        conexion.execute("SELECT pg_advisory_xact_lock(hashtext('ingesta:' || %s))", (titulo,))
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


def retirar_corpus(conexion: psycopg.Connection, carpeta: Path) -> list[str]:
    """Retira (deja de buscar) los documentos que lista carpeta/corpus.json; no borra nada.

    Sirve para sacar el corpus complementario cuando llegue el material del CEE. Volver a cargar la carpeta
    con "corpus" crea una versión nueva y vigente."""
    manifiesto = json.loads((carpeta / "corpus.json").read_text(encoding="utf-8"))
    mensajes = []
    with conexion.transaction():
        for d in manifiesto["documentos"]:
            fila = conexion.execute(
                """UPDATE versiones_documento v SET estado = 'retirado', retirado_en = now()
                     FROM documentos d
                    WHERE d.id = v.documento_id AND d.titulo = %s AND v.estado = 'vigente'
                RETURNING v.version""",
                (d["titulo"],),
            ).fetchone()
            mensajes.append(f"{d['archivo']}: " + (f"versión {fila[0]} retirada." if fila else "no estaba vigente."))
        conexion.execute("INSERT INTO eventos (tipo, estado, ms_total) VALUES ('ingesta', 'retirar', 0)")
    return mensajes


def reindexar(conexion: psycopg.Connection, emb: Embeddings) -> str:
    """Recalcula los embeddings de todos los fragmentos y FAQs con el modelo actual.

    Hace falta al cambiar de modelo de embeddings: la ingesta normal se salta los PDF que no cambiaron,
    y los vectores viejos (de otro modelo) no se pueden comparar con las preguntas codificadas con el nuevo."""
    inicio = time.monotonic()
    with conexion.transaction():
        fragmentos = conexion.execute("SELECT id, texto FROM fragmentos ORDER BY id").fetchall()
        faqs = conexion.execute("SELECT id, pregunta FROM faqs ORDER BY id").fetchall()
        with conexion.cursor() as cursor:
            if fragmentos:
                vectores = emb.codificar([t for _, t in fragmentos])
                cursor.executemany("UPDATE fragmentos SET embedding = %s WHERE id = %s",
                                   [(como_vector(v), i) for (i, _), v in zip(fragmentos, vectores)])
            if faqs:
                vectores = emb.codificar([p for _, p in faqs], es_consulta=True)
                cursor.executemany("UPDATE faqs SET embedding = %s WHERE id = %s",
                                   [(como_vector(v), i) for (i, _), v in zip(faqs, vectores)])
        conexion.execute("INSERT INTO eventos (tipo, estado, ms_total) VALUES ('ingesta', 'reindexar', %s)",
                         (int((time.monotonic() - inicio) * 1000),))
    return (f"Reindexado con el modelo actual: {_cantidad(len(fragmentos), 'fragmento')} y "
            f"{_cantidad(len(faqs), 'FAQ')} ({time.monotonic() - inicio:.0f} s).")


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
    p_retirar = sub.add_parser("retirar", help="Retira los documentos que lista corpus.json de una carpeta")
    p_retirar.add_argument("carpeta", type=Path)
    sub.add_parser("estado", help="Muestra qué hay cargado")
    sub.add_parser("reindexar", help="Recalcula los embeddings con el modelo actual (al cambiar de modelo)")
    args = parser.parse_args(argumentos)

    config = obtener_configuracion()
    try:
        with psycopg.connect(config.database_url) as conexion:
            if args.accion == "estado":
                mensajes = estado(conexion)
            elif args.accion == "retirar":
                mensajes = retirar_corpus(conexion, args.carpeta)
            else:
                print("Preparando el modelo de embeddings (la primera vez se descarga)...", flush=True)
                emb = crear_embeddings(config.embeddings_proveedor, config.embeddings_modelo)
                if args.accion == "corpus":
                    mensajes = cargar_corpus(conexion, emb, args.carpeta)
                elif args.accion == "reindexar":
                    mensajes = [reindexar(conexion, emb)]
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
