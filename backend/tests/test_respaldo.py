"""Control de respaldo con respuestas reales de granite3.3:2b en la PC de Alfredo (08/11/2026)."""

from app.config import Configuracion
from app.rag.respaldo import respaldo

TEMARIO_LEAN = ("Unidad 1 – Pensamiento Lean: los 8 desperdicios, mapa de flujo de valor (VSM) y 5S. Unidad 2 – "
                "Metodología DMAIC: definir, medir, analizar, mejorar y controlar. Unidad 3 – Herramientas estadísticas: "
                "capacidad de proceso (Cp y Cpk), diagramas de Pareto, Ishikawa y gráficos de control.")
TEMARIO_PMBOK = ("Unidad 1 – Alcance: acta de constitución, requisitos y estructura de desglose del trabajo (EDT o WBS). "
                 "Unidad 2 – Cronograma: secuencia de actividades, método de la ruta crítica (CPM) y diagrama de Gantt.")
MINIMO = Configuracion().minimo_respaldo

INVENTADA = ("Los 8 desperdicios son conceptos clave en el Lean Manufacturing y se enumeran de la siguiente manera: "
             "1. Producción excesiva: producir más de lo necesario. 2. Fugas: Flujo de materiales o información "
             "innecesario. 3. Movimientos innecesarios de personas. 4. Tiempo de espera entre procesos. 5. Procesos "
             "innecesarios. 6. Materiales defectuosos. 7. Movimientos incorrectos. 8. Procesos ineficientes.")


def test_lista_inventada_no_tiene_respaldo():
    assert respaldo(INVENTADA, [TEMARIO_LEAN], "cuales son los 8 desperdicios") < MINIMO


def test_respuestas_correctas_tienen_respaldo():
    casos = [
        ("El primer tema del curso Lean Six Sigma Green Belt es Pensamiento Lean: los 8 desperdicios, mapa de flujo "
         "de valor (VSM) y 5S.", TEMARIO_LEAN, "cual es el primer tema de sixsigma"),
        ("Las siglas DMAIC significan: - D: Definir - M: Medir - A: Analizar - I: Mejorar - C: Controlar. Estas son "
         "las etapas de la metodología DMAIC utilizada en el curso Lean Six Sigma Green Belt.", TEMARIO_LEAN,
         "¿Qué significan las siglas DMAIC?"),
        # Con la frase propia que agrega granite: igual pasa.
        ("Tema dos: Cronograma. Se trata de la secuencia de actividades, el método de la ruta crítica (CPM) y el "
         "diagrama de Gantt. Esto incluye la planificación y organización de las tareas del proyecto, determinando "
         "los plazos y las relaciones entre las actividades.", TEMARIO_PMBOK, "¿y el tema dos?"),
    ]
    for respuesta, fragmento, pregunta in casos:
        assert respaldo(respuesta, [fragmento], pregunta) >= MINIMO, respuesta[:40]


def test_respuesta_sin_palabras_de_contenido_no_se_descarta():
    assert respaldo("Sí.", [TEMARIO_LEAN]) == 1.0
