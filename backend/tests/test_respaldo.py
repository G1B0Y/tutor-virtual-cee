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


SEPARATA_INVENTARIOS = ("2. Clasificación ABC El método ABC clasifica los artículos según su participación en el valor "
                        "anual del consumo, aplicando el principio de Pareto. Los artículos A representan aproximadamente "
                        "el 80 % del valor y alrededor del 20 % de los ítems; los B, cerca del 15 % del valor; y los C, "
                        "el 5 % restante del valor pero la mayor cantidad de ítems.")


def test_cifras_que_no_estan_en_los_documentos_se_quitan():
    """Benchmark del 08/11/2026: granite inventó el 10 % y el 5 % de los ítems para los artículos B y C."""
    abc = ("La clasificación ABC de inventarios es un método que clasifica los artículos según su participación en el "
           "valor anual del consumo. Se aplica el principio de Pareto, que establece que aproximadamente el 80% del "
           "valor y el 20% de los ítems corresponden a los artículos A, el 15% del valor y el 10% de los ítems a los "
           "artículos B, y el 5% del valor y el 5% de los ítems a los artículos C.")
    texto, _ = revisar(abc, [SEPARATA_INVENTARIOS], "¿En qué consiste la clasificación ABC de inventarios?", MINIMO)
    assert texto == ("La clasificación ABC de inventarios es un método que clasifica los artículos según su "
                     "participación en el valor anual del consumo.")
    correcta = "Los artículos A representan aproximadamente el 80 % del valor y alrededor del 20 % de los ítems."
    assert revisar(correcta, [SEPARATA_INVENTARIOS], "", MINIMO) == (correcta, "")


def test_cifra_de_la_pregunta_vale():
    texto = "La Unidad 1 incluye los 8 desperdicios."
    assert revisar(texto, [TEMARIO_LEAN], DESPERDICIOS, MINIMO) == (texto, "")


def test_clasificacion_abc_correcta_pasa_con_el_fragmento_real():
    """Texto del fragmento tal como lo extrae la ingesta en la PC de Alfredo, con el encabezado que ve el modelo."""
    visto = ("[1] Separata del Módulo 3 – Gestión de Inventarios (PRUEBA), página 1. DOCUMENTO DE PRUEBA – contenido "
             "ficticio para probar el Tutor Virtual. No es información oficial del CEE. Separata del Módulo 3 – Gestión "
             "de Inventarios 1. ¿Por qué gestionar inventarios? " + SEPARATA_INVENTARIOS)
    pregunta = "¿En qué consiste la clasificación ABC de inventarios?"
    lista = ("La clasificación ABC clasifica los artículos según su participación en el valor anual del consumo, "
             "aplicando el principio de Pareto:\n1. Artículos A: aproximadamente el 80 % del valor y alrededor del 20 % "
             "de los ítems.\n2. Artículos B: cerca del 15 % del valor.\n3. Artículos C: el 5 % restante del valor pero "
             "la mayor cantidad de ítems.")
    oracion = ("La clasificación ABC de inventarios es un método que clasifica los artículos según su participación en "
               "el valor anual del consumo.")
    assert revisar(lista, [visto], pregunta, MINIMO) == (lista, "")
    assert revisar(oracion, [visto], pregunta, MINIMO) == (oracion, "")
    assert revisar(oracion, visto, pregunta, MINIMO) == (oracion, "")  # también con un solo texto


# Fragmentos reales del corpus complementario (08/11/2026): con 18 documentos el tutor dijo "no encontré" a OEE y
# PERT aunque estaban. El control partía la fórmula "(4 + 4×6 + 14) / 6" como si "14)" fuera un ítem y pedía
# "estimación pesimista" pegado, cuando el documento dice "la estimación optimista (O), la más probable (M) y la
# pesimista (P)".
OEE = ("8. Eficiencia general de los equipos (OEE) El OEE (Overall Equipment Effectiveness) mide qué parte del tiempo "
       "planificado un equipo produce piezas buenas a la velocidad ideal: OEE = disponibilidad × rendimiento × "
       "calidad.  Disponibilidad: tiempo de operación / tiempo planificado de producción.  Rendimiento: (tiempo de "
       "ciclo ideal × unidades producidas) / tiempo de operación.  Calidad: unidades buenas / unidades producidas.")
PERT = ("Estimación de tres valores: considera la estimación optimista (O), la más probable (M) y la pesimista (P). "
        "Distribución beta (PERT): duración esperada = (O + 4M + P) / 6 y desviación estándar = (P − O) / 6. "
        "Ejemplo: con O = 4 días, M = 6 días y P = 14 días, la duración PERT es (4 + 24 + 14) / 6 = 7 días.")


def test_lista_con_formulas_y_comentario_en_otra_linea_pasa():
    respuesta = ("Para calcular la duración PERT:\n1. Estimación optimista (O): 4 días\n"
                 "2. Estimación más probable (M): 6 días\n3. Estimación pesimista (P): 14 días\n"
                 "Duración esperada = (4 + 4×6 + 14) / 6 = 7 días.")
    texto, motivo = revisar(respuesta, [PERT], "¿Cómo se calcula la duración PERT?")
    assert texto is not None and "3. Estimación pesimista (P): 14 días" in texto
    assert "Duración esperada" in texto


def test_elementos_con_igual_y_aclaracion_entre_parentesis_pasan():
    con_igual = ("- Disponibilidad = tiempo de operación / tiempo planificado de producción\n"
                 "- Rendimiento = (tiempo de ciclo ideal × unidades producidas) / tiempo de operación\n"
                 "- Calidad = unidades buenas / unidades producidas")
    texto, _ = revisar(con_igual, [OEE], "¿Cómo se calcula el OEE?")
    assert texto == con_igual
    con_ingles = ("El OEE es disponibilidad × rendimiento × calidad.\n1. Disponibilidad (Availability): tiempo de "
                  "operación / tiempo planificado de producción\n2. Rendimiento (Performance): (tiempo de ciclo ideal "
                  "× unidades producidas) / tiempo de operación\n3. Calidad (Quality): unidades buenas / unidades "
                  "producidas")
    texto, _ = revisar(con_ingles, [OEE], "¿Cómo se calcula el OEE?")
    assert texto is not None and texto.count("\n") == 3


def test_lista_inventada_con_formulas_sigue_descartada():
    inventada = ("1. Productividad (P): piezas por hora\n2. Eficiencia energética: kWh por pieza\n"
                 "3. Tasa de rechazo: (piezas malas / piezas totales) - 1")
    assert revisar(inventada, [OEE], "¿Cómo se calcula el OEE?")[0] is None
