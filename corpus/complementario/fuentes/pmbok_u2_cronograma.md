# Gestión de Proyectos con el PMBOK – Unidad 2: Gestión del cronograma

## 1. Del alcance al cronograma
La gestión del cronograma busca que el proyecto termine a tiempo. Parte de los paquetes de trabajo de la EDT y sigue estos pasos:
1. **Planificar la gestión del cronograma:** definir la metodología, la herramienta, las unidades de medida y los umbrales de control.
2. **Definir las actividades:** descomponer cada paquete de trabajo en actividades concretas. Resultado: la lista de actividades, sus atributos y la lista de hitos. Un **hito** es un punto o evento significativo del proyecto con duración cero, como "contrato firmado".
3. **Secuenciar las actividades:** establecer las dependencias entre ellas.
4. **Estimar las duraciones.**
5. **Desarrollar el cronograma:** calcular fechas, ruta crítica y holguras, y aprobar la línea base del cronograma.
6. **Controlar el cronograma:** comparar el avance real con la línea base y gestionar los cambios.

## 2. Secuenciación: método de diagramación por precedencia (PDM)
En el PDM las actividades son nodos y las flechas indican dependencias. Hay cuatro tipos de relación lógica: final a inicio, inicio a inicio, final a final e inicio a final.
- **Final a inicio (FI o FS):** la sucesora no puede empezar hasta que termine la predecesora. Es la más común. Ejemplo: no se puede pintar una pared hasta terminar de construirla.
- **Inicio a inicio (II o SS):** la sucesora no puede empezar hasta que empiece la predecesora.
- **Final a final (FF):** la sucesora no puede terminar hasta que termine la predecesora.
- **Inicio a final (IF o SF):** la sucesora no puede terminar hasta que empiece la predecesora; es la menos usada.
Tipos de dependencias según su origen: **obligatorias** (por la naturaleza del trabajo o por contrato), **discrecionales** (preferencias o buenas prácticas), **externas** (dependen de terceros, como un permiso municipal) e **internas** (dentro del control del equipo).
- **Adelanto (lead):** cuánto se puede adelantar la sucesora respecto de la predecesora.
- **Retraso (lag):** espera obligatoria entre dos actividades, como el fraguado del concreto.

## 3. Estimación de duraciones
- **Juicio de expertos.**
- **Estimación análoga:** usa la duración de un proyecto o actividad similar; es rápida pero poco precisa.
- **Estimación paramétrica:** usa una relación estadística. Ejemplo: si se instalan 50 metros de cable por hora, 400 metros toman 8 horas.
- **Estimación de tres valores:** considera la estimación optimista (O), la más probable (M) y la pesimista (P).
  - Distribución beta (PERT): duración esperada = (O + 4M + P) / 6 y desviación estándar = (P − O) / 6.
  - Distribución triangular: duración esperada = (O + M + P) / 3.
  - Ejemplo: con O = 4 días, M = 6 días y P = 14 días, la duración PERT es (4 + 24 + 14) / 6 = 7 días, con una desviación estándar de (14 − 4) / 6 ≈ 1,67 días. La triangular da (4 + 6 + 14) / 3 = 8 días.
- **Estimación ascendente:** se estiman los componentes de menor nivel y se suman.
- **Análisis de reservas:** se agrega una reserva de contingencia para los riesgos identificados.
- **Estimación ágil:** con puntos de historia y la velocidad del equipo (puntos completados por iteración).

