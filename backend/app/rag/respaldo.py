"""Control de respaldo: lo que dice el tutor tiene que estar en los documentos que se le dieron al modelo.

Regla del proyecto (Alfredo, 08/11/2026): "no debería inventar nada de lo que no está en la información cargada".
granite3.3:2b no la cumple siempre: a "¿cuáles son los 8 desperdicios?" (el temario los nombra sin listarlos)
respondió tres listas inventadas distintas, y en respuestas correctas agrega frases propias ("Definir: identificar
el problema…"). Contar palabras sueltas no sirve: las listas inventadas usaban palabras que sí están en otros
documentos (inventario, defectos, tiempo de espera).

Por eso la respuesta se revisa por partes, sin depender del modelo:
- Cada elemento de una lista (lo que va antes de ":") tiene que aparecer como frase en los documentos: sus palabras
  con contenido seguidas, en ese orden ("mano de obra", "tiempo de espera"). Si más de un tercio no aparece, la lista
  es inventada y el tutor se abstiene. Los que no aparecen se quitan.
- Cada oración, y la explicación de cada elemento, se queda solo si al menos el 60 % (`MINIMO_RESPALDO`) de sus
  palabras con contenido está en los documentos o en la pregunta; si no, se quita.
- En un texto corrido, si la primera oración (la respuesta directa) no está en los documentos, el tutor se abstiene;
  si está, se queda con las oraciones respaldadas ("¿Qué es un VSM?" queda solo con la primera). En una lista, se
  abstiene si se quitaron más de dos tercios. En una lista respaldada, las explicaciones y el
  comentario final que se quitan no cuentan para eso.
- Toda cifra (porcentaje, horas, nota, fecha) tiene que estar en los documentos o en la pregunta: si no, se quita
  la oración o el elemento. Granite cambió los porcentajes de la clasificación ABC ("el 10 % de los ítems").
- Los títulos de los documentos cuentan como parte de ellos ("Lean Six Sigma Green Belt").
- Una aclaración entre paréntesis sin respaldo se quita sola ("CTQ (Customer-Supplier Quality)").
"""

import re
import unicodedata

# Palabras frecuentes que no dicen nada del contenido (y las que el modelo usa para redactar).
_VACIAS = set("""
    para como esta este esto estos estas tiene tienen sobre entre desde hasta donde cuando cual cuales porque pero
    tambien puede pueden debe deben cada todo toda todos todas otro otra otros otras mismo misma muy mas menos
    siguiente siguientes manera forma incluye incluyen trata tratan esta estan ser son sera seran hace hacen
    curso cursos tema temas unidad unidades documento documentos segun parte partes general importante clave
    claves alumno alumnos pregunta respuesta informacion materiales material programa siguiente ejemplo
    refiere significa significan consiste utiliza utilizan permite permiten llama llaman conoce conocen
    entonces tanto deberia deberian conviene ello razon debido decir caso casos aplica aplicar aplicarse aplicado
    conclusion concluye primero segundo luego finalmente situacion modulo modulos dado ademas mientras
    """.split())
# La última línea (09/11/2026): conectores de un razonamiento ("por lo tanto", "en este caso", "según el módulo"),
# que no dicen nada del contenido y no deben bajar el respaldo de una respuesta razonada.

_ITEM = re.compile(r"(?:^|\s)(\d{1,2}[.)]|[-•*])\s+")
# Si la lista está numerada, el guion no marca ítems: "1. Seiri - Clasificar… 2. Seiton - Ordenar…" (08/11/2026).
_ITEM_NUMERADO = re.compile(r"(?:^|\s)(\d{1,2}[.)])\s+")
_NUMEROS_EN_PALABRAS = {"dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
                        "diez": 10, "once": 11, "doce": 12}
_CANTIDAD_PEDIDA = re.compile(r"\b(?:los|las|sus|cu[aá]les son)\s+(\d{1,2}|" + "|".join(_NUMEROS_EN_PALABRAS) +
                              r")\s*[a-zñ]", re.IGNORECASE)


def cantidad_pedida(pregunta: str) -> int | None:
    """Cuántos elementos pide la pregunta: "las 5S" → 5, "los ocho desperdicios" → 8; "PMBOK 8.ª edición" → None."""
    hallados = _CANTIDAD_PEDIDA.findall(pregunta)
    if not hallados:
        return None
    valor = hallados[-1].lower()
    n = int(valor) if valor.isdigit() else _NUMEROS_EN_PALABRAS[valor]
    return n if 2 <= n <= 20 else None
_ORACION = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])")


