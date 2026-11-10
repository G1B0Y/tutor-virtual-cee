"""Curso Sistemas Integrados Empresariales (09/11/2026): los 3 módulos (Marketing, Ventas y CRM) se leen bien y las
preguntas de razonamiento del profesor se reconocen y se responden solo con los conceptos de los documentos."""

import json
from pathlib import Path

import pytest

from app.config import Configuracion
from app.rag.fragmentar import extraer_paginas, fragmentar, limpiar, palabra_por_linea
from app.rag.prompt import RAZONAMIENTO, armar_mensajes
from app.rag.razonamiento import es_razonamiento
from app.rag.respaldo import revisar

RAIZ = Path(__file__).resolve().parents[2]
CARPETA = RAIZ / "corpus" / "sie"
MANIFIESTO = json.loads((CARPETA / "corpus.json").read_text(encoding="utf-8"))
PREGUNTAS = json.loads((RAIZ / "benchmark" / "preguntas_sie.json").read_text(encoding="utf-8"))


def test_el_curso_tiene_los_3_modulos():
    assert [d["archivo"] for d in MANIFIESTO["documentos"]] == ["sie_marketing.pdf", "sie_ventas.pdf", "sie_crm.pdf"]
    assert {d["curso"] for d in MANIFIESTO["documentos"]} == {"Sistemas Integrados Empresariales"}


def test_los_titulos_no_chocan_con_otros_corpus():
    otros = set()
    for carpeta in ("prueba", "complementario"):
        manifiesto = json.loads((RAIZ / "corpus" / carpeta / "corpus.json").read_text(encoding="utf-8"))
        otros |= {d["titulo"] for d in manifiesto["documentos"]}
    assert not otros & {d["titulo"] for d in MANIFIESTO["documentos"]}


@pytest.mark.parametrize("doc", MANIFIESTO["documentos"], ids=lambda d: d["archivo"])
def test_los_pdf_de_google_docs_se_leen_por_lineas(doc):
    # Error del 09/11/2026: pypdf sacaba una palabra por línea y los fragmentos se cortaban en cualquier palabra.
    paginas = extraer_paginas(CARPETA / doc["archivo"])
    texto = "\n".join(paginas)
    assert not palabra_por_linea(texto)
    assert "​" not in texto
    lineas = [l for l in texto.splitlines() if l.strip()]
    assert sum(len(l.split()) >= 5 for l in lineas) / len(lineas) > 0.7
    fragmentos = fragmentar(paginas)
    assert fragmentos and all(len(f.texto) <= 900 for f in fragmentos)


def test_el_texto_de_cada_modulo_tiene_sus_conceptos_clave():
    texto = {d["archivo"]: " ".join(" ".join(extraer_paginas(CARPETA / d["archivo"])).split())
             for d in MANIFIESTO["documentos"]}
    assert "Amigos Verdaderos (Alta Rentabilidad / Alta Lealtad)" in texto["sie_marketing.pdf"]
    assert "Mientras no se vise no se pasa" in texto["sie_ventas.pdf"]
    assert "son cuatro cosas que hace CRM" in texto["sie_crm.pdf"]


def test_palabra_por_linea_no_confunde_un_pdf_normal():
    assert palabra_por_linea("\n \n".join("una palabra por linea en este pdf de google docs que sale mal".split() * 3))
    assert not palabra_por_linea("Unidad 1 – Pensamiento Lean\nLos 8 desperdicios\nMapa de flujo de valor\n" * 10)
    assert not palabra_por_linea("Título\nCorto")  # pocas líneas: no se decide nada


def test_limpiar_quita_espacios_de_ancho_cero():
    assert limpiar("●​ Lógica operativa") == "● Lógica operativa"