## 4. Método de la ruta crítica (CPM)
La **ruta crítica** es la secuencia de actividades más larga del proyecto; determina la duración mínima del proyecto. Sus actividades tienen holgura total cero (en un cronograma sin restricciones de fecha): si cualquiera se atrasa, se atrasa todo el proyecto.
### 4.1 Cálculos
- **Pase hacia adelante:** se calculan el inicio temprano (IT o ES) y el final temprano (FT o EF) de cada actividad. FT = IT + duración. El IT de una actividad es el mayor FT de sus predecesoras.
- **Pase hacia atrás:** se calculan el final tardío (FTa o LF) y el inicio tardío (ITa o LS). ITa = FTa − duración. El FTa de una actividad es el menor ITa de sus sucesoras.
- **Holgura total:** cuánto se puede retrasar una actividad sin retrasar el fin del proyecto. Holgura total = ITa − IT = FTa − FT.
- **Holgura libre:** cuánto se puede retrasar una actividad sin retrasar el inicio temprano de ninguna sucesora. Holgura libre = menor IT de las sucesoras − FT de la actividad.
### 4.2 Ejemplo resuelto
Actividades (duración en días y predecesoras): A (3, ninguna), B (4, A), C (2, A), D (5, B), E (3, C) y F (2, D y E).
Pase hacia adelante (empezando en el día 0):
- A: IT 0, FT 3.
- B: IT 3, FT 7.
- C: IT 3, FT 5.
- D: IT 7, FT 12.
- E: IT 5, FT 8.
- F: IT 12 (el mayor entre 12 y 8), FT 14.
La duración del proyecto es 14 días.
Pase hacia atrás (empezando con FTa de F = 14):
- F: FTa 14, ITa 12.
- D: FTa 12, ITa 7.
- E: FTa 12, ITa 9.
- B: FTa 7, ITa 3.
- C: FTa 9, ITa 7.
- A: FTa 3 (el menor entre 3 y 7), ITa 0.
Holguras totales: A = 0, B = 0, C = 4, D = 0, E = 4 y F = 0. La **ruta crítica es A – B – D – F**, con 3 + 4 + 5 + 2 = 14 días. La otra ruta, A – C – E – F, dura 10 días. La holgura libre de C es 0 (E empieza apenas termina C) y la de E es 4.

## 5. Compresión del cronograma
Cuando hay que acortar el proyecto sin reducir el alcance:
- **Intensificación (crashing):** agregar recursos a actividades de la ruta crítica (horas extra, más personal, equipos adicionales). Aumenta el costo; se empieza por la actividad crítica con el menor costo por día ahorrado.
- **Ejecución rápida (fast tracking):** hacer en paralelo, total o parcialmente, actividades que normalmente se harían en secuencia. No suele aumentar el costo directo pero aumenta el riesgo y el reproceso.
Ejemplo: en el proyecto anterior, si acortar B un día cuesta S/ 500 y acortar D un día cuesta S/ 800, conviene intensificar B: el proyecto pasa a 13 días y la ruta crítica sigue siendo A – B – D – F, porque la otra ruta dura 10 días.
Al acortar la ruta crítica, otra ruta puede volverse crítica; hay que recalcular después de cada cambio.

## 6. Otras técnicas
- **Diagrama de Gantt:** barras horizontales sobre un calendario que muestran el inicio, la duración y el final de cada actividad; es la forma más usada de presentar el cronograma.
- **Cronograma de hitos:** solo las fechas de los hitos; útil para la dirección.
- **Nivelación de recursos:** ajustar las fechas para que la demanda de recursos no supere la disponibilidad; puede alargar la ruta crítica.
- **Suavizado de recursos:** ajustar actividades solo dentro de su holgura, sin cambiar la fecha de fin.
- **Método de la cadena crítica:** considera la disponibilidad de recursos y agrupa la contingencia en amortiguadores (buffers) del proyecto y de alimentación.
- **Planificación gradual (rolling wave):** el trabajo cercano se planifica en detalle y el lejano a alto nivel.
- **Enfoques ágiles:** el trabajo se organiza en iteraciones (sprints) de duración fija, normalmente de una a cuatro semanas, y el avance se sigue con diagramas de trabajo pendiente (burndown) o de trabajo completado (burnup).

## 7. Control del cronograma
Se compara el avance real con la línea base del cronograma, se analizan las variaciones y se toman acciones correctivas o preventivas. Con el método del valor ganado (Unidad 3), la variación del cronograma es SV = EV − PV y el índice de desempeño del cronograma es SPI = EV / PV: un SPI menor que 1 indica atraso.

## Fuentes
- PMI. A Guide to the Project Management Body of Knowledge (PMBOK® Guide), 6.ª ed. (2017), capítulo 6 "Gestión del cronograma del proyecto", y 8.ª ed. (2025), dominio de cronograma.
- PMI. Practice Standard for Scheduling. 3.ª ed., 2019.
- Kerzner, H. Project Management: A Systems Approach to Planning, Scheduling, and Controlling. Wiley (13.ª ed., 2022).
- Kelley, J. E. y Walker, M. R. "Critical-Path Planning and Scheduling". Proceedings of the Eastern Joint Computer Conference, 1959.
- Goldratt, E. M. Critical Chain. North River Press, 1997.
- Schwaber, K. y Sutherland, J. The Scrum Guide. 2020 (scrumguides.org).
