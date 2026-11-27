# Lean Six Sigma Green Belt – Unidad 3: Herramientas estadísticas y control estadístico de procesos

## 1. Estadística descriptiva
- **Media (μ o x̄):** promedio de los datos; indica dónde está centrado el proceso.
- **Mediana:** valor central de los datos ordenados; es menos sensible a valores extremos que la media.
- **Moda:** valor que más se repite.
- **Rango (R):** valor máximo menos valor mínimo.
- **Desviación estándar (σ o s):** medida de cuánto se dispersan los datos alrededor de la media. La varianza es el cuadrado de la desviación estándar.
Los datos pueden ser **continuos** (se miden: peso, tiempo, temperatura) o **discretos o de atributos** (se cuentan: número de defectos, conforme o no conforme).

## 2. Distribución normal
Muchas características de procesos siguen una distribución normal, con forma de campana y simétrica alrededor de la media. Regla empírica:
- Entre μ − 1σ y μ + 1σ está aproximadamente el 68,27 % de los datos.
- Entre μ − 2σ y μ + 2σ, el 95,45 %.
- Entre μ − 3σ y μ + 3σ, el 99,73 %.
El valor Z = (x − μ) / σ indica a cuántas desviaciones estándar está un valor de la media y permite calcular probabilidades con la tabla normal estándar.

## 3. Las siete herramientas básicas de la calidad
Kaoru Ishikawa propuso un conjunto de siete herramientas sencillas que permiten resolver la mayoría de los problemas de calidad: hoja de verificación, histograma, diagrama de Pareto, diagrama de causa y efecto (Ishikawa), diagrama de dispersión, gráfico de control y estratificación.
1. **Hoja de verificación:** formato para registrar datos en el lugar donde ocurren, de manera ordenada y rápida.
2. **Histograma:** gráfico de barras que muestra la distribución de frecuencias de datos continuos: su centro, su dispersión y su forma.
3. **Diagrama de Pareto:** barras ordenadas de mayor a menor frecuencia o costo, con una línea de porcentaje acumulado. Se basa en el principio de Pareto o regla 80/20, popularizado en calidad por Joseph Juran: pocas causas vitales explican la mayor parte del problema.
4. **Diagrama de causa y efecto (Ishikawa o espina de pescado):** organiza las posibles causas de un problema en categorías. En manufactura se usan las 6M: método, mano de obra, máquina, material, medición y medio ambiente. En servicios se usan a menudo las 4P o categorías propias del proceso.
5. **Diagrama de dispersión:** muestra la relación entre dos variables continuas; sirve para ver si existe correlación.
6. **Gráfico de control:** muestra la evolución del proceso en el tiempo con límites de control (sección 6).
7. **Estratificación:** separar los datos por grupos (turno, máquina, proveedor, operador) para encontrar patrones que se esconden en los datos agregados. En algunas versiones de la lista se usa el diagrama de flujo en lugar de la estratificación.

## 4. Correlación y regresión
- El **coeficiente de correlación de Pearson (r)** va de −1 a +1 y mide la fuerza de la relación lineal entre dos variables: cerca de +1, relación directa fuerte; cerca de −1, relación inversa fuerte; cerca de 0, sin relación lineal. Correlación no implica causalidad.
- La **regresión lineal** estima la ecuación Y = a + b × X que mejor se ajusta a los datos; el **R²** indica qué proporción de la variación de Y explica X.

## 5. Capacidad del proceso
La capacidad del proceso indica si un proceso estable es capaz de cumplir las especificaciones del cliente. Requiere que el proceso esté bajo control estadístico y que los datos sean aproximadamente normales.
- **LIE y LSE:** límites inferior y superior de especificación, que fija el cliente.
- **Cp = (LSE − LIE) / (6σ):** compara el ancho de la especificación con la variación natural del proceso (6σ), sin considerar dónde está centrado.
- **Cpk = mín[(LSE − μ) / (3σ), (μ − LIE) / (3σ)]:** considera además el centrado: mide la distancia de la media al límite más cercano.
- **Pp y Ppk:** fórmulas equivalentes que usan la desviación estándar total de largo plazo en lugar de la variación de corto plazo dentro de los subgrupos.
Interpretación habitual: Cpk menor que 1 indica que el proceso produce fuera de especificación; entre 1 y 1,33, que es apenas capaz; mayor o igual a 1,33, que es capaz. Un proceso con nivel seis sigma tiene Cp = 2 y Cpk = 1,5 si se considera el desplazamiento de 1,5 sigmas. Si Cp es alto y Cpk bajo, el proceso tiene poca variación pero está descentrado: conviene ajustar la media.
Ejemplo: un eje tiene especificación de 10,0 ± 0,6 mm (LIE = 9,4 y LSE = 10,6), media de 10,1 mm y σ = 0,15 mm. Cp = 1,2 / 0,9 = 1,33. Cpk = mín(0,5 / 0,45; 0,7 / 0,45) = mín(1,11; 1,56) = 1,11. El proceso tendría capacidad suficiente si estuviera centrado, pero está desplazado hacia el límite superior.