@pytest.mark.parametrize("pregunta", [
    "Una pollería recibe la queja de un cliente porque su pedido llegó tarde, ¿qué área debe atenderlo?",
    "¿Por qué el cliente no debería tener contacto con el vendedor después de la venta?",
    "¿Qué pasaría si una empresa industrial empieza a fabricar sin orden de pedido?",
    "¿En qué se diferencia una mariposa de un amigo verdadero?",
    "Si un cliente compra poco pero viene siempre, ¿conviene invertir en él?",
    "¿Cómo se relaciona el CRM con el proceso de marketing?",
    "¿Es correcto decir que un vendedor que entrega muchas proformas es exitoso?",
    "Supongamos que un banco quiere retener a un millennial, ¿qué haría según el curso?",
    "¿A quién le corresponde visar la orden de pedido?",
])
def test_reconoce_preguntas_de_razonamiento(pregunta):
    assert es_razonamiento(pregunta)


@pytest.mark.parametrize("pregunta", [
    "¿Qué es el CRM?",
    "¿Cuáles son las 4 P del marketing mix?",
    "¿Cuáles son las etapas del embudo de ventas?",
    "¿Qué es la visación?",
    "¿Cuántas horas dura el programa de Gestión de la Cadena de Suministro?",
    "¿Cómo se calcula el inventario de seguridad?",
    "¿Por qué se llama lote económico?",
])
def test_no_confunde_preguntas_directas(pregunta):
    assert not es_razonamiento(pregunta)


def test_las_preguntas_directas_del_benchmark_original_siguen_el_camino_normal():
    # El benchmark de 30 preguntas (corpus de prueba) ya dio 20/20 y 10/10: no se le cambia el camino a las de dentro.
    originales = json.loads((RAIZ / "benchmark" / "preguntas.json").read_text(encoding="utf-8"))
    assert [p["id"] for p in originales["dentro"] if es_razonamiento(p["pregunta"])] == []


def test_el_benchmark_del_curso_marca_bien_sus_preguntas():
    for p in PREGUNTAS["dentro"]:
        assert es_razonamiento(p["pregunta"]) == p.get("razonamiento", False), p["id"]
    archivos = {d["archivo"] for d in MANIFIESTO["documentos"]}
    assert {p["archivo"] for p in PREGUNTAS["dentro"]} <= archivos
    assert sum(p.get("razonamiento", False) for p in PREGUNTAS["dentro"]) >= 8


def test_el_prompt_de_razonamiento_solo_va_cuando_se_pide():
    normal = armar_mensajes("¿Qué es el CRM?", [])[0]["content"]
    razonada = armar_mensajes("¿Por qué…?", [], razonar=True)[0]["content"]
    assert RAZONAMIENTO not in normal
    assert razonada.endswith(RAZONAMIENTO) and "SIN_EVIDENCIA" in RAZONAMIENTO


CRM = ("[1] Sistemas Integrados Empresariales – Módulo de CRM: gestión, post-venta y fidelización, página 1. "
       "Una regla de oro en la teoría comercial es que, una vez finalizada la transacción, el cliente no va a tener "
       "contacto con el vendedor. El cliente debe comunicarse con un área que lo pueda atender y que conozca el producto "
       "y que conozca el negocio. Su función inicial es registrar el reclamo y luego derivar el reclamo a quien le "
       "corresponde. CRM va a hacer el seguimiento post-venta y es quien va a dar la cara.")
PREGUNTA_CASO = ("Una pollería recibe la queja de un cliente porque su pedido del Día de la Madre llegó tarde, "
                 "¿qué área debe atenderlo y qué debe hacer?")


def test_una_respuesta_razonada_con_los_conceptos_del_modulo_pasa_el_control():
    respuesta = ("Debe atenderlo el área de CRM, no el vendedor. Según el módulo de CRM, una vez finalizada la "
                 "transacción el cliente no debe tener contacto con el vendedor, sino con un área que conozca el "
                 "producto y el negocio. Por lo tanto, en este caso el CRM registra el reclamo del pedido, lo deriva "
                 "a quien le corresponde y hace el seguimiento post-venta para dar la cara ante el cliente.")
    texto, _ = revisar(respuesta, [CRM], PREGUNTA_CASO, Configuracion().minimo_respaldo_razonamiento)
    assert texto is not None
    assert texto.startswith("Debe atenderlo el área de CRM")
    assert "seguimiento post-venta" in texto


