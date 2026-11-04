"""Benchmark de la Fase 2: compara modelos de embeddings y de lenguaje con el set de 30 preguntas.

Uso (dentro del contenedor de la API, con el corpus y el benchmark montados):
    docker compose exec api python -m app.benchmark
    docker compose exec api python -m app.benchmark --solo-busqueda          # rápido: sin modelo de lenguaje
    docker compose exec api python -m app.benchmark --llm qwen2.5:1.5b --embeddings sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

Qué hace con cada modelo de embeddings:
  1. Dentro de una transacción que se deshace al final, vacía la base de conocimiento y carga el corpus
     con ese modelo (la base real no cambia: la API sigue respondiendo con lo de siempre).
  2. Búsqueda: recall@1 y recall@5 (¿el fragmento con la respuesta está entre los primeros?) y las distancias
     de las preguntas de dentro y de fuera, para proponer el umbral que mejor las separa.
  3. Con cada modelo de lenguaje: responde las 30 preguntas como lo haría el chat y mide aciertos con fuente,
     rechazos correctos, tiempo al primer token, tiempo total y RAM.
El informe queda en benchmark/resultados/ (Markdown para leer y CSV con el detalle de cada pregunta).
"""

import argparse
import csv
import gc
import json
import math
import os
import re
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import httpx
import psycopg

from app.config import Configuracion, obtener_configuracion
from app.consulta import FAQ, RESPONDIDA, SIN_EVIDENCIA, Turno, responder
from app.ingesta import cargar_corpus
from app.rag.busqueda import buscar_faq, buscar_fragmentos
from app.rag.embeddings import Embeddings, _crear
from app.rag.llm import ErrorLLM, LLMOllama

LIMA = timezone(timedelta(hours=-5))  # Perú no tiene horario de verano

EMBEDDINGS_POR_DEFECTO = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "intfloat/multilingual-e5-small",
]
LLM_POR_DEFECTO = ["qwen2.5:1.5b", "granite3.3:2b"]

# Licencia declarada por cada modelo. Se vuelve a verificar en la ficha oficial antes de elegirlo (RNF-23).
LICENCIAS = {
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": "Apache 2.0",
    "intfloat/multilingual-e5-small": "MIT",
    "qwen2.5:1.5b": "Apache 2.0",
    "granite3.3:2b": "Apache 2.0",
    "hash": "— (solo pruebas)",
}

META_RECALL5 = 0.80  # "Listo cuando" de la Fase 2 en docs/ROADMAP.md


# ---------------------------------------------------------------- reglas puras (con pruebas unitarias)

