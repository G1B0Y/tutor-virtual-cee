# Sistemas Integrados Empresariales – Módulo de Costos: apuntes de clase

## 1. Costo y gasto
- **Costo:** es un "sacrificio" que realiza la empresa para obtener un bien o llevar a cabo un servicio que será ofrecido a los clientes. Se considera un sacrificio porque existe un lapso (por ejemplo, tres meses) entre el momento en que se paga al proveedor y el momento en que el cliente paga por el producto final; durante ese tiempo la empresa no ve el retorno inmediato de su inversión.
- **Gasto:** es un desembolso de dinero necesario para apoyar la fabricación del bien o la administración del servicio, pero que no se recupera directamente como el costo.

## 2. Gastos generales
Los gastos generales se componen de tres categorías: gastos administrativos, gastos de ventas y gastos financieros.
- **Gastos administrativos:** relacionados con la gestión de la empresa.
- **Gastos de ventas:** relacionados con la comercialización.
- **Gastos financieros:** incluyen los intereses de préstamos, el impuesto a las transacciones financieras (ITF), las comisiones bancarias y los portes.

## 3. Estructura en el Estado de Resultados
En el Estado de Resultados, la utilidad operativa se calcula restando a los ingresos los costos, los gastos administrativos y los gastos de ventas.
Los gastos financieros no son operativos; por eso se descuentan después de la utilidad operativa, para llegar a la utilidad antes de impuestos o neta.

## 4. Objeto de costo y centro de costos
- **Objeto de costo:** es aquello que se va a costear (un producto, un área, una máquina, etc.).
- **Centro de costos:** es el lugar o entidad donde se consumen los recursos y se imputan los costos. Puede ser un área, una máquina, un proceso o un puesto de trabajo (por ejemplo, "Centro de Costos Planta General" o "Proceso A").

## 5. Los tres elementos del costo
Los tres elementos del costo de producción son: la Materia Prima Directa (MPD), la Mano de Obra Directa (MOD) y los Costos Indirectos de Fabricación (CIF).
- **Materia Prima Directa (MPD):** se obtiene multiplicando la cantidad consumida por el costo unitario de la materia prima. La cantidad consumida sale del módulo de Producción (recetas) y el costo unitario sale del registro de Compras y Almacén (kardex valorizado).
- **Mano de Obra Directa (MOD):** se obtiene multiplicando las horas hombre utilizadas por la tasa del costo laboral (soles por hora). Las horas salen del control de tiempos (marcado de reloj, horas efectivas en máquina) y la tasa sale de la planilla de Recursos Humanos. Las horas efectivas son las de trabajo real, descontando tiempos muertos como ir al baño o almorzar.
- **Costos Indirectos de Fabricación (CIF):** incluyen materiales indirectos (suministros de oficina, limpieza), seguros del local, energía eléctrica, agua y depreciación de maquinaria.

## 6. Costo primo y costo de conversión
- **Costo primo:** suma de la Materia Prima Directa más la Mano de Obra Directa (MPD + MOD).
- **Costo de conversión:** suma de los Costos Indirectos de Fabricación más la Mano de Obra Directa (CIF + MOD).

## 7. Metodologías de costeo
Para asignar los costos (especialmente los indirectos) a los productos existen varias metodologías. Las metodologías de costeo son: costeo tradicional, costeo ABC, costeo por órdenes de trabajo, costeo por procesos y costeo estándar.

## 8. Costeo tradicional
Es un método de asignación que usa una base de distribución única (generalmente el volumen o la cantidad producida) para repartir los costos indirectos (CIF).
- **Ejemplo:** si el gasto de luz es 5,000 y se producen 3,000 unidades, se divide 5,000 entre 3,000 y se asigna igual a todos.
- **Desventaja:** no refleja la realidad, porque asigna el mismo peso a procesos que podrían consumir recursos de manera diferente.
- **Uso:** se sigue usando porque es barato y fácil de aplicar. Si los costos indirectos son bajos (por ejemplo, 10-15% del total), no vale la pena usar un sistema complejo.

## 9. Costeo ABC
El costeo ABC se basa en actividades. Primero se asignan los costos a las actividades (por ejemplo, negociar con proveedores o firmar cheques) y luego esas actividades se asignan a los objetos de costo.
- **Ventaja:** es la metodología más cercana a la realidad.
- **Desventaja:** es muy complejo y costoso de implementar. Requiere mapear todas las actividades, capacitar al personal para registrar tiempos por actividad y tener sistemas de información robustos.

## 10. Costeo por órdenes de trabajo y costeo por procesos
- **Costeo por órdenes de trabajo:** se utiliza cuando la producción es por pedido específico (por ejemplo, una imprenta o una carpintería). Los costos se acumulan por cada orden. La MPD y la MOD son de asignación directa (se sabe cuánto se usó para esa orden). El reto está en asignar los CIF (energía, depreciación) a cada orden, lo que requiere una metodología de prorrateo.
- **Costeo por procesos:** se usa en producción continua. Los costos se asignan a cada proceso (A, B, C) y se van acumulando conforme el producto avanza: el proceso B carga sus propios costos más los costos heredados del proceso A.

## 11. Costeo estándar
El costeo estándar es el más usado. Es una proyección basada en data histórica para determinar un costo estimado antes de producir.
- **Funcionamiento:** se calcula una tasa estándar (por ejemplo, 3.5 soles por kilo de CIF). Esa tasa se ingresa al sistema (un ERP como SAP o Epicor) y se multiplica automáticamente por la producción real.
- **Herramienta:** el costeador usa Excel para procesar la data histórica y calcular estas tasas, que luego sube al sistema.
- **Control:** al final del periodo se compara el costo estándar contra el costo real, para analizar las variaciones y ajustar.