def _palabras(texto: str) -> list[str]:
    """Raíces (5 letras) de las palabras con contenido, en orden."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))
    return [p[:5] for p in re.findall(r"[a-zñ]{4,}", sin_tildes) if p not in _VACIAS]


def _numeros(texto: str) -> set[str]:
    """Cifras del texto ("80 %", "4,5", "2026"), con coma o punto decimal igualados."""
    return {n.replace(",", ".") for n in re.findall(r"\d+(?:[.,]\d+)?", texto)}


def _raices(texto: str) -> set[str]:
    return set(_palabras(texto))


def respaldo(respuesta: str, fragmentos: list[str], pregunta: str = "") -> float:
    """Fracción (0–1) de las raíces de la respuesta que están en los fragmentos o en la pregunta.
    Raíz = primeras 5 letras, para aceptar plurales y conjugaciones ("desperdicios" ~ "desperdicio")."""
    propias = _raices(respuesta)
    if not propias:
        return 1.0
    fuente = _raices(" ".join(fragmentos) + " " + pregunta)
    return len(propias & fuente) / len(propias)


def _frase_en(frase: list[str], fuentes: list[list[str]]) -> bool:
    """Las raíces de `frase` aparecen seguidas y en orden en alguna fuente (se toleran 2 palabras entre medio:
    "estimación pesimista" está en "la estimación optimista (O), la más probable (M) y la pesimista (P)")."""
    if not frase:
        return True
    for fuente in fuentes:
        for inicio, raiz in enumerate(fuente):
            if raiz != frase[0]:
                continue
            pos, ok = inicio, True
            for siguiente in frase[1:]:
                ventana = fuente[pos + 1: pos + 4]
                if siguiente not in ventana:
                    ok = False
                    break
                pos = pos + 1 + ventana.index(siguiente)
            if ok:
                return True
    return False


_LINEA_ITEM = re.compile(r"^\s*(\d{1,2}[.)]|[-•*])\s+(.*)$")


def _partir(respuesta: str) -> tuple[str, list[tuple[str, str]], str]:
    """(texto antes de la lista, [(marca, ítem)], texto después de la lista); sin lista: (respuesta, [], "").

    Si 3 líneas o más empiezan con "1." o "-", solo esas son ítems: en una fórmula, "(4 + 4×6 + 14) / 6" o
    "(P - O) / 6" tienen "14)" y "- " que no son ítems (08/11/2026, PERT). Lo que viene en líneas después del último
    ítem es un comentario aparte ("Duración esperada = …"). Si no, se buscan ítems en una sola línea ("1. … 2. …")."""
    lineas = respuesta.strip().splitlines()
    marcadas = [n for n, linea in enumerate(lineas) if _LINEA_ITEM.match(linea)]
    if len(marcadas) >= 3:
        lista: list[tuple[str, str]] = []
        for k, n in enumerate(marcadas):
            fin = marcadas[k + 1] if k + 1 < len(marcadas) else n + 1
            marca, texto = _LINEA_ITEM.match(lineas[n]).groups()
            lista.append((marca, " ".join([texto, *[l.strip() for l in lineas[n + 1:fin]]]).strip()))
        antes = " ".join(l.strip() for l in lineas[:marcadas[0]])
        despues = " ".join(l.strip() for l in lineas[marcadas[-1] + 1:])
        return antes, lista, despues
    partes = _ITEM_NUMERADO.split(respuesta)
    if len(partes) <= 6:
        partes = _ITEM.split(respuesta)
    if len(partes) <= 6:  # menos de 3 ítems
        return respuesta, [], ""
    return partes[0], list(zip(partes[1::2], partes[2::2])), ""


def items(respuesta: str) -> list[str]:
    """Ítems de una enumeración ("1. …  2. …" o "- …"), aunque vengan en una sola línea."""
    return [t.strip() for _, t in _partir(respuesta)[1] if t.strip()]


def revisar(respuesta: str, fragmentos: list[str], pregunta: str = "", minimo: float = 0.6) -> tuple[str | None, str]:
    """Devuelve (texto con solo lo respaldado, motivo). Texto None = abstenerse."""
    if isinstance(fragmentos, str):  # un solo texto: sin esto se recorrería letra por letra y todo quedaría sin respaldo
        fragmentos = [fragmentos]
    fuentes = [_palabras(f) for f in fragmentos] + [_palabras(pregunta)]
    conocidas = set().union(*fuentes)
    cifras = _numeros(" ".join(fragmentos) + " " + pregunta)

    def aclaracion_ok(m: re.Match) -> str:
        # Una aclaración entre paréntesis sin respaldo se quita sola, sin tocar la oración: granite escribió
        # "el árbol de CTQ (Customer-Supplier Quality)" y CTQ es Critical to Quality (08/11/2026).
        dentro = m.group(1)
        if not dentro.strip():
            return ""
        propias = _raices(dentro)
        if not _numeros(dentro) <= cifras or (propias and len(propias & conocidas) / len(propias) < minimo):
            return ""
        return m.group(0)

    # Ningún documento del CEE está en japonés ni en chino: granite escribió "Seiri (ソリ)" y otros kanji inventados.
    respuesta = re.sub(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\uac00-\ud7af]+", "", respuesta)
    respuesta = re.sub(r"[ \t]*\(([^()]*)\)", aclaracion_ok, respuesta)

    def cifras_ok(texto: str) -> bool:
        # Una cifra que no está en los documentos es el error más grave para un alumno (porcentajes, horas, notas).
        return _numeros(texto) <= cifras

    def oracion_ok(texto: str) -> bool:
        if not cifras_ok(texto):
            return False
        propias = _raices(texto)
        return not propias or len(propias & conocidas) / len(propias) >= minimo

    antes, lista, despues = _partir(respuesta)
    es_lista = bool(lista)  # 3 ítems o más
    salida: list[str] = []
    quitadas = total = 0

    def agregar_oraciones(texto: str, cuenta: bool = True) -> None:
        """`cuenta=False`: las oraciones sin respaldo se quitan pero no llevan a abstenerse."""
        nonlocal quitadas, total
        for oracion in _ORACION.split(texto.strip()):
            if not oracion.strip():
                continue
            peso = len(_raices(oracion)) if cuenta else 0
            total += peso
            if oracion_ok(oracion):
                salida.append(oracion.strip())
            else:
                quitadas += peso

    if not es_lista:
        primera = next((o for o in _ORACION.split(respuesta.strip()) if o.strip()), "")
        if not oracion_ok(primera):
            # La primera oración suele ser la respuesta directa: si no está en los documentos, el resto es relleno.
            return None, "la primera oración no está en los documentos"
        agregar_oraciones(respuesta)
    else:
        agregar_oraciones(antes)
        malos = 0
        for n, (marca, item) in enumerate(lista):
            item = item.strip()
            resto = ""
            if n == len(lista) - 1:  # tras el último ítem suele venir texto suelto
                trozos = _ORACION.split(item, maxsplit=1)
                item, resto = trozos[0], (trozos[1] if len(trozos) > 1 else "")
                resto = f"{resto} {despues}".strip()
            # "Nombre: explicación" o "Nombre = fórmula" ("Disponibilidad = tiempo de operación / …").
            # También "Nombre - explicación" ("Seiri - Clasificar…").
            cabeza, separador, explicacion = (re.split(r"(:| = | [-–] )", item, maxsplit=1) + ["", ""])[:3]
            nombre = cabeza
            if len(cabeza.split()) > 6:
                cabeza = nombre = item
                separador = explicacion = ""
            else:
                # Lo que va entre paréntesis en el nombre es una aclaración ("Disponibilidad (Availability)",
                # "Optimista (O)"): la frase que tiene que estar en los documentos es el nombre.
                nombre = re.sub(r"\([^)]*\)", " ", cabeza)
            peso = len(_raices(item))
            total += peso
            if not _frase_en(_palabras(nombre), fuentes) or not cifras_ok(cabeza):
                malos += 1
                quitadas += peso
                continue
            if explicacion.strip() and not oracion_ok(explicacion):
                # Se quita la explicación propia del modelo, pero el elemento sí está en los documentos: no cuenta
                # para abstenerse ("Definir: identificar el problema…" → "Definir").
                total -= len(_raices(explicacion))
                explicacion = ""
            sep = ":" if separador.strip() == ":" else f" {separador.strip()}"
            salida.append(f"{marca} {cabeza.strip()}" + (f"{sep} {explicacion.strip()}" if explicacion.strip() else ""))
            if resto:
                # Comentario del modelo después de la lista ("Estas son las etapas…"): si no tiene respaldo se
                # quita, pero la lista, que sí está en los documentos, se mantiene.
                agregar_oraciones(resto, cuenta=False)
        if malos * 3 > len(lista):
            return None, f"lista con {malos} de {len(lista)} elementos que no están en los documentos"
        pedida = cantidad_pedida(pregunta)
        if malos and pedida and len(lista) - malos < pedida:
            # "¿Cuáles son las 5S?" y quedaban solo Seiso y Seiketsu: una lista a medias se lee como si fuera completa.
            return None, f"lista incompleta: quedan {len(lista) - malos} de los {pedida} elementos que se piden"

    if not salida or (es_lista and total and quitadas / total > 2 / 3):
        return None, f"{quitadas} de {total} palabras con contenido no están en los documentos"
    texto = "\n".join(salida) if es_lista else " ".join(salida)
    return texto, (f"se quitaron {quitadas} de {total} palabras sin respaldo" if quitadas else "")