def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y con espacios simples. Conserva símbolos como √, σ y ×."""
    descompuesto = unicodedata.normalize("NFKD", texto.lower())
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_tildes.split())


def cumple_claves(respuesta: str, claves: list[list[str]]) -> bool:
    """La respuesta tiene al menos una alternativa de cada grupo. Cada alternativa debe empezar una palabra
    ("ac" no cuenta dentro de "evaluación", "30" no cuenta dentro de "130"), pero puede seguir ("promedio" → "promedios")."""
    texto = normalizar(respuesta)
    return all(any(re.search(r"(?<!\w)" + re.escape(normalizar(a)), texto) for a in grupo) for grupo in claves)


def umbral_que_separa(dentro: list[float], fuera: list[float], desde: float = 0.05, hasta: float = 1.20,
                      paso: float = 0.01) -> tuple[float, int, int]:
    """Umbral de distancia que deja pasar la mayor cantidad de preguntas de dentro y la menor de fuera.

    Prueba valores de `desde` a `hasta`; puntaje = dentro que pasan − fuera que pasan. Si varios valores
    empatan, toma el punto medio de ese rango (queda lejos de los dos grupos). Devuelve
    (umbral, dentro que pasan, fuera que pasan)."""
    candidatos = [round(desde + i * paso, 2) for i in range(int(round((hasta - desde) / paso)) + 1)]

    def puntaje(u: float) -> int:
        return sum(d <= u for d in dentro) - sum(f <= u for f in fuera)

    mejor = max(puntaje(u) for u in candidatos)
    empatados = [u for u in candidatos if puntaje(u) == mejor]
    # Solo el primer tramo seguido de empatados (si hubiera dos tramos separados, el de menor distancia).
    tramo = [empatados[0]]
    for u in empatados[1:]:
        if round(u - tramo[-1], 2) > paso:
            break
        tramo.append(u)
    umbral = round((tramo[0] + tramo[-1]) / 2, 2)
    return umbral, sum(d <= umbral for d in dentro), sum(f <= umbral for f in fuera)


def percentil(valores: list[float], p: float) -> float:
    """Percentil por el método del más cercano (p entre 0 y 100). 0 si no hay valores."""
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    indice = max(0, math.ceil(p / 100 * len(ordenados)) - 1)
    return ordenados[indice]


def promedio(valores: list[float]) -> float:
    return sum(valores) / len(valores) if valores else 0.0


# ---------------------------------------------------------------- medición

def ram_del_proceso_mb() -> float:
    """Memoria residente de este proceso (Linux). 0 si no se puede leer."""
    try:
        for linea in Path("/proc/self/status").read_text().splitlines():
            if linea.startswith("VmRSS:"):
                return int(linea.split()[1]) / 1024
    except OSError:
        pass
    return 0.0


def ram_total_mb() -> float:
    try:
        for linea in Path("/proc/meminfo").read_text().splitlines():
            if linea.startswith("MemTotal:"):
                return int(linea.split()[1]) / 1024
    except OSError:
        pass
    return 0.0


class LLMMedido(LLMOllama):
    """Igual que LLMOllama, pero con streaming para medir el tiempo al primer token."""

    def __init__(self, url: str, modelo: str, timeout: float):
        super().__init__(url, modelo, timeout)
        self.ultima: dict | None = None

    def generar(self, mensajes: list[dict[str, str]]) -> str:
        inicio = time.monotonic()
        primer_token = None
        partes: list[str] = []
        final: dict = {}
        try:
            with httpx.stream(
                "POST", f"{self.url}/api/chat",
                json={"model": self.nombre, "messages": mensajes, "stream": True,
                      "options": {"temperature": 0.1, "num_ctx": 4096}},
                timeout=self.timeout,
            ) as respuesta:
                if respuesta.status_code == 404:
                    raise ErrorLLM(f"El modelo {self.nombre} no está descargado en Ollama")
                respuesta.raise_for_status()
                for linea in respuesta.iter_lines():
                    if not linea.strip():
                        continue
                    trozo = json.loads(linea)
                    texto = trozo.get("message", {}).get("content", "")
                    if texto and primer_token is None:
                        primer_token = time.monotonic()
                    partes.append(texto)
                    if trozo.get("done"):
                        final = trozo
        except (httpx.HTTPError, ValueError) as error:
            raise ErrorLLM(f"{type(error).__name__}: {error}") from error
        fin = time.monotonic()
        self.ultima = {
            "ttft_ms": int(((primer_token or fin) - inicio) * 1000),
            "ms_llm": int((fin - inicio) * 1000),
            "tokens": final.get("eval_count", 0),
        }
        return "".join(partes).strip()

    def descargar_todos(self) -> None:
        """Saca de la memoria cualquier modelo cargado, para medir la carga desde cero."""
        try:
            cargados = httpx.get(f"{self.url}/api/ps", timeout=10).json().get("models", [])
            for m in cargados:
                httpx.post(f"{self.url}/api/generate", json={"model": m["name"], "keep_alive": 0}, timeout=60)
        except (httpx.HTTPError, ValueError):
            pass

    def ram_mb(self) -> float:
        """Memoria que ocupa el modelo según Ollama (/api/ps)."""
        try:
            for m in httpx.get(f"{self.url}/api/ps", timeout=10).json().get("models", []):
                if m.get("name") == self.nombre or m.get("model") == self.nombre:
                    return m.get("size", 0) / 1024 / 1024
        except (httpx.HTTPError, ValueError):
            pass
        return 0.0


# ---------------------------------------------------------------- resultados

@dataclass
class Fila:
    """Una pregunta con una combinación de modelos (una fila del CSV)."""
    embeddings: str
    llm: str
    id: str
    grupo: str  # "dentro" o "fuera"
    pregunta: str
    en_top1: bool | None = None
    en_top5: bool | None = None
    distancia_mejor: float | None = None
    distancia_faq: float | None = None
    estado: str = ""
    correcta: bool | None = None
    fuente_ok: bool | None = None
    rechazo_por: str = ""  # "búsqueda" o "modelo" (solo preguntas de fuera rechazadas)
    ttft_ms: int | None = None
    ms_total: int | None = None
    respuesta: str = ""


@dataclass
class ResultadoEmbeddings:
    modelo: str
    licencia: str
    carga_s: float
    ram_mb: float
    ingesta_s: float
    recall1: float
    recall5: float
    recall5_documento: float
    distancia_dentro: float
    distancia_fuera: float
    umbral: float
    dentro_pasan: int
    fuera_pasan: int
    umbral_faq: float
    faq_pasan: int
    no_faq_pasan: int


@dataclass
class ResultadoLLM:
    embeddings: str
    llm: str
    licencia: str
    carga_s: float
    ram_mb: float
    aciertos: int
    aciertos_con_fuente: int
    rechazos: int
    rechazos_busqueda: int
    rechazos_modelo: int
    sin_llm: int
    ms_promedio: float
    ms_p95: float
    ttft_promedio: float


@dataclass
class Informe:
    inicio: datetime
    n_dentro: int
    n_fuera: int
    n_documentos: int
    embeddings: list[ResultadoEmbeddings] = field(default_factory=list)
    llms: list[ResultadoLLM] = field(default_factory=list)
    filas: list[Fila] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- ejecución

def _titulos_por_archivo(corpus: Path) -> dict[str, str]:
    manifiesto = json.loads((corpus / "corpus.json").read_text(encoding="utf-8"))
    return {d["archivo"]: d["titulo"] for d in manifiesto["documentos"]}


def evaluar_busqueda(conexion: psycopg.Connection, emb: Embeddings, preguntas: dict, titulos: dict[str, str],
                     nombre_emb: str) -> tuple[list[Fila], dict]:
    filas: list[Fila] = []
    for grupo in ("dentro", "fuera"):
        for p in preguntas[grupo]:
            vector = emb.codificar([p["pregunta"]], es_consulta=True)[0]
            top = buscar_fragmentos(conexion, vector, 5)
            faq = buscar_faq(conexion, vector)
            fila = Fila(nombre_emb, "", p["id"], grupo, p["pregunta"],
                        distancia_mejor=round(top[0].distancia, 4) if top else None,
                        distancia_faq=round(faq.distancia, 4) if faq else None)
            if grupo == "dentro":
                esperado = (titulos[p["archivo"]], p["pagina"])
                lugares = [(f.titulo, f.pagina) for f in top]
                fila.en_top1 = esperado in lugares[:1]
                fila.en_top5 = esperado in lugares
                fila.fuente_ok = any(t == esperado[0] for t, _ in lugares)  # documento correcto en el top 5
            filas.append(fila)
    dentro = [f for f in filas if f.grupo == "dentro"]
    con_faq = {p["id"] for p in preguntas["dentro"] if p.get("faq")}

    def distancias(lista: list[Fila]) -> list[float]:
        return [f.distancia_mejor for f in lista if f.distancia_mejor is not None]

    umbral, dentro_pasan, fuera_pasan = umbral_que_separa(distancias(dentro), distancias([f for f in filas if f.grupo == "fuera"]))
    faq_si = [f.distancia_faq for f in filas if f.id in con_faq and f.distancia_faq is not None]
    faq_no = [f.distancia_faq for f in filas if f.id not in con_faq and f.distancia_faq is not None]
    umbral_faq, faq_pasan, no_faq_pasan = umbral_que_separa(faq_si, faq_no) if faq_si else (0.0, 0, 0)
    resumen = {
        "recall1": promedio([f.en_top1 for f in dentro]),
        "recall5": promedio([f.en_top5 for f in dentro]),
        "recall5_documento": promedio([f.fuente_ok for f in dentro]),
        "distancia_dentro": promedio(distancias(dentro)),
        "distancia_fuera": promedio(distancias([f for f in filas if f.grupo == "fuera"])),
        "umbral": umbral, "dentro_pasan": dentro_pasan, "fuera_pasan": fuera_pasan,
        "umbral_faq": umbral_faq, "faq_pasan": faq_pasan, "no_faq_pasan": no_faq_pasan,
    }
    for f in filas:
        f.fuente_ok = None  # en la fase de búsqueda solo se usó para el recall por documento
    return filas, resumen


class _Espia:
    """Envuelve el modelo para saber si `responder` llegó a llamarlo en esta pregunta."""

    def __init__(self, llm):
        self.llm = llm
        self.nombre = llm.nombre
        self.llamado = False

    def generar(self, mensajes: list[dict[str, str]]) -> str:
        self.llamado = True
        return self.llm.generar(mensajes)


def evaluar_llm(conexion: psycopg.Connection, emb: Embeddings, llm, preguntas: dict, titulos: dict[str, str],
                config: Configuracion, nombre_emb: str) -> list[Fila]:
    filas: list[Fila] = []
    turno = Turno(config.cola_maxima)
    for grupo in ("dentro", "fuera"):
        for p in preguntas[grupo]:
            if hasattr(llm, "ultima"):
                llm.ultima = None
            espia = _Espia(llm)
            r = responder(p["pregunta"], conexion, emb, espia, turno, config)
            medida = getattr(llm, "ultima", None)
            fila = Fila(nombre_emb, llm.nombre, p["id"], grupo, p["pregunta"], estado=r.estado, ms_total=r.ms,
                        ttft_ms=medida["ttft_ms"] if medida else None,
                        respuesta=" ".join(r.respuesta.split())[:400])
            if grupo == "dentro":
                fila.correcta = r.estado in (RESPONDIDA, FAQ) and cumple_claves(r.respuesta, p["claves"])
                fila.fuente_ok = r.estado == FAQ or any(f.titulo == titulos[p["archivo"]] for f in r.fuentes)
            else:
                fila.correcta = r.estado == SIN_EVIDENCIA
                if fila.correcta:
                    fila.rechazo_por = "modelo" if espia.llamado else "búsqueda"
            filas.append(fila)
    return filas


def resumir_llm(filas: list[Fila], nombre_emb: str, nombre_llm: str, carga_s: float, ram_mb: float) -> ResultadoLLM:
    dentro = [f for f in filas if f.grupo == "dentro"]
    fuera = [f for f in filas if f.grupo == "fuera"]
    con_modelo = [f for f in filas if f.ttft_ms is not None]
    return ResultadoLLM(
        embeddings=nombre_emb, llm=nombre_llm, licencia=LICENCIAS.get(nombre_llm, "por verificar"),
        carga_s=round(carga_s, 1), ram_mb=round(ram_mb),
        aciertos=sum(bool(f.correcta) for f in dentro),
        aciertos_con_fuente=sum(bool(f.correcta and f.fuente_ok) for f in dentro),
        rechazos=sum(bool(f.correcta) for f in fuera),
        rechazos_busqueda=sum(f.rechazo_por == "búsqueda" for f in fuera),
        rechazos_modelo=sum(f.rechazo_por == "modelo" for f in fuera),
        sin_llm=sum(f.estado == "sin_llm" for f in filas),
        ms_promedio=round(promedio([f.ms_total for f in filas if f.ms_total is not None])),
        ms_p95=round(percentil([f.ms_total for f in filas if f.ms_total is not None], 95)),
        ttft_promedio=round(promedio([f.ttft_ms for f in con_modelo])),
    )


def ejecutar(url: str, corpus: Path, preguntas: dict, modelos_emb: list[str], modelos_llm: list[str],
             config: Configuracion, proveedor: str = "sentence-transformers",
             crear_llm: Callable[[str], object] | None = None, umbral_fijo: float | None = None,
             umbral_faq_fijo: float | None = None, aviso: Callable[[str], None] = print) -> Informe:
    titulos = _titulos_por_archivo(corpus)
    faltan = {p["archivo"] for p in preguntas["dentro"]} - titulos.keys()
    if faltan:
        raise ValueError(f"preguntas.json usa archivos que no están en corpus.json: {sorted(faltan)}")
    informe = Informe(datetime.now(LIMA), len(preguntas["dentro"]), len(preguntas["fuera"]), len(titulos))
    crear_llm = crear_llm or (lambda nombre: LLMMedido(config.ollama_url, nombre, config.timeout_llm))
    llms = {nombre: crear_llm(nombre) for nombre in modelos_llm}

    for nombre_emb in modelos_emb:
        aviso(f"\n== Embeddings: {nombre_emb}")
        gc.collect()
        ram_antes = ram_del_proceso_mb()
        inicio = time.monotonic()
        emb = _crear(proveedor, nombre_emb)  # sin la caché de la API: cada modelo se libera al terminar
        carga_s = time.monotonic() - inicio
        ram_emb = max(ram_del_proceso_mb() - ram_antes, 0.0)
        with psycopg.connect(url) as conexion:
            # Todo dentro de una transacción que se deshace: la base real no cambia.
            with conexion.transaction(force_rollback=True):
                conexion.execute("DELETE FROM faqs")
                conexion.execute("DELETE FROM documentos")
                inicio = time.monotonic()
                cargar_corpus(conexion, emb, corpus)
                ingesta_s = time.monotonic() - inicio
                filas, r = evaluar_busqueda(conexion, emb, preguntas, titulos, nombre_emb)
                informe.filas += filas
                informe.embeddings.append(ResultadoEmbeddings(
                    nombre_emb, LICENCIAS.get(nombre_emb, "por verificar"), round(carga_s, 1), round(ram_emb),
                    round(ingesta_s, 1), **r))
                aviso(f"   recall@5 {r['recall5']:.0%} · umbral propuesto {r['umbral']} · umbral FAQ {r['umbral_faq']}")

                umbral = umbral_fijo if umbral_fijo is not None else r["umbral"]
                umbral_faq = umbral_faq_fijo if umbral_faq_fijo is not None else r["umbral_faq"]
                config_bench = config.model_copy(update={"umbral_distancia": umbral, "umbral_faq": umbral_faq})
                for nombre_llm, llm in llms.items():
                    aviso(f"   -- Modelo de lenguaje: {nombre_llm} (umbral {umbral}, FAQ {umbral_faq})")
                    carga_llm, ram_llm = 0.0, 0.0
                    if isinstance(llm, LLMMedido):
                        llm.descargar_todos()
                        inicio = time.monotonic()
                        if not llm.precargar():
                            informe.avisos.append(f"{nombre_llm}: no se pudo cargar (¿falta `ollama pull {nombre_llm}`"
                                                  " o no hay RAM libre?). Sus respuestas salen como sin_llm.")
                        carga_llm = time.monotonic() - inicio
                        ram_llm = llm.ram_mb()
                    filas_llm = evaluar_llm(conexion, emb, llm, preguntas, titulos, config_bench, nombre_emb)
                    informe.filas += filas_llm
                    resultado = resumir_llm(filas_llm, nombre_emb, nombre_llm, carga_llm, ram_llm)
                    informe.llms.append(resultado)
                    aviso(f"      aciertos con fuente {resultado.aciertos_con_fuente}/{informe.n_dentro} · "
                          f"rechazos {resultado.rechazos}/{informe.n_fuera} · {resultado.ms_promedio / 1000:.1f} s promedio")
        del emb
        gc.collect()

    if proveedor == "hash":
        informe.avisos.insert(0, "Embeddings «hash» (solo para pruebas): estos números NO miden la calidad del tutor.")
    return informe


# ---------------------------------------------------------------- informe

def _pct(x: float) -> str:
    return f"{round(x * 100)} %"


def _dec(x: float, decimales: int = 1) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


def _s(ms: float) -> str:
    return f"{_dec(ms / 1000)} s"


def informe_markdown(inf: Informe) -> str:
    fecha = inf.inicio.strftime("%d/%m/%Y %H:%M")
    lineas = [
        f"# Benchmark del Tutor Virtual – {fecha}",
        "",
        f"Corpus: {inf.n_documentos} documentos · Preguntas: {inf.n_dentro} dentro de los documentos y "
        f"{inf.n_fuera} fuera de alcance · Equipo: {os.cpu_count()} núcleos, {_dec(ram_total_mb() / 1024)} GB de RAM"
        " visibles para el contenedor.",
        "",
    ]
    for a in inf.avisos:
        lineas += [f"> **Aviso:** {a}", ""]

    lineas += [
        "## 1. Búsqueda (modelos de embeddings)",
        "",
        "- **recall@5**: de las preguntas de dentro, en cuántas el fragmento con la respuesta (documento y página)"
        f" quedó entre los 5 más cercanos. Meta de la Fase 2: {_pct(META_RECALL5)}.",
        "- **Umbral propuesto**: la distancia que mejor separa las preguntas de dentro de las de fuera."
        " Las de fuera que pasan el umbral las tiene que rechazar el modelo de lenguaje.",
        "",
        "Los umbrales van con punto porque así se copian al `.env`.",
        "",
        "| Modelo | Licencia | Carga | RAM | recall@1 | recall@5 | recall@5 (solo documento) | Distancia media dentro / fuera | Umbral propuesto | Pasan dentro / fuera | Umbral FAQ propuesto |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for e in inf.embeddings:
        lineas.append(
            f"| {e.modelo} | {e.licencia} | {_dec(e.carga_s)} s | {e.ram_mb} MB | {_pct(e.recall1)} | **{_pct(e.recall5)}** | "
            f"{_pct(e.recall5_documento)} | {_dec(e.distancia_dentro, 2)} / {_dec(e.distancia_fuera, 2)} | {e.umbral} | "
            f"{e.dentro_pasan}/{inf.n_dentro} · {e.fuera_pasan}/{inf.n_fuera} | {e.umbral_faq} |"
        )

    if inf.llms:
        lineas += [
            "",
            "## 2. Respuestas (modelos de lenguaje)",
            "",
            "- **Aciertos con fuente**: respuesta con los datos esperados y citando el documento correcto (o FAQ).",
            "- **Rechazos correctos**: preguntas de fuera en las que el tutor se abstuvo y derivó al canal humano"
            " (por la búsqueda, sin llamar al modelo, o porque el modelo respondió SIN_EVIDENCIA).",
            "- Tiempos medidos en este equipo, una pregunta a la vez. RAM del modelo según Ollama.",
            "",
            "| Embeddings | Modelo de lenguaje | Licencia | Carga | RAM | Aciertos con fuente | Rechazos correctos (búsqueda + modelo) | sin_llm | Primer token (promedio) | Respuesta (promedio / p95) |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for r in inf.llms:
            lineas.append(
                f"| {r.embeddings.split('/')[-1]} | {r.llm} | {r.licencia} | {_dec(r.carga_s)} s | {r.ram_mb} MB | "
                f"**{r.aciertos_con_fuente}/{inf.n_dentro}** | **{r.rechazos}/{inf.n_fuera}** "
                f"({r.rechazos_busqueda} + {r.rechazos_modelo}) | {r.sin_llm} | {_s(r.ttft_promedio)} | "
                f"{_s(r.ms_promedio)} / {_s(r.ms_p95)} |"
            )
        fallos = [f for f in inf.filas if f.llm and not (f.correcta and (f.grupo == "fuera" or f.fuente_ok))]
        lineas += ["", "## 3. Preguntas que fallaron", ""]
        if not fallos:
            lineas.append("Ninguna.")
        else:
            lineas += ["| Embeddings | Modelo | Pregunta | Estado | Qué pasó |", "|---|---|---|---|---|"]
            for f in fallos:
                if f.grupo == "fuera":
                    motivo = "respondió una pregunta que debía rechazar"
                elif f.estado not in (RESPONDIDA, FAQ):
                    motivo = "no respondió"
                elif not f.correcta:
                    motivo = "faltan los datos esperados"
                else:
                    motivo = "citó otro documento"
                texto = f.respuesta[:160].replace("|", "/")
                lineas.append(f"| {f.embeddings.split('/')[-1]} | {f.llm} | {f.id}: {f.pregunta} | {f.estado} | "
                              f"{motivo}: «{texto}» |")

    lineas += [
        "",
        "## Cómo se elige",
        "",
        f"1. Embeddings: el de mayor recall@5 (mínimo {_pct(META_RECALL5)}); si empatan, el que separa mejor dentro y fuera"
        " y ocupa menos RAM.",
        "2. Modelo de lenguaje: el que tiene más aciertos con fuente **sin fallar rechazos** (inventar es peor que no"
        " responder); si empatan, el más rápido y liviano. Todo el stack debe caber en ~4 GB del equipo del CEE.",
        "3. Los umbrales propuestos se copian al `.env` (`UMBRAL_DISTANCIA`, `UMBRAL_FAQ`) junto con el modelo elegido:"
        " cada modelo de embeddings mide las distancias en su propia escala.",
        "",
        "El detalle de cada pregunta está en el CSV del mismo nombre.",
    ]
    return "\n".join(lineas) + "\n"


def guardar(inf: Informe, carpeta: Path) -> tuple[Path, Path]:
    carpeta.mkdir(parents=True, exist_ok=True)
    base = carpeta / inf.inicio.strftime("%Y-%m-%d_%H%M")
    md, csv_ = base.with_suffix(".md"), base.with_suffix(".csv")
    md.write_text(informe_markdown(inf), encoding="utf-8")
    with csv_.open("w", encoding="utf-8-sig", newline="") as archivo:  # utf-8-sig: Excel lo abre con tildes
        campos = list(asdict(inf.filas[0]).keys()) if inf.filas else list(Fila.__dataclass_fields__)
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        for f in inf.filas:
            escritor.writerow(asdict(f))
    return md, csv_


def _lista(texto: str) -> list[str]:
    return [x.strip() for x in re.split(r"[,;]", texto) if x.strip()]


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.benchmark", description="Compara modelos con el set de preguntas.")
    parser.add_argument("--preguntas", type=Path, default=Path("/benchmark/preguntas.json"))
    parser.add_argument("--corpus", type=Path, default=Path("/corpus/prueba"))
    parser.add_argument("--salida", type=Path, default=Path("/benchmark/resultados"))
    parser.add_argument("--embeddings", type=_lista, default=EMBEDDINGS_POR_DEFECTO,
                        help="Modelos separados por coma")
    parser.add_argument("--llm", type=_lista, default=LLM_POR_DEFECTO, help="Modelos de Ollama separados por coma")
    parser.add_argument("--solo-busqueda", action="store_true", help="Sin modelo de lenguaje (rápido)")
    parser.add_argument("--umbral", type=float, help="Usar este umbral en vez del propuesto")
    parser.add_argument("--umbral-faq", type=float, help="Usar este umbral de FAQ en vez del propuesto")
    args = parser.parse_args(argumentos)

    config = obtener_configuracion()
    preguntas = json.loads(args.preguntas.read_text(encoding="utf-8"))
    print(f"Benchmark: {len(preguntas['dentro'])} preguntas dentro y {len(preguntas['fuera'])} fuera.")
    print("La primera vez descarga los modelos de embeddings. Con modelo de lenguaje tarda unos 30–60 min.", flush=True)
    try:
        inf = ejecutar(config.database_url, args.corpus, preguntas, args.embeddings,
                       [] if args.solo_busqueda else args.llm, config, proveedor=config.embeddings_proveedor,
                       umbral_fijo=args.umbral, umbral_faq_fijo=args.umbral_faq,
                       aviso=lambda m: print(m, flush=True))
    except (ValueError, FileNotFoundError, psycopg.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        if not args.solo_busqueda:
            # Deja cargado el modelo que usa el chat, para que la próxima pregunta no espere la carga.
            print(f"Volviendo a cargar {config.llm_modelo} para el chat...", flush=True)
            LLMOllama(config.ollama_url, config.llm_modelo, config.timeout_llm).precargar()
    md, csv_ = guardar(inf, args.salida)
    print(f"\nInforme: {md}\nDetalle: {csv_}")
    for a in inf.avisos:
        print(f"Aviso: {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
