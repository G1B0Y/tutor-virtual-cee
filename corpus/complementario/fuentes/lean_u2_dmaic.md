# Lean Six Sigma Green Belt – Unidad 2: Six Sigma y la metodología DMAIC

## 1. ¿Qué es Six Sigma?
Six Sigma es una metodología de mejora basada en datos que busca reducir la variación de los procesos y los defectos hasta niveles muy bajos. Fue desarrollada en Motorola a mediados de la década de 1980, con Bill Smith como uno de sus impulsores, y se hizo conocida cuando General Electric la adoptó en la década de 1990 bajo la dirección de Jack Welch.
Un proceso con nivel seis sigma produce como máximo 3,4 defectos por millón de oportunidades. Esa cifra supone que, en el largo plazo, la media del proceso se desplaza 1,5 sigmas; por eso un proceso "seis sigma" equivale a 4,5 sigmas de distancia efectiva al límite de especificación.
**Lean Six Sigma** combina la eliminación de desperdicios y la mejora del flujo de Lean con la reducción de la variación y el análisis estadístico de Six Sigma.

## 2. Conceptos y métricas básicas
- **Voz del cliente (VOC):** lo que el cliente necesita y espera, obtenido de encuestas, reclamos, entrevistas o grupos focales.
- **CTQ (crítico para la calidad):** característica medible del producto o proceso que traduce una necesidad del cliente y tiene un límite de especificación.
- **Defecto:** cualquier incumplimiento de un requisito del cliente.
- **Oportunidad de defecto:** cada característica que puede fallar en una unidad.
- **DPU (defectos por unidad):** defectos / unidades.
- **DPMO (defectos por millón de oportunidades):** defectos / (unidades × oportunidades por unidad) × 1 000 000.
Ejemplo: se revisaron 500 facturas, cada una con 4 oportunidades de error (RUC, monto, fecha y descripción), y se encontraron 30 defectos. DPMO = 30 / (500 × 4) × 1 000 000 = 15 000. Eso equivale a un rendimiento de 98,5 % y a un nivel sigma de aproximadamente 3,7.
- **Rendimiento de primera pasada (FPY):** unidades buenas a la primera / unidades que entraron al paso.
- **Rendimiento acumulado (RTY, Rolled Throughput Yield):** producto de los FPY de todos los pasos; es la probabilidad de que una unidad atraviese todo el proceso sin ningún defecto.
Ejemplo: un proceso de tres pasos con FPY de 95 %, 98 % y 90 % tiene un RTY de 0,95 × 0,98 × 0,90 ≈ 83,8 %.
### 2.1 Tabla de nivel sigma (con desplazamiento de 1,5 sigmas)
- 1 sigma: 690 000 DPMO aproximadamente (31 % de rendimiento).
- 2 sigma: 308 537 DPMO (69,1 %).
- 3 sigma: 66 807 DPMO (93,3 %).
- 4 sigma: 6 210 DPMO (99,38 %).
- 5 sigma: 233 DPMO (99,977 %).
- 6 sigma: 3,4 DPMO (99,99966 %).

## 3. Roles en Six Sigma
Los roles de Six Sigma son: champion o patrocinador, dueño del proceso, Master Black Belt, Black Belt, Green Belt, Yellow Belt y White Belt.
- **Champion o patrocinador:** directivo que elige los proyectos, asigna recursos y elimina barreras.
- **Dueño del proceso:** responsable del proceso que se mejora; recibe y mantiene los resultados.
- **Master Black Belt:** experto que forma y asesora a los Black Belts y Green Belts y vela por la metodología.
- **Black Belt:** dedicado a tiempo completo a liderar proyectos complejos y a asesorar a los Green Belts.
- **Green Belt:** profesional que lidera proyectos de mejora en su área a tiempo parcial y participa en proyectos de Black Belts.
- **Yellow Belt y White Belt:** personas con formación básica que participan en los equipos de proyecto.

