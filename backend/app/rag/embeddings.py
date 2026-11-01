"""Cálculo de embeddings (vectores de significado) de forma local."""

import hashlib
import math
import re
import unicodedata
from functools import lru_cache
from typing import Protocol

DIMENSION = 384  # Debe coincidir con vector(384) en infra/db/002_base_conocimiento.sql


class Embeddings(Protocol):
    def codificar(self, textos: list[str], es_consulta: bool = False) -> list[list[float]]: ...


class EmbeddingsSentenceTransformers:
    """Modelo multilingüe local. Se descarga la primera vez y queda en caché (volumen de Docker)."""

    def __init__(self, nombre: str):
        from sentence_transformers import SentenceTransformer  # import pesado: solo si se usa

        self.nombre = nombre
        self.modelo = SentenceTransformer(nombre, device="cpu")
        # sentence-transformers renombró el método; se acepta el nombre nuevo y el anterior.
        obtener_dimension = getattr(self.modelo, "get_embedding_dimension", None) or self.modelo.get_sentence_embedding_dimension
        dimension = obtener_dimension()
        if dimension != DIMENSION:
            raise ValueError(f"El modelo {nombre} da vectores de {dimension}; la base espera {DIMENSION}")
        # Los modelos E5 necesitan prefijos distintos para preguntas y para pasajes.
        self.prefijos = ("query: ", "passage: ") if "e5" in nombre.lower() else ("", "")

    def codificar(self, textos: list[str], es_consulta: bool = False) -> list[list[float]]:
        prefijo = self.prefijos[0] if es_consulta else self.prefijos[1]
        vectores = self.modelo.encode([prefijo + t for t in textos], normalize_embeddings=True)
        return [v.tolist() for v in vectores]


def _palabras(texto: str) -> list[str]:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return [p for p in re.findall(r"[a-z0-9]+", sin_tildes) if len(p) > 2]


class EmbeddingsHash:
    """Solo para pruebas y CI (no necesita descargar modelos).

    Cuenta palabras en 384 casillas: encuentra textos que comparten palabras,
    pero no entiende sinónimos ni significado. Nunca usarlo con alumnos reales.
    """

    def codificar(self, textos: list[str], es_consulta: bool = False) -> list[list[float]]:
        resultado = []
        for texto in textos:
            vector = [0.0] * DIMENSION
            for palabra in _palabras(texto):
                h = int.from_bytes(hashlib.md5(palabra.encode()).digest()[:4], "little")
                vector[h % DIMENSION] += 1.0 if h & 1 << 31 else -1.0
            norma = math.sqrt(sum(v * v for v in vector)) or 1.0
            resultado.append([v / norma for v in vector])
        return resultado


@lru_cache
def crear_embeddings(proveedor: str, modelo: str) -> Embeddings:
    if proveedor == "hash":
        return EmbeddingsHash()
    if proveedor == "sentence-transformers":
        return EmbeddingsSentenceTransformers(modelo)
    raise ValueError(f"Proveedor de embeddings desconocido: {proveedor}")


def como_vector(valores: list[float]) -> str:
    """Formato de texto que entiende pgvector: '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{v:.6f}" for v in valores) + "]"
