"""Control de respaldo con respuestas reales de granite3.3:2b en la PC de Alfredo (08/11/2026).

Regla: el tutor no dice nada que no esté en los documentos cargados.
"""

from app.config import Configuracion
from app.rag.respaldo import items, respaldo, revisar

TEMARIO_LEAN = ("Unidad 1 – Pensamiento Lean: los 8 desperdicios, mapa de flujo de valor (VSM) y 5S. Unidad 2 – "
                "Metodología DMAIC: definir, medir, analizar, mejorar y controlar. Unidad 3 – Herramientas estadísticas: "
                "capacidad de proceso (Cp y Cpk), diagramas de Pareto, Ishikawa y gráficos de control.")
TITULO_LEAN = "Temario – Lean Six Sigma Green Belt"
TEMARIO_PMBOK = ("Unidad 1 – Alcance: acta de constitución, requisitos y estructura de desglose del trabajo (EDT o WBS). "
                 "Unidad 2 – Cronograma: secuencia de actividades, método de la ruta crítica (CPM) y diagrama de Gantt.")
SEPARATA_U3 = ("El diagrama de Pareto ordena las causas de un problema de mayor a menor frecuencia. Ayuda a concentrar el "
               "esfuerzo en las pocas causas vitales que suelen explicar cerca del 80 % de los defectos. El diagrama de "
               "Ishikawa organiza las posibles causas de un problema en seis categorías conocidas como las 6M: método, "
               "mano de obra, máquina, material, medición y medio ambiente. La capacidad de proceso indica si un proceso "
               "cumple las especificaciones del cliente.")
CADENA = ("El inventario de seguridad protege a la empresa de la variabilidad de la demanda y del tiempo de espera del "
          "proveedor. Los productos con defectos generan costos de transporte y de movimiento adicionales.")
MINIMO = Configuracion().minimo_respaldo
DESPERDICIOS = "cuales son los 8 desperdicios"

# Tres listas distintas que granite inventó para la misma pregunta (el temario solo nombra "los 8 desperdicios").
INVENTADA = ("Los 8 desperdicios son conceptos clave en el Lean Manufacturing y se enumeran de la siguiente manera: "
             "1. Producción excesiva: producir más de lo necesario. 2. Fugas: Flujo de materiales o información "
             "innecesario. 3. Movimientos innecesarios de personas. 4. Tiempo de espera entre procesos. 5. Procesos "
             "innecesarios. 6. Materiales defectuosos. 7. Movimientos incorrectos. 8. Procesos ineficientes.")
INVENTADA_2 = ("Los 8 desperdicios son conceptos clave del Lean Manufacturing, mencionados en la separata de la Unidad 3: "
               "1. Exceso de producción: producir más de lo necesario. 2. Exceso de procesamiento: pasos que no agregan "
               "valor. 3. Exceso de transporte: mover materiales. 4. Esperar: tiempos muertos. 5. Producción de defectos: "
               "errores. 6. Movimientos innecesarios: del personal. 7. Producción de exceso de calidad. 8. Calidad "
               "defectuosa. Estos desperdicios se representan en un diagrama de Pareto.")
# Usa palabras que sí están en otros documentos (inventario, defectos, tiempo de espera, transporte).
INVENTADA_3 = ("Según el temario, los 8 desperdicios son: 1. Sobreproducción 2. Inventario 3. Defectos 4. Tiempo de "
               "espera 5. Transporte 6. Movimiento 7. Sobreprocesamiento 8. Talento no utilizado.")


def test_listas_inventadas_se_descartan():
    fuentes = [SEPARATA_U3, f"{TITULO_LEAN}. {TEMARIO_LEAN}", CADENA]
    for inventada in (INVENTADA, INVENTADA_2, INVENTADA_3):
        texto, motivo = revisar(inventada, fuentes, DESPERDICIOS, MINIMO)
        assert texto is None, inventada[:60]
        assert "no están en los documentos" in motivo


def test_dmaic_quita_las_explicaciones_propias_y_deja_los_elementos():
    """Falso rechazo del benchmark del 08/11/2026 (respaldo global 0,31 con el piso en 0.4)."""
    dmaic = ("Las siglas DMAIC significan: - Definir: Identificar el problema o la oportunidad de mejora. - Medir: "
             "Recopilar datos relevantes para entender el problema. - Analizar: Analizar los datos para identificar "
             "causas raíz. - Mejorar: Desarrollar soluciones para abordar las causas identificadas. - Control: "
             "Implementar medidas para asegurar que las soluciones se mantengan y que el problema no vuelva a ocurrir.")
    texto, _ = revisar(dmaic, [TEMARIO_LEAN], "¿Qué significan las siglas DMAIC?", MINIMO)
    assert texto == "Las siglas DMAIC significan:\n- Definir\n- Medir\n- Analizar\n- Mejorar\n- Control"