## 4. La metodología DMAIC
DMAIC es el ciclo de cinco fases que siguen los proyectos Six Sigma para mejorar un proceso existente: Definir (Define), Medir (Measure), Analizar (Analyze), Mejorar (Improve) y Controlar (Control). Al final de cada fase suele haber una revisión (tollgate) con el patrocinador.
### 4.1 Definir (Define)
Objetivo: dejar claro el problema, su alcance, el cliente y la meta.
- **Acta del proyecto (project charter):** caso de negocio, enunciado del problema, meta medible (por ejemplo, reducir los reclamos de 8 % a 3 % en seis meses), alcance, equipo y cronograma.
- **SIPOC:** diagrama de alto nivel del proceso con sus Proveedores (Suppliers), Entradas (Inputs), Proceso (Process), Salidas (Outputs) y Clientes (Customers).
- **Voz del cliente y árbol de CTQ.**
- **Análisis de interesados.**
### 4.2 Medir (Measure)
Objetivo: conocer el desempeño actual del proceso con datos confiables.
- **Mapa detallado del proceso.**
- **Plan de recolección de datos:** qué medir, cómo, dónde, cuándo y quién.
- **Análisis del sistema de medición (MSA):** comprobar que la medición es confiable. El estudio **Gage R&R** separa la variación debida al instrumento (repetibilidad) y a los operadores (reproducibilidad). Como referencia de AIAG, un sistema con Gage R&R menor al 10 % de la variación total es aceptable, entre 10 % y 30 % puede ser aceptable según la aplicación, y más de 30 % no es aceptable.
- **Línea base:** DPMO, nivel sigma, capacidad del proceso (Cp, Cpk) o tiempo de ciclo actuales.
### 4.3 Analizar (Analyze)
Objetivo: encontrar y comprobar con datos las causas raíz del problema.
- **Diagrama de Ishikawa** (causa y efecto) y **cinco porqués**.
- **Diagrama de Pareto** para priorizar causas.
- **Análisis del flujo de valor** para localizar esperas y desperdicios.
- **Pruebas de hipótesis** (t, ANOVA, chi cuadrado), **correlación y regresión** para confirmar qué variables de entrada (X) influyen en la salida (Y). La relación se expresa como Y = f(X).
### 4.4 Mejorar (Improve)
Objetivo: diseñar, probar e implementar soluciones a las causas raíz.
- Generación de ideas (lluvia de ideas) y matriz de selección de soluciones.
- **Diseño de experimentos (DOE)** para encontrar la mejor combinación de factores.
- **AMEF (Análisis de Modo y Efecto de Falla, FMEA):** para cada modo de falla se califican la severidad (S), la ocurrencia (O) y la detección (D) de 1 a 10; el número de prioridad de riesgo es NPR = S × O × D. Ejemplo: S = 8, O = 5 y D = 4 dan un NPR de 160. El manual AIAG-VDA de 2019 reemplazó el NPR por una prioridad de acción (alta, media o baja).
- **Prueba piloto** antes de implementar a escala completa.
- Herramientas Lean: 5S, poka-yoke, SMED, trabajo estandarizado.
### 4.5 Controlar (Control)
Objetivo: asegurar que la mejora se mantenga en el tiempo.
- **Plan de control:** qué variables se vigilan, cómo, con qué frecuencia, quién lo hace y qué se hace si se salen de control.
- **Gráficos de control estadístico (SPC)**, desarrollados en la Unidad 3.
- **Procedimientos y trabajo estandarizado actualizados**, capacitación y controles visuales.
- **Cierre del proyecto:** resultados finales, beneficios validados por finanzas, lecciones aprendidas y entrega al dueño del proceso.

## 5. DMAIC, DMADV y PDCA
- **DMAIC** mejora un proceso que ya existe.
- **DMADV** (Definir, Medir, Analizar, Diseñar, Verificar), parte del **Diseño para Six Sigma (DFSS)**, se usa para crear un proceso o producto nuevo o rediseñarlo por completo.
- **PDCA** (Planificar, Hacer, Verificar, Actuar), o ciclo de Deming, es un ciclo de mejora continua más simple que comparte la misma lógica de aprender con datos.

## Fuentes
- ASQ (American Society for Quality). "What Is Six Sigma?" y "DMAIC Process" (asq.org/quality-resources).
- Pyzdek, T. y Keller, P. The Six Sigma Handbook. McGraw-Hill (5.ª ed., 2018).
- George, M. L. y otros. The Lean Six Sigma Pocket Toolbook. McGraw-Hill, 2005.
- AIAG. Measurement Systems Analysis (MSA) Reference Manual (4.ª ed., 2010).
- AIAG y VDA. FMEA Handbook. 2019.
- Breyfogle, F. W. Implementing Six Sigma. Wiley (2.ª ed., 2003).
