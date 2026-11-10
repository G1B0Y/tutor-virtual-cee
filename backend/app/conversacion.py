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
# Cierres de la conversación (demo 10/11/2026: "gracias, ya no te necesito" quedó como consulta pendiente).
_CIERRE = (r"(ya no te necesito|ya no necesito nada( mas)?|no necesito nada mas|eso (es|seria|era) todo|es todo"
           r"|nada mas|ya (esta|entendi|quedo claro)|entendido|me (sirvio|ayudaste)( mucho)?|de acuerdo)")
_OK = r"(ok|okey|vale|listo|perfecto|genial|excelente|super|bien)"

_REGLAS = [
    (re.compile(rf"({_SALUDO} )?({_TUTOR} )?{_AYUDA}( {_TUTOR})?"), PRESENTACION),
    (re.compile(rf"{_SALUDO}( {_SALUDO})?( {_TUTOR})?"), PRESENTACION),
    (re.compile(rf"{_GRACIAS}( {_TUTOR})?"), GRACIAS),
    (re.compile(rf"({_GRACIAS} )?{_DESPEDIDA}( {_TUTOR})?"), DESPEDIDA),
    # "gracias ya no te necesito", "eso es todo gracias chau", "entendido gracias": solo piezas de cierre.
    (re.compile(rf"(({_GRACIAS}|{_DESPEDIDA}|{_TUTOR}|{_OK}) )*{_CIERRE}( ({_GRACIAS}|{_CIERRE}|{_DESPEDIDA}|{_TUTOR}))*"),
     DESPEDIDA),
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


# --- Tolerancia a faltas de ortografía ("que curos llebo?", 08/11/2026) -----------------------------------
# Cada palabra del alumno que no está en el vocabulario de las reglas se cambia por la palabra del vocabulario
# que suena igual (b/v, s/c/z, ll/y, h muda, qu/k…) o que está a 1 letra (2 si es larga). Así las reglas siguen
# escritas en buen español.

_FONETICA = [
    (r"h", ""), (r"v", "b"), (r"w", "u"), (r"ll", "y"), (r"qu", "k"), (r"c([ei])", r"s\1"), (r"z", "s"),
    (r"c", "k"), (r"x", "ks"), (r"g([ei])", r"j\1"), (r"(.)\1", r"\1"),
]


def _sonido(palabra: str) -> str:
    for patron, reemplazo in _FONETICA:
        palabra = re.sub(patron, reemplazo, palabra)
    return palabra


def _distancia(a: str, b: str, tope: int) -> int:
    """Levenshtein con corte: devuelve tope + 1 si se pasa."""
    if abs(len(a) - len(b)) > tope:
        return tope + 1
    fila = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        anterior, fila[0] = fila[0], i
        for j, cb in enumerate(b, 1):
            anterior, fila[j] = fila[j], min(fila[j] + 1, fila[j - 1] + 1, anterior + (ca != cb))
        if min(fila) > tope:
            return tope + 1
    return fila[-1]


def _vocabulario(patrones: list[re.Pattern]) -> dict[str, str]:
    """Palabras de las reglas (sonido → palabra). Las de 1–2 letras no se corrigen."""
    palabras = set()
    for patron in patrones:
        palabras.update(re.findall(r"[a-zñ]{3,}", re.sub(r"\\[a-z]", " ", patron.pattern)))
    return {_sonido(p): p for p in sorted(palabras)}


# Abreviaturas de chat y palabras cortas que se escriben mal seguido.
_ABREVIATURAS = {"q": "que", "k": "que", "ke": "que", "qe": "que", "xq": "porque", "pq": "porque", "x": "por",
                 "ola": "hola", "tng": "tengo", "tb": "tambien", "pls": "por favor", "grax": "gracias", "thx": "gracias"}
# Palabras correctas comunes que quedan a 1 letra de una del vocabulario y no se deben "corregir"
# ("esta" no es "hasta", "cuesta" no es "cuenta").
_NO_CORREGIR = {"esta", "estas", "este", "esto", "estan", "cuesta", "cuestan", "matricula", "nota", "notas", "modo",
                "todo", "toda", "todos", "otra", "otro", "como", "cosa", "pasa", "paso", "casa", "caso", "dice",
                "ayer", "hoy", "mas", "menos", "tema", "temas", "cuento", "cuantas", "cuantos", "sale", "salen",
                "llega", "debe", "deben", "pago", "puede", "pueden", "hace", "hacen", "vence", "dura", "duran",
                "curso", "cursos", "clase", "clases", "pide", "piden", "nivel"}


def _corregir(texto: str, vocabulario: dict[str, str]) -> str:
    conocidas = set(vocabulario.values())
    corregidas = []
    for palabra in texto.split():
        palabra = _ABREVIATURAS.get(palabra, palabra)
        if palabra in conocidas or palabra in _NO_CORREGIR or len(palabra) < 4:
            corregidas.append(palabra)
            continue
        sonido = _sonido(palabra)
        if sonido in vocabulario:
            corregidas.append(vocabulario[sonido])
            continue
        tope = 1 if len(palabra) < 7 else 2
        candidatas = [(d, p) for s, p in vocabulario.items() if len(p) >= 4 and (d := _distancia(sonido, s, tope)) <= tope]
        corregidas.append(min(candidatas)[1] if candidatas else palabra)
    return " ".join(" ".join(corregidas).split())


_VOCABULARIO = _vocabulario([p for p, _ in _REGLAS + _DATOS_DEL_ALUMNO])


# Comentarios de agradecimiento con otras palabras ("bueno, la verdad me ha servido de ayuda", "muy útil, gracias"):
# sin signo de pregunta y, quitando el elogio, solo quedan palabras de relleno (demo 10/11/2026).
_ELOGIO = re.compile(
    r"\b(muchas |mil )?gracias\b|\bme (ha |has )?(servido|sirvio|ayudado|ayudaste|ayudo)\b"
    r"|\b(muy|super|bastante|re) (util|utiles|bueno|buena|claro|clara|amable)\b"
    r"|\b(buen|buena|excelente|gran|genial) (trabajo|bot|tutor|respuesta|explicacion|ayuda)\b"
    r"|\b(me gusto|me encanto)\b|\b(util|genial|excelente|perfecto|chevere|bacan)\b|\blo maximo\b"
)
_RELLENO = set(
    "bueno buena la verdad muy mucho bastante ok okey vale si tutor bot de ayuda todo por el lo me has ha te eres es "
    "fue y que tu tus respuestas respuesta explicacion bien super listo pues oye amigo profe en serio un una".split()
)


def _es_comentario(pregunta: str) -> bool:
    if "?" in pregunta:
        return False
    texto = _normalizar(pregunta)
    if not _ELOGIO.search(texto) or len(texto.split()) > 15:
        return False
    return all(p in _RELLENO for p in _ELOGIO.sub(" ", texto).split())


def respuesta_de_conversacion(pregunta: str) -> str | None:
    """Texto fijo para saludos, gracias, despedidas, preguntas sobre el tutor o sobre datos del alumno."""
    texto = _corregir(_normalizar(pregunta), _VOCABULARIO)
    for patron, respuesta in _REGLAS:
        if patron.fullmatch(texto):
            return respuesta
    for patron, respuesta in _DATOS_DEL_ALUMNO:
        if patron.search(texto):
            return respuesta
    if _es_comentario(pregunta):
        return GRACIAS
    return None
