"""Control de respaldo con respuestas reales de granite3.3:2b en la PC de Alfredo (08/11/2026)."""

from app.config import Configuracion
from app.rag.respaldo import items, lista_sin_respaldo, respaldo

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


SEPARATA_U3 = ("El diagrama de Pareto ordena las causas de un problema de mayor a menor frecuencia. Ayuda a concentrar el "
               "esfuerzo en las pocas causas vitales que suelen explicar cerca del 80 % de los defectos. El diagrama de "
               "Ishikawa organiza las posibles causas de un problema en seis categorías conocidas como las 6M: método, "
               "mano de obra, máquina, material, medición y medio ambiente. La capacidad de proceso indica si un proceso "
               "cumple las especificaciones del cliente.")
# Segunda lista inventada (81ec0c7): sus palabras sueltas sí están en la separata, por eso pasaba la cuenta global.
INVENTADA_2 = ("Los 8 desperdicios son conceptos clave del Lean Manufacturing, mencionados en la separata de la Unidad 3: "
               "1. Exceso de producción: producir más de lo necesario. 2. Exceso de procesamiento: pasos que no agregan "
               "valor. 3. Exceso de transporte: mover materiales. 4. Esperar: tiempos muertos. 5. Producción de defectos: "
               "errores. 6. Movimientos innecesarios: del personal. 7. Producción de exceso de calidad. 8. Calidad "
               "defectuosa. Estos desperdicios se representan en un diagrama de Pareto.")


def test_listas_inventadas_se_detectan_item_por_item():
    for inventada in (INVENTADA, INVENTADA_2):
        assert lista_sin_respaldo(inventada, [SEPARATA_U3, TEMARIO_LEAN], "cuales son los 8 desperdicios")


def test_listas_correctas_pasan():
    assert not lista_sin_respaldo("Las 6M del diagrama de Ishikawa son: 1. Método 2. Mano de obra 3. Máquina "
                                  "4. Material 5. Medición 6. Medio ambiente.", [SEPARATA_U3], "¿Cuáles son las 6M?")
    assert not lista_sin_respaldo("Las siglas DMAIC significan: - D: Definir - M: Medir - A: Analizar - I: Mejorar "
                                  "- C: Controlar.", [TEMARIO_LEAN], "¿Qué significa DMAIC?")
    assert not lista_sin_respaldo("El temario incluye: 1. Unidad 1: Alcance, acta de constitución. 2. Unidad 2: "
                                  "Cronograma. 3. Unidad 3: Costos.", [TEMARIO_PMBOK + " Unidad 3 – Costos."], "temario")


def test_items_en_una_sola_linea_y_texto_sin_lista():
    assert items("Son: 1. Uno 2. Dos 3. Tres") == ["Uno", "Dos", "Tres"]
    assert items("El EOQ = √(2 × D × S / H) - es la fórmula.") == []