## 6. Control estadístico de procesos (SPC)
Walter Shewhart, de los Laboratorios Bell, propuso los gráficos de control en la década de 1920. Distinguió dos tipos de variación:
- **Causas comunes (o aleatorias):** variación natural e inherente al proceso; un proceso con solo causas comunes está bajo control estadístico y es predecible.
- **Causas especiales (o asignables):** variación por un hecho particular (una materia prima defectuosa, un operador nuevo, una máquina desajustada); se deben identificar y eliminar.
Un gráfico de control tiene una línea central (la media) y límites de control superior e inferior, normalmente a ±3σ del estadístico graficado. Los límites de control se calculan con los datos del proceso; no son los límites de especificación del cliente.
### 6.1 Tipos de gráficos de control
Para variables continuas se usan los gráficos X̄-R, X̄-S e I-MR; para atributos, los gráficos p, np, c y u.
Para datos continuos (variables):
- **X̄-R (media y rango):** subgrupos pequeños, normalmente de 2 a 9 unidades.
- **X̄-S (media y desviación estándar):** subgrupos más grandes, de 10 o más.
- **I-MR (valores individuales y rango móvil):** cuando se mide una unidad a la vez, por ejemplo, en procesos lentos o datos administrativos.
Para datos de atributos:
- **p:** proporción de unidades defectuosas, con tamaño de muestra variable.
- **np:** número de unidades defectuosas, con tamaño de muestra constante.
- **c:** número de defectos por unidad de inspección de tamaño constante.
- **u:** defectos por unidad, con tamaño de muestra variable.
### 6.2 Cálculo de límites del gráfico X̄-R
- Gráfico de medias: LC = X̄̄ (promedio de las medias), LCS = X̄̄ + A2 × R̄ y LCI = X̄̄ − A2 × R̄.
- Gráfico de rangos: LC = R̄, LCS = D4 × R̄ y LCI = D3 × R̄.
- Para subgrupos de 5 unidades, las constantes son A2 = 0,577, D3 = 0, D4 = 2,114 y d2 = 2,326. La desviación estándar del proceso se estima como σ = R̄ / d2.
Ejemplo: con subgrupos de 5 piezas, X̄̄ = 50,0 y R̄ = 4,0, los límites del gráfico de medias son 50,0 ± 0,577 × 4,0, es decir, LCS = 52,31 y LCI = 47,69. Para el gráfico de rangos, LCS = 2,114 × 4,0 = 8,46 y LCI = 0. La desviación estándar estimada es 4,0 / 2,326 = 1,72.
### 6.3 Cálculo de límites del gráfico p
LCS y LCI = p̄ ± 3 × √(p̄ × (1 − p̄) / n). Si el LCI resulta negativo, se toma 0.
Ejemplo: con una proporción promedio de defectuosos p̄ = 0,04 y muestras de n = 200, √(0,04 × 0,96 / 200) = 0,0139; LCS = 0,04 + 3 × 0,0139 = 0,0816, es decir, 8,16 %, y el LCI es 0.
### 6.4 Reglas para detectar causas especiales
Las reglas de la Western Electric (1956) dividen el gráfico en zonas de una sigma. Se considera que hay una causa especial cuando:
1. Un punto cae fuera de los límites de control (más allá de 3σ).
2. Dos de tres puntos consecutivos están más allá de 2σ, del mismo lado de la línea central.
3. Cuatro de cinco puntos consecutivos están más allá de 1σ, del mismo lado.
4. Ocho puntos consecutivos están del mismo lado de la línea central.
Las reglas de Nelson agregan otros patrones, como seis puntos seguidos subiendo o bajando (tendencia). Usar muchas reglas a la vez aumenta las falsas alarmas.

## 7. Pruebas de hipótesis (nociones)
Una prueba de hipótesis decide con datos si una diferencia observada es real o se debe al azar. La **hipótesis nula (H0)** dice que no hay diferencia o efecto; la **alternativa (H1)**, que sí la hay. Si el **valor p** es menor que el nivel de significancia elegido (normalmente α = 0,05), se rechaza H0. Pruebas frecuentes: t de Student para comparar medias, ANOVA para comparar tres o más medias, chi cuadrado para datos de atributos y pruebas de normalidad como Anderson-Darling.

## Fuentes
- NIST/SEMATECH. e-Handbook of Statistical Methods, sección 6.1.6 "What is Process Capability?" y sección 6.3 "Univariate and Multivariate Control Charts" (itl.nist.gov/div898/handbook).
- Montgomery, D. C. Introduction to Statistical Quality Control. Wiley (8.ª ed., 2019).
- Ishikawa, K. Guide to Quality Control. Asian Productivity Organization, 1976.
- Western Electric Company. Statistical Quality Control Handbook. 1956.
- ASQ. "Control Chart" y "The Seven Basic Quality Tools" (asq.org/quality-resources).
- AIAG. Statistical Process Control (SPC) Reference Manual (2.ª ed., 2005).
