"""Saludos, agradecimientos y preguntas sobre el propio tutor ("¿en qué me puedes ayudar?").

No están en los documentos ni en las FAQs: sin esto el tutor se abstenía y las dejaba como consulta
pendiente para el CEE (lo encontró Alfredo el 07/11/2026). Se responden con un texto fijo, sin buscar
ni llamar al modelo. Solo si el mensaje entero es eso: "hola, ¿cuántas horas dura el curso?" sigue el
camino normal.
"""

import re
import unicodedata

PRESENTACION = (
    "Soy el tutor virtual del CEE. Puedo responder dudas sobre los temarios, módulos, separatas y el "
    "reglamento de tus cursos, y te indico el documento y la página de donde sale cada respuesta. "
    "Por ejemplo: «¿Cómo se calcula el inventario de seguridad?» o «¿Qué nota necesito para aprobar?». "
    "Para trámites, pagos o tus notas, te oriento al personal del CEE."
)
GRACIAS = "¡De nada! Si tienes otra duda sobre tus cursos, pregúntame."
DESPEDIDA = "¡Hasta luego! Aquí estaré si tienes otra duda sobre tus cursos."

_SALUDO = r"(hola|holi|buenas|buen dia|buenos dias|buenas tardes|buenas noches|hey|que tal|saludos)"
_TUTOR = r"(tutor|bot|profe|profesor|amigo)"
_AYUDA = (
    r"(en que (me )?(puedes|podrias|pueden) ayudar(me)?|como (me )?(puedes|podrias) ayudar(me)?"
    r"|en que me ayudas|que (puedes|sabes) hacer|que haces|para que sirves|como funcionas"
    r"|quien eres|que eres|ayuda|ayudame|necesito ayuda|que puedo preguntar(te)?|sobre que puedo preguntar(te)?)"
)
_GRACIAS = r"((ok|okey|vale|listo|perfecto|genial|excelente|super) )?(muchas |mil )?gracias( (por todo|por la ayuda))?"
_DESPEDIDA = r"(chau|chao|adios|hasta luego|hasta pronto|nos vemos|bye)"

_REGLAS = [
    (re.compile(rf"({_SALUDO} )?({_TUTOR} )?{_AYUDA}( {_TUTOR})?"), PRESENTACION),
    (re.compile(rf"{_SALUDO}( {_SALUDO})?( {_TUTOR})?"), PRESENTACION),
    (re.compile(rf"{_GRACIAS}( {_TUTOR})?"), GRACIAS),
    (re.compile(rf"({_GRACIAS} )?{_DESPEDIDA}( {_TUTOR})?"), DESPEDIDA),
]


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9ñ]+", " ", sin_tildes).split())


def respuesta_de_conversacion(pregunta: str) -> str | None:
    """Texto fijo si el mensaje es solo un saludo, un gracias, una despedida o una pregunta sobre el tutor."""
    texto = _normalizar(pregunta)
    for patron, respuesta in _REGLAS:
        if patron.fullmatch(texto):
            return respuesta
    return None
