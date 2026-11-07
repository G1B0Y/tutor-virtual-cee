"""Mensajes que no se responden con los documentos y tienen una respuesta fija, sin buscar ni usar el modelo.

1. Saludos, agradecimientos y preguntas sobre el propio tutor ("¿en qué me puedes ayudar?").
2. Datos del alumno que están en el Campus y no en los documentos ("¿qué cursos llevo?", "mi nota",
   "¿qué me falta entregar?"): se le indica dónde verlos. El tutor no guarda ni lee datos personales
   (Ley 29733). Cuando el plugin del Campus pase los cursos del alumno, "¿qué cursos llevo?" se podrá
   responder con ellos.

No están en los documentos ni en las FAQs: sin esto el tutor se abstenía y las dejaba como consulta
pendiente para el CEE (lo encontró Alfredo el 07/11/2026). Se responden con un texto fijo, sin buscar
ni llamar al modelo. Los saludos cuentan solo si el mensaje entero es eso: "hola, ¿cuántas horas dura
el curso?" sigue el camino normal. Los datos del alumno se buscan como frases dentro del mensaje, pero
solo frases en primera persona sobre su propia situación: "Si mi nota final está entre 11 y 13, ¿qué
puedo hacer?" es del reglamento y sigue al buscador.
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

CAMPUS_CURSOS = (
    "Tus cursos aparecen en el Campus Virtual, en «Mis cursos». Si quieres, pregúntame por el temario, "
    "los módulos o las separatas de cualquiera de ellos."
)
CAMPUS_NOTAS = (
    "Tus notas y tu asistencia las ves en el Campus Virtual, en la sección «Calificaciones» de cada curso. "
    "Yo no tengo acceso a tus datos personales. Si algo no cuadra, consulta con la coordinación académica del CEE."
)
CAMPUS_ENTREGAS = (
    "Tus tareas y fechas de entrega aparecen en el Campus Virtual, en la «Línea de tiempo» o en el calendario "
    "del curso. Yo no tengo acceso a tus entregas. Si quieres, te explico un tema del temario o de las separatas."
)
CAMPUS_PAGOS = (
    "No tengo acceso a tus pagos ni a tu estado de cuenta. Consulta con la coordinación académica del CEE."
)

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


_DATOS_DEL_ALUMNO = [
    (re.compile(r"\b(que|cuales|cuantos) (son )?(los )?cursos (llevo|estoy llevando|tengo|curso|estoy cursando)\b"
                r"|\ben que cursos (estoy|me matricule|me inscribi)\b|\bmis cursos\b"
                r"|\bcursos en los que estoy (matriculado|inscrito)\b"), CAMPUS_CURSOS),
    (re.compile(r"\b(cual|cuanto) (es|fue|seria) mi (nota|promedio|calificacion)\b|\bmis (notas|calificaciones)\b"
                r"|\bcuanto (me )?saque\b|\bque (nota )?(me )?saque\b|\bya (salio|salieron) (mi|mis) (nota|notas)\b"
                r"|\bcomo voy en\b|\bvoy aprobando\b|\b(estoy|voy) desaprobado\b"
                r"|\bcuantas (faltas|inasistencias) (tengo|llevo)\b|\bmi (porcentaje de )?asistencia\b"), CAMPUS_NOTAS),
    (re.compile(r"\bque me falta (entregar|presentar|hacer)\b|\bmis (tareas|entregas|trabajos|pendientes)\b"
                r"|\btengo (tareas|entregas|trabajos) pendientes\b|\bcuando (vence|se entrega) mi\b"), CAMPUS_ENTREGAS),
    (re.compile(r"\bcuanto (debo|le debo)\b|\bmi (deuda|pago|pagos|estado de cuenta)\b|\bmis (pagos|deudas|cuotas)\b"
                r"|\btengo (deuda|deudas|cuotas pendientes)\b"), CAMPUS_PAGOS),
]


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9ñ]+", " ", sin_tildes).split())


def respuesta_de_conversacion(pregunta: str) -> str | None:
    """Texto fijo para saludos, gracias, despedidas, preguntas sobre el tutor o sobre datos del alumno."""
    texto = _normalizar(pregunta)
    for patron, respuesta in _REGLAS:
        if patron.fullmatch(texto):
            return respuesta
    for patron, respuesta in _DATOS_DEL_ALUMNO:
        if patron.search(texto):
            return respuesta
    return None
