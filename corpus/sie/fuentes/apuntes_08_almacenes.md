# Sistemas Integrados Empresariales – Módulo de Almacenes: apuntes de clase

## 1. Qué es un almacén
Un almacén es el espacio físico donde se guardan y depositan materiales y productos. La estructura metálica que se usa para organizar los productos se denomina correctamente **racks**, no estantes.

## 2. Tipos de almacenes en una empresa industrial
Los tipos de almacenes de una empresa industrial son: de materia prima, de productos en proceso, de productos terminados, de mercadería, de productos no conformes y el almacén virtual (o de tránsito).
- **Almacén de materia prima:** guarda los insumos básicos para la producción.
- **Almacén de productos en proceso:** contiene productos que no han completado su ciclo de fabricación. El costeo de estos productos se basa en su grado de avance.
- **Almacén de productos terminados:** almacena los productos listos para la venta.
- **Almacén de mercadería:** contiene productos que la empresa compra y revende sin transformarlos (por ejemplo, una pastelería que vende gaseosas).
- **Almacén de productos no conformes:** aquí se depositan los productos que no han pasado la inspección de calidad.

## 3. Almacén virtual o de tránsito
El almacén virtual (o de tránsito) es un espacio temporal donde se coloca la materia prima recién llegada antes de ser inspeccionada por calidad. Es un estado de tránsito: la materia prima llegó pero aún no ha sido aprobada por Calidad (cuarentena).
La materia prima no se registra oficialmente en el almacén de materia prima hasta que Calidad da su visto bueno. Si el producto es rechazado, se devuelve al proveedor desde el almacén virtual, sin haber ingresado formalmente a los registros de inventario.
Quien administra el almacén de materia prima es responsable de este almacén virtual en el sistema hasta que se decida su ingreso físico definitivo.

## 4. Productos no conformes: qué hacer con ellos
Los productos no conformes son los que no cumplen los estándares. Hay tres opciones para gestionarlos: reprocesar, revender o desechar.
- **Reprocesar:** si se puede salvar parte del producto.
- **Revender (segunda calidad):** venderlo tal como está a un precio menor, si es aceptable para otro mercado.
- **Desechar:** si no tiene arreglo, se elimina.
Caso práctico de clase: unos langostinos que no pasaron la prueba sensorial (olor y color) tuvieron que ser desechados tras la autorización.

## 5. Empresas industriales, comerciales y de servicios
La palabra clave para diferenciar una empresa industrial de una de servicios es **tangible**.
- **Empresa industrial y empresa comercial:** ofrecen productos tangibles.
- **Empresa de servicios:** ofrece un intangible. Una empresa desarrolladora de software, por ejemplo, es una empresa de servicios y, por lo tanto, no tiene almacenes.

## 6. Filosofías de inventario: Just in Time y Cross-Docking
- **Just in Time (JIT):** la filosofía es tener inventario cero. Es de alto riesgo, porque cualquier falla en la cadena de suministro detiene la producción. En clase se mencionó que en Perú es difícil de aplicar por la falta de cultura de cumplimiento y puntualidad de los proveedores.
- **Cross-Docking:** es la técnica en la que el material llega y casi inmediatamente se distribuye, sin ser almacenado por largo tiempo. Funcionamiento: se sincronizan los camiones de entrada y de salida en las rampas; se descarga, se clasifica en la plataforma y se carga al camión de salida.

## 7. Identificación y trazabilidad: código de barras, SKU y lote
- **Código de barras:** sirve para identificar el producto rápidamente mediante un escáner (pistola lectora). Puede ser numérico o alfanumérico. Existen estándares globales como el UPC y el EAN.
- **SKU:** es el código del producto; es el mismo para un tipo de producto.
- **Lote:** cambia según la fecha de producción. Permite la trazabilidad, es decir, saber cuándo se hizo el producto y con qué insumos.
La diferencia entre SKU y lote: el SKU identifica el tipo de producto y no cambia; el lote cambia con cada fecha de producción y permite la trazabilidad.
En el sistema se registra: código (SKU) + cantidad + lote + ubicación.

## 8. Kardex y métodos de valuación de inventarios
El control de inventarios se lleva mediante el Kardex. Se distingue el Kardex físico (del almacén) del Kardex valorizado (de contabilidad).
Los métodos de valuación son: PEPS, UEPS y promedio ponderado.
- **PEPS (Primeras Entradas, Primeras Salidas):** lo primero que entra es lo primero que sale. Es ideal para productos perecibles (moda, alimentos).
- **UEPS (Últimas Entradas, Primeras Salidas):** lo último que entra es lo primero que sale. Importante: este método no está autorizado por la SUNAT en Perú para temas contables.
- **Promedio ponderado:** el costo unitario se actualiza cada vez que hay una nueva compra con precio distinto.
Ejemplo de clase del costo promedio: si se tiene stock a 5 soles y se compra nuevo stock a 6 soles, el nuevo costo promedio sube (por ejemplo, a 5.83). Las salidas de almacén (ventas o producción) se registran a ese costo promedio vigente.

## 9. Niveles de stock y reposición
Los niveles para gestionar el reabastecimiento son: stock máximo, stock mínimo y stock de seguridad.
- **Stock máximo:** el tope de inventario permitido.
- **Stock mínimo:** nivel de alerta.
- **Stock de seguridad:** un "colchón" por debajo del mínimo para cubrir emergencias o retrasos.
- **Lead time:** es el tiempo que transcurre desde que se coloca la orden de compra hasta que el proveedor entrega el producto.

## 10. Operaciones de salida: picking, packing y despacho
Las operaciones de salida se gestionan con un WMS (Warehouse Management System). Son tres: picking, packing y despacho.
- **Picking (recogida):** es la preparación del pedido. Se genera una lista ("picking list") para ir a las ubicaciones y recoger los productos. Se suele hacer consolidado, agrupando varios pedidos a la vez para ser eficientes.
- **Packing (empaquetado):** es el proceso de acondicionar los productos recogidos en cajas o paquetes, según el pedido específico de cada cliente. Aquí se valida que lo recogido coincida con la orden.
- **Despacho (dispatch):** es la zona donde se apilan los pedidos listos para ser cargados en la unidad de transporte.
