"""Control de respaldo: ¿la respuesta del modelo sale de los documentos que se le dieron?

granite3.3:2b a veces no se abstiene cuando el documento solo nombra un tema: a "¿cuáles son los 8 desperdicios?"
(el temario dice "los 8 desperdicios" sin listarlos) respondió una lista inventada (08/11/2026). Este control no
depende del modelo: cuenta qué parte de las palabras con contenido de la respuesta aparece en los fragmentos o en
la pregunta. Si es poca, la respuesta se descarta y el tutor se abstiene.

La cuenta global no basta con las listas: la segunda lista inventada ("1. Exceso de producción… 2. Exceso de
transporte…") usaba palabras del mismo tema que sí están en la separata (producción, defectos, calidad, Pareto).
Por eso las enumeraciones se revisan ítem por ítem (`lista_sin_respaldo`).
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
    """.split())


def _raices(texto: str) -> set[str]:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))
    palabras = re.findall(r"[a-zñ]{4,}", sin_tildes)
    return {p[:5] for p in palabras if p not in _VACIAS}


def respaldo(respuesta: str, fragmentos: list[str], pregunta: str = "") -> float:
    """Fracción (0–1) de las raíces de la respuesta que están en los fragmentos o en la pregunta.
    Raíz = primeras 5 letras, para aceptar plurales y conjugaciones ("desperdicios" ~ "desperdicio")."""
    propias = _raices(respuesta)
    if not propias:
        return 1.0
    fuente = _raices(" ".join(fragmentos) + " " + pregunta)
    return len(propias & fuente) / len(propias)


_ITEM = re.compile(r"(?:^|\s)(?:\d{1,2}[.)]|[-•*])\s+")


def items(respuesta: str) -> list[str]:
    """Ítems de una enumeración ("1. …  2. …" o "- …"), aunque vengan en una sola línea."""
    partes = _ITEM.split(respuesta)
    return [p.strip() for p in partes[1:] if p.strip()] if len(partes) > 3 else []


def lista_sin_respaldo(respuesta: str, fragmentos: list[str], pregunta: str = "", minimo: float = 0.5) -> bool:
    """True si la respuesta es una lista (3 ítems o más) y más de un tercio de sus ítems no sale de los documentos.
    Cada ítem se mide solo por su comienzo (hasta ":" o 6 palabras): ahí está el elemento de la lista; lo que
    sigue suele ser explicación."""
    fuente = _raices(" ".join(fragmentos) + " " + pregunta)
    lista = items(respuesta)
    if len(lista) < 3:
        return False
    malos = 0
    for item in lista:
        cabeza = " ".join(item.split(":")[0].split()[:6])
        propias = _raices(cabeza)
        if propias and len(propias & fuente) / len(propias) < minimo:
            malos += 1
    return malos * 3 > len(lista)