def test_comentario_propio_despues_de_la_lista_se_quita():
    dmaic = ("Las siglas DMAIC significan: - D: Definir - M: Medir - A: Analizar - I: Mejorar - C: Controlar. Estas son "
             "las etapas de la metodología DMAIC que se aplican en las empresas modernas de todo el mundo.")
    texto, _ = revisar(dmaic, [TEMARIO_LEAN], "¿Qué significan las siglas DMAIC?", MINIMO)
    assert texto is not None and texto.endswith("C: Controlar.")
    assert "empresas" not in texto


def test_frase_propia_en_prosa_se_quita():
    cronograma = ("Tema dos: Cronograma. Se trata de la secuencia de actividades, el método de la ruta crítica (CPM) y "
                  "el diagrama de Gantt. Esto incluye la planificación y organización de las tareas del proyecto, "
                  "determinando los plazos y las relaciones entre las actividades.")
    texto, motivo = revisar(cronograma, [TEMARIO_PMBOK], "¿y el tema dos?", MINIMO)
    assert texto == ("Tema dos: Cronograma. Se trata de la secuencia de actividades, el método de la ruta crítica (CPM) "
                     "y el diagrama de Gantt.")
    assert motivo.startswith("se quitaron")


def test_respuestas_correctas_quedan_igual():
    casos = [
        ("El primer tema del curso Lean Six Sigma Green Belt es Pensamiento Lean: los 8 desperdicios, mapa de flujo "
         "de valor (VSM) y 5S.", f"{TITULO_LEAN}. {TEMARIO_LEAN}", "cual es el primer tema de sixsigma"),
        ("Un VSM es un mapa de flujo de valor, del Pensamiento Lean.", TEMARIO_LEAN, "que es un VSM?"),
    ]
    for respuesta, fragmento, pregunta in casos:
        assert revisar(respuesta, [fragmento], pregunta, MINIMO) == (respuesta, "")
    seis_m = ("Las 6M del diagrama de Ishikawa son: 1. Método 2. Mano de obra 3. Máquina 4. Material 5. Medición "
              "6. Medio ambiente.")
    texto, motivo = revisar(seis_m, [SEPARATA_U3], "¿Cuáles son las 6M?", MINIMO)
    assert texto.splitlines()[2] == "2. Mano de obra" and len(texto.splitlines()) == 7 and motivo == ""
    temario = "El temario incluye: 1. Unidad 1: Alcance, acta de constitución. 2. Unidad 2: Cronograma. 3. Unidad 3: Costos."
    assert revisar(temario, [TEMARIO_PMBOK + " Unidad 3 – Costos."], "temario", MINIMO)[0] is not None


def test_respuesta_ajena_a_los_documentos_se_descarta():
    ajena = "Argentina ganó el mundial de fútbol en Qatar después de vencer a Francia en los penales."
    assert revisar(ajena, [TEMARIO_LEAN], "¿Quién ganó el mundial?", MINIMO)[0] is None


def test_respuesta_sin_palabras_de_contenido_no_se_descarta():
    assert respaldo("Sí.", [TEMARIO_LEAN]) == 1.0
    assert revisar("Sí.", [TEMARIO_LEAN], "", MINIMO) == ("Sí.", "")


def test_items_en_una_sola_linea_y_texto_sin_lista():
    assert items("Son: 1. Uno 2. Dos 3. Tres") == ["Uno", "Dos", "Tres"]
    assert items("El EOQ = √(2 × D × S / H) - es la fórmula.") == []


def test_vsm_queda_con_la_primera_oracion():
    """Benchmark del 08/11/2026 en la PC de Alfredo: se descartaba entera (13 de 24 palabras propias)."""
    vsm = ("El VSM se refiere a la herramienta de mapa de flujo de valor, que es parte del pensamiento lean. Este mapa "
           "visualiza el proceso de producción, identificando los pasos necesarios para llevar un producto o servicio "
           "desde su origen hasta su entrega al cliente, y destaca los desperdicios innecesarios.")
    texto, motivo = revisar(vsm, [f"{TITULO_LEAN}. {TEMARIO_LEAN}"], "que es un VSM?", MINIMO)
    assert texto == "El VSM se refiere a la herramienta de mapa de flujo de valor, que es parte del pensamiento lean."
    assert motivo.startswith("se quitaron")


def test_primera_oracion_sin_respaldo_se_abstiene():
    relleno = ("El Kaizen es una filosofía japonesa de mejora continua creada por Masaaki Imai. Se relaciona con el "
               "Pensamiento Lean, los 8 desperdicios y las 5S.")
    assert revisar(relleno, [TEMARIO_LEAN], "que es kaizen", MINIMO)[0] is None
