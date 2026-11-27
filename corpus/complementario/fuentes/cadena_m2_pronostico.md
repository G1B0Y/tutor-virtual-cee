# Gestión de la Cadena de Suministro – Módulo 2: Pronóstico y planificación de la demanda

## 1. ¿Para qué sirve el pronóstico?
El pronóstico de la demanda estima cuánto comprarán los clientes en un periodo futuro. Es la base de casi todas las decisiones de la cadena de suministro: compras, producción, inventarios, capacidad, personal y transporte. Todo pronóstico tiene error; por eso se debe acompañar de una medida de su precisión y revisarse periódicamente. Los pronósticos agregados (por familia de productos o por región) suelen ser más precisos que los pronósticos detallados por artículo, y los de corto plazo más precisos que los de largo plazo.

## 2. Componentes de una serie de tiempo
- **Nivel:** el valor promedio de la demanda.
- **Tendencia:** crecimiento o disminución sostenida en el tiempo.
- **Estacionalidad:** patrón que se repite en periodos fijos (meses del año, días de la semana).
- **Ciclo:** fluctuaciones de más de un año ligadas a la economía.
- **Componente aleatorio:** variación que no se puede explicar ni predecir.

## 3. Métodos cualitativos
Se usan cuando no hay datos históricos suficientes (producto nuevo) o cuando el entorno cambia mucho:
- **Método Delphi:** un panel de expertos responde en varias rondas anónimas hasta llegar a un consenso.
- **Opinión de la fuerza de ventas:** cada vendedor estima las ventas de su zona y se consolidan.
- **Jurado de opinión ejecutiva:** un grupo de gerentes estima la demanda en conjunto.
- **Investigación de mercados:** encuestas y estudios a clientes potenciales.

## 4. Métodos cuantitativos de series de tiempo
### 4.1 Promedio móvil simple
El pronóstico del siguiente periodo es el promedio de las últimas n demandas reales. Un n grande suaviza más pero reacciona más lento a los cambios.
Ejemplo: con demandas de enero a junio de 120, 132, 128, 140, 136 y 150 unidades, el promedio móvil de 3 periodos para julio es (140 + 136 + 150) / 3 = 142 unidades.
### 4.2 Promedio móvil ponderado
Asigna más peso a los datos más recientes; los pesos suman 1.
Ejemplo: con pesos 0,5 para junio, 0,3 para mayo y 0,2 para abril, el pronóstico de julio es 0,5 × 150 + 0,3 × 136 + 0,2 × 140 = 143,8 unidades.
### 4.3 Suavizamiento exponencial simple
El nuevo pronóstico corrige el anterior con una fracción α del último error: F(t+1) = F(t) + α × (A(t) − F(t)), donde A(t) es la demanda real, F(t) el pronóstico del periodo t y α la constante de suavizamiento, entre 0 y 1. Un α alto reacciona rápido a los cambios; un α bajo suaviza más. Es adecuado para demanda sin tendencia ni estacionalidad.
Ejemplo: si el pronóstico de junio fue 138, la demanda real de junio fue 150 y α = 0,3, el pronóstico de julio es 138 + 0,3 × (150 − 138) = 141,6 unidades.
### 4.4 Suavizamiento con tendencia (Holt) y con estacionalidad (Holt-Winters)
- El método de Holt agrega una segunda ecuación que suaviza la tendencia (constante β), para series con crecimiento o caída sostenidos.
- El método de Holt-Winters agrega una tercera ecuación para los índices estacionales (constante γ). Puede ser aditivo (la estacionalidad suma una cantidad fija) o multiplicativo (la estacionalidad es un porcentaje del nivel).
### 4.5 Índices estacionales
Un índice estacional indica cuánto se aleja un periodo del promedio. Por ejemplo, un índice de 1,20 para diciembre significa que en diciembre se vende 20 % más que en un mes promedio. Para pronosticar, se desestacionaliza la serie (dividiendo entre el índice), se proyecta la tendencia y luego se vuelve a multiplicar por el índice.

## 5. Métodos causales
Relacionan la demanda con variables que la explican, como el precio, la publicidad, el PBI o el clima. El más usado es la **regresión lineal**: Y = a + b × X, donde Y es la demanda, X la variable explicativa, a el intercepto y b la pendiente. La regresión con el tiempo como variable X sirve para proyectar una tendencia lineal. El coeficiente de determinación R² indica qué parte de la variación de la demanda explica el modelo.

