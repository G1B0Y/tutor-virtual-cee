# Gestión de la Cadena de Suministro – Módulo 3: Gestión de inventarios

## 1. Funciones y tipos de inventario
El inventario es la existencia de materiales o productos que una organización mantiene para usarlos o venderlos más adelante. Cumple varias funciones: desacoplar etapas del proceso, protegerse de la incertidumbre de la demanda y del abastecimiento, aprovechar economías de escala en compras y transporte, y atender demandas estacionales.
Por su etapa en el proceso, se distinguen:
- **Materias primas e insumos.**
- **Productos en proceso (WIP).**
- **Productos terminados.**
- **Repuestos y materiales de mantenimiento (MRO).**
Por su función, se distinguen el inventario de ciclo (el que se consume entre pedidos), el inventario de seguridad, el inventario en tránsito y el inventario estacional o de anticipación.

## 2. Costos relacionados con el inventario
- **Costo de pedir o de preparación (S):** costo fijo por cada pedido o por cada preparación de máquina: emisión de la orden, transporte fijo, recepción e inspección.
- **Costo de mantener (H):** costo anual de tener una unidad en inventario: capital inmovilizado, almacenamiento, seguros, obsolescencia y mermas. Se suele expresar como un porcentaje i del costo unitario C, de modo que H = i × C.
- **Costo de faltante:** ventas perdidas, pedidos pendientes, penalidades y pérdida de clientes.
- **Costo de compra:** precio unitario por la cantidad comprada; importa cuando hay descuentos por volumen.

## 3. Clasificación ABC
La clasificación ABC ordena los artículos según su valor anual de consumo (demanda anual × costo unitario) y aplica el principio de Pareto: pocos artículos concentran la mayor parte del valor.
- **Artículos A:** aproximadamente el 20 % de los ítems y el 80 % del valor. Requieren control estricto, registros exactos, revisión frecuente y buena relación con el proveedor.
- **Artículos B:** aproximadamente el 30 % de los ítems y el 15 % del valor. Control intermedio.
- **Artículos C:** aproximadamente el 50 % de los ítems y solo el 5 % del valor. Controles simples y pedidos más grandes y menos frecuentes.
Los porcentajes son referenciales: cada empresa define sus cortes al ordenar los artículos de mayor a menor valor y calcular el porcentaje acumulado.
Pasos: (1) calcular el valor anual de cada ítem; (2) ordenarlos de mayor a menor; (3) calcular el porcentaje acumulado del valor; (4) asignar las clases según los cortes elegidos.
La clasificación ABC se complementa con otros criterios, como la criticidad del ítem o la variabilidad de su demanda (análisis XYZ).

## 4. Lote económico de compra (EOQ)
El modelo del lote económico de compra (Economic Order Quantity), propuesto por Ford W. Harris en 1913, calcula la cantidad por pedido que minimiza la suma del costo anual de pedir y el costo anual de mantener. Supone demanda constante y conocida, tiempo de entrega constante, reposición instantánea del lote completo, sin faltantes y sin descuentos por cantidad.
Fórmula: EOQ = √(2 × D × S / H), donde D es la demanda anual, S el costo por pedido y H el costo anual de mantener una unidad.
- Costo anual de pedir = (D / Q) × S.
- Costo anual de mantener = (Q / 2) × H, porque el inventario promedio de ciclo es la mitad del lote.
- En el EOQ, el costo de pedir y el costo de mantener son iguales.
Ejemplo: con una demanda anual de 12 000 unidades, un costo por pedido de S/ 150 y un costo de mantener de S/ 4 por unidad al año, el EOQ es √(2 × 12 000 × 150 / 4) = √900 000 ≈ 949 unidades. Se hacen unos 12,65 pedidos al año, uno cada 29 días aproximadamente. El costo anual de pedir es S/ 1 897 y el de mantener también S/ 1 897, con un costo total de S/ 3 795.
### 4.1 Variantes del modelo
- **Lote económico de producción (EPQ):** la reposición no es instantánea sino a una tasa de producción p mayor que la tasa de demanda d. Fórmula: EPQ = √(2 × D × S / (H × (1 − d / p))).
- **Descuentos por cantidad:** se calcula el EOQ para cada rango de precio, se ajusta al mínimo del rango si queda por debajo, y se elige la cantidad con el menor costo total incluido el costo de compra.

