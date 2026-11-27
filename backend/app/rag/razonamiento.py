"""Preguntas que piden razonar con el material, no solo encontrar un dato (09/11/2026).

Pedido de Alfredo: el profesor de Sistemas Integrados Empresariales va a probar el tutor con preguntas que no están
escritas tal cual en los módulos ("una pollería recibe quejas porque el pedido llegó tarde, ¿quién debe atenderlo y
por qué?"): la idea está en el documento, pero hay que aplicarla al caso, compararla o sacar la consecuencia.

Con esas preguntas el tutor:
- busca con más fragmentos y un margen más amplio (una respuesta razonada suele juntar ideas de dos módulos),
- le pide al modelo que dé la conclusión y la razone solo con los conceptos de los documentos (regla 14 del prompt),
- revisa la respuesta con un mínimo de respaldo algo menor, porque la respuesta usa palabras del caso de la pregunta
  y conectores del razonamiento. Las cifras y las listas inventadas se siguen quitando igual.

Se reconoce por frases típicas, sin modelo: es rápido y predecible. Una pregunta de razonamiento que no se reconozca
sigue el camino normal (más estricto): el riesgo es que se abstenga, no que invente.
"""

import re
import unicodedata

_PATRONES = re.compile(
    r"\bpor ?que\b(?! (se llama|significa))"           # "¿por qué…?" (no "¿por qué se llama…?")
    r"|\bpara que (sirve|serviria|le sirve)\b.*\b(si|cuando|en)\b"
    r"|\bque (pasaria|pasa|sucederia|sucede|ocurriria|ocurre) (si|cuando)\b"
    r"|\bsi (una|un|la|el|mi|tu|su) (empresa|cliente|vendedor|negocio|tienda|marca|consumidor|area|banco|"
    r"restaurante|polleria|universidad|gerente|jefe|supervisor)\b"
    r"|\b(supongamos|supon|imagina|imaginemos|en el caso de|en un caso|caso practico|por ejemplo si)\b"
    r"|\b(como|donde|cuando) (aplicarias|aplicaria|aplico|se aplica|aplicamos|usarias|usaria)\b"
    r"|\b(deberia|deberian|debe|deben|conviene|convendria|seria mejor|es mejor|es recomendable|recomiendas|"
    r"recomendarias|harias|haria)\b.*\?"
    r"|\b(es correcto|es cierto|es verdad|estas de acuerdo|tiene sentido|es valido)\b"
    r"|\b(compara|comparar|comparacion|diferencia|diferencias|se diferencia|semejanza|en comun|relacion|"
    r"se relaciona|relacionan|vinculo|vincula)\b"
    r"|\bque (area|estrategia|herramienta|tipo de cliente|tipo de empresa|etapa|fase|documento|error|riesgo)\b"
    r"|\b(a quien|quien) (le )?(corresponde|debe|deberia)\b"
    r"|\b(justifica|justificar|argumenta|analiza|analizar|explica por que|deduce|concluye|concluir|evalua)\b"
)


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))
    return " ".join(sin_tildes.replace("¿", " ").replace("¡", " ").split())


def es_razonamiento(pregunta: str) -> bool:
    """La pregunta pide aplicar, comparar, justificar o sacar una consecuencia de lo que dicen los documentos."""
    texto = _normalizar(pregunta)
    if not texto.endswith("?"):
        texto += " ?"  # "deberia … ?" sin signo final también cuenta
    return bool(_PATRONES.search(texto))