## 6. Medición del error del pronóstico
El error de un periodo es e(t) = A(t) − F(t), demanda real menos pronóstico.
- **MAD (desviación absoluta media):** promedio de los errores en valor absoluto.
- **MSE (error cuadrático medio):** promedio de los errores al cuadrado; penaliza más los errores grandes.
- **MAPE (error porcentual absoluto medio):** promedio de |e(t)| / A(t), expresado en porcentaje; permite comparar productos de distinto volumen.
- **Sesgo:** suma o promedio de los errores con su signo; si es positivo, el pronóstico subestima la demanda y, si es negativo, la sobrestima.
- **Señal de rastreo (tracking signal):** suma de los errores dividida entre el MAD. Si sale de un rango definido, comúnmente ±4, el pronóstico tiene sesgo y debe revisarse.
Ejemplo: con demandas reales de 100, 110, 95 y 105 y pronósticos de 98, 105, 100 y 100, los errores son 2, 5, −5 y 5. El MAD es (2 + 5 + 5 + 5) / 4 = 4,25; el MSE es (4 + 25 + 25 + 25) / 4 = 19,75; el MAPE es 4,14 %; la suma de errores es 7 y la señal de rastreo es 7 / 4,25 = 1,65, dentro del rango aceptable.

## 7. Planificación de ventas y operaciones (S&OP)
La planificación de ventas y operaciones (Sales and Operations Planning, S&OP) es un proceso mensual en el que las áreas de ventas, marketing, operaciones, compras y finanzas acuerdan un único plan para los siguientes 12 a 18 meses, por familias de productos. Su objetivo es equilibrar la demanda y la oferta y alinear las operaciones con el plan financiero y la estrategia.
Pasos habituales del ciclo mensual: recolección de datos, planificación de la demanda, planificación del suministro, reunión previa (pre-S&OP) y reunión ejecutiva de S&OP.
1. **Recolección de datos:** cierre de ventas reales, inventarios y actualización de las bases para el pronóstico.
2. **Planificación de la demanda:** ventas y marketing revisan el pronóstico estadístico y lo ajustan con información del mercado.
3. **Planificación del suministro:** operaciones verifica si la capacidad, los materiales y el personal alcanzan para cubrir la demanda.
4. **Reunión previa (pre-S&OP):** los responsables resuelven diferencias y preparan escenarios y recomendaciones.
5. **Reunión ejecutiva de S&OP:** la alta dirección toma las decisiones y aprueba el plan.
La evolución del S&OP que integra explícitamente el plan financiero y la estrategia se conoce como **planificación integrada del negocio (Integrated Business Planning, IBP)**.
### 7.1 Estrategias del plan agregado
- **Persecución (chase):** la producción sigue a la demanda, contratando o ajustando turnos; bajo inventario y mayores costos de cambio.
- **Nivelación (level):** producción constante; el inventario absorbe las diferencias con la demanda.
- **Mixta:** combinación de ambas, con horas extra, subcontratación o inventario estacional.

## 8. Del plan agregado al detalle: MPS, MRP y DRP
- **Programa maestro de producción (MPS):** desagrega el plan por producto final y por semana.
- **Planificación de requerimientos de materiales (MRP):** a partir del MPS, la lista de materiales (BOM) y el estado del inventario, calcula qué componentes comprar o fabricar, en qué cantidad y cuándo, considerando sus tiempos de entrega.
- **Planificación de requerimientos de distribución (DRP):** aplica la misma lógica para reabastecer los centros de distribución.

## 9. Planificación colaborativa (CPFR)
CPFR (Collaborative Planning, Forecasting and Replenishment) es una práctica en la que el proveedor y el cliente comparten pronósticos, planes promocionales e información de ventas y acuerdan un pronóstico conjunto y un plan de reabastecimiento. Reduce el efecto látigo y los quiebres de stock.

## Fuentes
- Hyndman, R. J. y Athanasopoulos, G. Forecasting: Principles and Practice. OTexts (3.ª ed., 2021), disponible en otexts.com/fpp3.
- Chopra, S. y Meindl, P. Supply Chain Management: Strategy, Planning, and Operation. Pearson (7.ª ed., 2019), capítulos de pronóstico y planificación agregada.
- Heizer, J., Render, B. y Munson, C. Principios de administración de operaciones. Pearson.
- Wallace, T. F. Sales & Operations Planning: The How-To Handbook. T. F. Wallace & Company.
- ASCM. ASCM Supply Chain Dictionary (definiciones de S&OP, IBP, MPS, MRP y DRP).