## 5. Inventario de seguridad
El inventario de seguridad (safety stock, SS) es la cantidad adicional que se mantiene para cubrir la variabilidad de la demanda y del tiempo de reposición, y así alcanzar el nivel de servicio deseado.
### 5.1 Nivel de servicio y factor Z
El **nivel de servicio de ciclo** es la probabilidad de no tener faltantes durante un ciclo de reposición. El factor Z sale de la distribución normal estándar:
- 90 % → Z = 1,28
- 95 % → Z = 1,65
- 97,5 % → Z = 1,96
- 99 % → Z = 2,33
No se debe confundir con la **tasa de cumplimiento (fill rate)**, que es la proporción de la demanda atendida directamente desde el inventario.
### 5.2 Demanda variable y tiempo de reposición constante
SS = Z × σd × √L, donde σd es la desviación estándar de la demanda diaria y L el tiempo de reposición en días.
Ejemplo: con σd = 20 unidades, L = 9 días y un nivel de servicio de 95 %, SS = 1,65 × 20 × √9 = 1,65 × 20 × 3 = 99 unidades.
### 5.3 Demanda y tiempo de reposición variables
SS = Z × √(L × σd² + d² × σL²), donde d es la demanda diaria promedio y σL la desviación estándar del tiempo de reposición.
Ejemplo: con d = 40 unidades por día, σd = 20, L = 9 días, σL = 2 días y Z = 1,65: L × σd² = 3 600; d² × σL² = 6 400; la raíz de 10 000 es 100, y SS = 1,65 × 100 = 165 unidades.

## 6. Punto de reorden (ROP)
En un sistema de revisión continua, se emite un pedido de tamaño Q cuando la posición de inventario (inventario disponible + pedidos en camino − pedidos pendientes) baja hasta el punto de reorden:
ROP = d × L + SS.
Ejemplo: con una demanda diaria promedio de 40 unidades, L = 9 días y SS = 99 unidades, ROP = 40 × 9 + 99 = 459 unidades.

## 7. Sistemas de revisión del inventario
- **Revisión continua (sistema Q o de cantidad fija):** el inventario se monitorea siempre; cuando llega al ROP se pide una cantidad fija Q (por ejemplo, el EOQ). Requiere más control pero menos inventario de seguridad.
- **Revisión periódica (sistema P o de periodo fijo):** se revisa cada R días y se pide la diferencia hasta un nivel objetivo T: T = d × (R + L) + Z × σd × √(R + L); cantidad a pedir = T − posición de inventario. Facilita agrupar pedidos de varios artículos al mismo proveedor, pero requiere más inventario de seguridad porque protege R + L días.
Ejemplo de revisión periódica: con d = 40, σd = 20, R = 7 días, L = 9 días y Z = 1,65, R + L = 16 y su raíz es 4; T = 40 × 16 + 1,65 × 20 × 4 = 640 + 132 = 772 unidades.
- **Sistema min-max:** se pide hasta el máximo cuando el inventario cae por debajo del mínimo.

## 8. Otras prácticas de gestión de inventarios
- **Conteo cíclico:** contar una parte del inventario cada día o semana, con más frecuencia los artículos A, en lugar de un inventario físico anual completo.
- **Inventario gestionado por el proveedor (VMI):** el proveedor decide cuándo y cuánto reponer con base en la información de consumo del cliente.
- **Consignación:** el inventario está en el almacén del cliente pero sigue siendo del proveedor hasta que se usa.
- **Justo a tiempo (JIT):** recibir los materiales en la cantidad y el momento en que se necesitan, con lotes pequeños y proveedores confiables.
- **Modelo de un solo periodo (vendedor de periódicos, newsvendor):** para productos perecibles o de temporada, la cantidad óptima es la que hace que la probabilidad de no tener faltante sea igual a la razón crítica Cu / (Cu + Co), donde Cu es el costo de faltar una unidad y Co el de que sobre una unidad.

## Fuentes
- Chopra, S. y Meindl, P. Supply Chain Management: Strategy, Planning, and Operation. Pearson (7.ª ed., 2019), capítulos de inventario de ciclo e inventario de seguridad.
- Silver, E. A., Pyke, D. F. y Thomas, D. J. Inventory and Production Management in Supply Chains. CRC Press (4.ª ed., 2017).
- Harris, F. W. "How Many Parts to Make at Once". Factory, The Magazine of Management, 1913.
- Heizer, J., Render, B. y Munson, C. Principios de administración de operaciones. Pearson, capítulo de administración de inventarios.
- ASCM. ASCM Supply Chain Dictionary (definiciones de safety stock, reorder point, cycle counting y VMI).