def test_en_una_respuesta_razonada_se_siguen_quitando_las_cifras_y_la_teoria_inventadas():
    respuesta = ("Debe atenderlo el área de CRM. El CRM registra el reclamo y lo deriva a quien le corresponde. "
                 "Según estudios, el 70 % de los clientes que reciben respuesta en 24 horas vuelven a comprar. "
                 "Kotler recomienda aplicar el modelo SERVQUAL de cinco dimensiones de calidad percibida.")
    texto, _ = revisar(respuesta, [CRM], PREGUNTA_CASO, Configuracion().minimo_respaldo_razonamiento)
    assert texto is not None
    assert "70" not in texto and "SERVQUAL" not in texto
    assert "Debe atenderlo el área de CRM" in texto


def test_el_prompt_de_razonamiento_pide_si_o_no_brevedad_y_no_abstenerse_por_no_estar_literal():
    # Benchmark del curso en la PC de Alfredo (09/11/2026): "¿Es correcto que el vendedor lo atienda?" → "Sí, es
    # correcto…" (al revés del módulo); R05 y R06 se abstuvieron; R08 y R09 llegaron al tope de 512 tokens.
    assert '"Sí" o "No"' in RAZONAMIENTO
    assert "NO es motivo" in RAZONAMIENTO
    assert "Máximo 100 palabras" in RAZONAMIENTO
    assert "biblioteca" in RAZONAMIENTO  # el ejemplo es de otro tema: no le da datos del curso


def test_el_segundo_intento_de_razonamiento_tiene_su_propio_aviso():
    from app.rag.prompt import REINTENTO, REINTENTO_RAZONAMIENTO, mensajes_de_reintento

    mensajes = armar_mensajes("¿Por qué…?", [], razonar=True)
    assert mensajes_de_reintento(mensajes)[-1]["content"].endswith(REINTENTO)
    assert mensajes_de_reintento(mensajes, REINTENTO_RAZONAMIENTO)[-1]["content"].endswith(REINTENTO_RAZONAMIENTO)


def test_el_benchmark_no_da_por_buena_una_conclusion_al_reves():
    from app.benchmark import cumple_claves, dice_lo_prohibido

    r12 = next(p for p in PREGUNTAS["dentro"] if p["id"] == "R12")
    al_reves = "Sí, es correcto que el vendedor lo atienda; no hace falta derivarlo al CRM."
    assert cumple_claves(al_reves, r12["claves"]) and dice_lo_prohibido(al_reves, r12["no_debe_decir"])
    bien = "No, no es correcto. Según el módulo de CRM, después de la venta el cliente debe ser atendido por el CRM."
    assert cumple_claves(bien, r12["claves"]) and not dice_lo_prohibido(bien, r12["no_debe_decir"])


def test_la_categoria_del_cliente_queda_en_el_mismo_fragmento_que_su_ejemplo():
    # R03 (10/11/2026): "3. Clientes Preferidos…: Compran / poco (ej. / piden solo un cuarto de pollo…" se partía por
    # el salto de línea y por el punto de "ej."; granite y qwen3 respondían con otra categoría.
    from app.rag.fragmentar import _oraciones, extraer_paginas, fragmentar

    assert _oraciones("Compran\npoco (ej. piden solo un cuarto), pero van siempre. Ver p. ej. la pág. 4.\nTítulo\nOtra.") == [
        "Compran poco (ej. piden solo un cuarto), pero van siempre.", "Ver p. ej. la pág. 4.", "Título", "Otra."]
    con_pollo = [f.texto for f in fragmentar(extraer_paginas(CARPETA / "sie_marketing.pdf")) if "cuarto de pollo" in f.texto]
    assert con_pollo and all("Clientes Preferidos" in t for t in con_pollo)
