"""Genera los PDFs de prueba del corpus (contenido ficticio, marcado como PRUEBA).

Uso (desde la raíz del repo):  python scripts/generar_corpus_prueba.py
Necesita reportlab (solo para generar; el tutor no lo usa):  pip install reportlab
Los PDFs quedan en corpus/prueba/. El texto de cada página está en PAGINAS para poder revisarlo.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

AVISO = "DOCUMENTO DE PRUEBA – contenido ficticio para probar el Tutor Virtual. No es información oficial del CEE."
DESTINO = Path(__file__).resolve().parent.parent / "corpus" / "prueba"

DOCUMENTOS = {
    "temario_gestion_cadena_suministro.pdf": (
        "Temario – Programa de Especialización en Gestión de la Cadena de Suministro",
        [
            [
                ("h", "Datos generales"),
                ("p", "El Programa de Especialización en Gestión de la Cadena de Suministro tiene una duración de 96 horas académicas, distribuidas en 4 módulos de 24 horas cada uno. La modalidad es virtual en vivo, con clases los martes y jueves de 7:00 p. m. a 10:00 p. m. (hora de Lima)."),
                ("p", "Está dirigido a profesionales de logística, compras, producción y operaciones que buscan mejorar la planificación y el control de la cadena de suministro en sus organizaciones."),
                ("h", "Objetivos"),
                ("p", "Al finalizar el programa, el participante será capaz de diseñar una cadena de suministro alineada a la estrategia de la empresa, aplicar técnicas de pronóstico de la demanda, gestionar inventarios con criterios de costo y nivel de servicio, y medir el desempeño logístico con indicadores clave."),
            ],
            [
                ("h", "Módulos"),
                ("p", "Módulo 1 – Fundamentos de la cadena de suministro (24 horas): diferencia entre logística y Supply Chain Management, el modelo SCOR, integración de proveedores y clientes."),
                ("p", "Módulo 2 – Pronóstico y planificación de la demanda (24 horas): promedios móviles, suavizamiento exponencial, planificación de ventas y operaciones (S&OP)."),
                ("p", "Módulo 3 – Gestión de inventarios (24 horas): clasificación ABC, inventario de seguridad, lote económico de compra (EOQ) y punto de reorden. Material de lectura: separata del módulo 3, Gestión de Inventarios."),
                ("p", "Módulo 4 – Indicadores y mejora del desempeño logístico (24 horas): nivel de servicio, rotación de inventario, costo logístico total y tablero de indicadores."),
                ("h", "Evaluación"),
                ("p", "La nota final se calcula con un trabajo aplicativo por módulo (60 %) y un proyecto final integrador (40 %). Para aprobar se requiere una nota final mínima de 14 sobre 20 y el 80 % de asistencia."),
            ],
        ],
    ),
    "separata_gestion_inventarios.pdf": (
        "Separata del Módulo 3 – Gestión de Inventarios",
        [
            [
                ("h", "1. ¿Por qué gestionar inventarios?"),
                ("p", "El inventario protege a la empresa frente a la incertidumbre de la demanda y del abastecimiento, pero inmoviliza capital y genera costos de almacenamiento, obsolescencia y mermas. Gestionar inventarios consiste en decidir cuánto pedir y cuándo pedir para equilibrar el costo total con el nivel de servicio deseado."),
                ("h", "2. Clasificación ABC"),
                ("p", "El método ABC clasifica los artículos según su participación en el valor anual del consumo, aplicando el principio de Pareto. Los artículos A representan aproximadamente el 80 % del valor y alrededor del 20 % de los ítems; los B, cerca del 15 % del valor; y los C, el 5 % restante del valor pero la mayor cantidad de ítems. Los artículos A requieren control estricto y revisión frecuente; los C, controles simples."),
                ("p", "Ejemplo: en un almacén de repuestos con 1 000 ítems, 200 ítems de alto costo (motores, tarjetas electrónicas) concentran el 80 % del valor anual y se clasifican como A."),
            ],
            [
                ("h", "3. Inventario de seguridad"),
                ("p", "El inventario de seguridad es la cantidad adicional que se mantiene para cubrir la variabilidad de la demanda durante el tiempo de reposición. Se calcula como SS = Z × σd × √L, donde Z es el factor del nivel de servicio (1,65 para un 95 %), σd es la desviación estándar de la demanda diaria y L es el tiempo de reposición en días."),
                ("p", "Ejemplo: si la desviación estándar de la demanda diaria es de 20 unidades, el tiempo de reposición es de 9 días y se desea un nivel de servicio de 95 %, el inventario de seguridad es 1,65 × 20 × 3 = 99 unidades."),
                ("h", "4. Punto de reorden"),
                ("p", "El punto de reorden indica el nivel de inventario en el que se debe emitir un nuevo pedido: ROP = demanda diaria promedio × tiempo de reposición + inventario de seguridad."),
            ],
            [
                ("h", "5. Lote económico de compra (EOQ)"),
                ("p", "El lote económico de compra es la cantidad que minimiza la suma del costo de pedir y el costo de mantener inventario. Se calcula como EOQ = √(2 × D × S / H), donde D es la demanda anual, S el costo por pedido y H el costo anual de mantener una unidad."),
                ("p", "Ejemplo: con una demanda anual de 12 000 unidades, un costo por pedido de S/ 150 y un costo de mantener de S/ 4 por unidad al año, el EOQ es √(2 × 12 000 × 150 / 4) = 949 unidades aproximadamente."),
            ],
        ],
    ),
    "temario_lean_six_sigma.pdf": (
        "Temario – Curso Lean Six Sigma Green Belt",
        [
            [
                ("h", "Datos generales"),
                ("p", "El curso Lean Six Sigma Green Belt tiene una duración de 60 horas académicas en modalidad semipresencial: sesiones virtuales los sábados de 9:00 a. m. a 1:00 p. m. y dos talleres presenciales en la FIIS-UNI. Al aprobar, el participante recibe un certificado de Green Belt emitido por el CEE FIIS-UNI."),
                ("h", "Contenido"),
                ("p", "Unidad 1 – Pensamiento Lean: los 8 desperdicios, mapa de flujo de valor (VSM) y 5S. Unidad 2 – Metodología DMAIC: definir, medir, analizar, mejorar y controlar. Unidad 3 – Herramientas estadísticas: capacidad de proceso (Cp y Cpk), diagramas de Pareto, Ishikawa y gráficos de control. Unidad 4 – Proyecto de mejora aplicado a la empresa del participante."),
                ("h", "Requisitos"),
                ("p", "Se recomienda conocimiento básico de estadística y manejo de Excel. No se requiere certificación previa en Lean ni Six Sigma."),
            ],
        ],
    ),
    "reglamento_academico_cee.pdf": (
        "Reglamento Académico de los Programas del CEE (extracto)",
        [
            [
                ("h", "Artículo 5 – Asistencia"),
                ("p", "La asistencia mínima para aprobar un curso o programa es del 80 % de las sesiones. Las inasistencias por motivos de salud se justifican presentando el certificado médico a la coordinación académica dentro de los 5 días hábiles siguientes."),
                ("h", "Artículo 8 – Calificación"),
                ("p", "La escala de calificación es vigesimal (0 a 20). La nota mínima aprobatoria es 14. El participante que obtenga una nota final entre 11 y 13 puede rendir una evaluación de recuperación por única vez."),
                ("h", "Artículo 12 – Certificación"),
                ("p", "El certificado se emite cuando el participante aprueba todos los cursos del programa y no tiene deudas pendientes. La emisión y entrega de certificados la realiza la coordinación académica; el plazo es de 30 días calendario después del cierre de notas."),
            ],
        ],
    ),
}


def generar() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    estilos = getSampleStyleSheet()
    aviso = ParagraphStyle("aviso", parent=estilos["Normal"], fontSize=8, textColor="#870c0e")
    for archivo, (titulo, paginas) in DOCUMENTOS.items():
        doc = SimpleDocTemplate(str(DESTINO / archivo), pagesize=A4, title=titulo, author="CEE FIIS-UNI (PRUEBA)",
                                leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
        historia = []
        for n, pagina in enumerate(paginas):
            if n:
                historia.append(PageBreak())
            historia += [Paragraph(AVISO, aviso), Spacer(1, 6)]
            if n == 0:
                historia += [Paragraph(titulo, estilos["Title"]), Spacer(1, 6)]
            for tipo, texto in pagina:
                historia.append(Paragraph(texto, estilos["Heading3" if tipo == "h" else "BodyText"]))
        doc.build(historia)
        print("Generado:", archivo)


if __name__ == "__main__":
    generar()
