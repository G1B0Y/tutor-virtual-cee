# Gestión de Proyectos con el PMBOK – Unidad 3: Gestión de los costos y del valor ganado

## 1. Procesos de la gestión de costos
La gestión de los costos busca que el proyecto se complete dentro del presupuesto aprobado. Comprende:
1. **Planificar la gestión de los costos:** unidades, nivel de precisión, umbrales de control y reglas para medir el desempeño.
2. **Estimar los costos:** aproximar los recursos monetarios necesarios para cada actividad o paquete de trabajo.
3. **Determinar el presupuesto:** sumar las estimaciones para establecer la línea base de costos autorizada.
4. **Controlar los costos:** monitorear el gasto y el avance y gestionar los cambios a la línea base.
En la octava edición del PMBOK estos temas forman parte del dominio de desempeño de **finanzas**.

## 2. Estimación de costos
Técnicas de estimación:
- **Análoga:** con el costo real de un proyecto similar anterior.
- **Paramétrica:** con una relación estadística entre variables. Ejemplo: si construir un metro cuadrado de oficina cuesta S/ 450, 200 m² cuestan S/ 90 000.
- **Ascendente (bottom-up):** se estima cada paquete de trabajo y se suman; es la más precisa pero la que más tiempo toma.
- **Tres valores:** igual que en las duraciones, con (O + 4M + P) / 6 en la distribución beta.
- **Análisis de ofertas de proveedores.**
Rangos de precisión de referencia según el PMI: la **estimación de orden de magnitud** (al inicio) tiene un rango de −25 % a +75 %, y la **estimación definitiva** (más adelante) de −5 % a +10 %.
Tipos de costos: **directos** (atribuibles al proyecto: materiales, mano de obra del equipo) e **indirectos** (gastos generales compartidos), **fijos** y **variables**.

## 3. Presupuesto, reservas y línea base de costos
- Las estimaciones de las actividades se suman por paquete de trabajo y por cuenta de control.
- Se agrega la **reserva para contingencias**, destinada a los riesgos identificados ("incógnitas conocidas"); forma parte de la línea base y la gestiona el director del proyecto.
- El resultado es la **línea base de costos**, también llamada presupuesto hasta la conclusión (BAC); distribuida en el tiempo forma la **curva S**.
- Se agrega la **reserva de gestión**, para trabajo no previsto ("incógnitas desconocidas"); no forma parte de la línea base y su uso requiere aprobación de la dirección.
- El **presupuesto del proyecto** es la línea base de costos más la reserva de gestión.
Ejemplo: los paquetes de trabajo suman S/ 80 000 y la reserva para contingencias es S/ 8 000; la línea base de costos es S/ 88 000. Con una reserva de gestión de S/ 5 000, el presupuesto del proyecto es S/ 93 000.

## 4. Gestión del valor ganado (EVM)
La gestión del valor ganado integra alcance, cronograma y costo para medir el desempeño del proyecto en una fecha de corte.
### 4.1 Valores básicos
Los tres valores básicos son PV (valor planificado), EV (valor ganado) y AC (costo real), que se comparan con el BAC (presupuesto hasta la conclusión).
- **PV (valor planificado):** presupuesto autorizado del trabajo que debía estar hecho a la fecha.
- **EV (valor ganado):** presupuesto del trabajo realmente completado a la fecha. EV = porcentaje completado × BAC.
- **AC (costo real):** lo que realmente se gastó en el trabajo completado.
- **BAC (presupuesto hasta la conclusión):** presupuesto total del proyecto (línea base de costos).
### 4.2 Variaciones e índices
- **Variación del costo:** CV = EV − AC. Negativa = sobrecosto.
- **Variación del cronograma:** SV = EV − PV. Negativa = atraso.
- **Índice de desempeño del costo:** CPI = EV / AC. Menor que 1 = se gasta más de lo presupuestado por cada unidad de trabajo.
- **Índice de desempeño del cronograma:** SPI = EV / PV. Menor que 1 = el trabajo avanza más lento de lo planificado.
### 4.3 Pronósticos
- **Estimación a la conclusión (EAC):**
  - Si se espera que el desempeño de costos actual continúe: EAC = BAC / CPI.
  - Si lo que falta se ejecutará según el presupuesto original: EAC = AC + (BAC − EV).
  - Si el costo y el atraso influyen juntos en lo que falta: EAC = AC + (BAC − EV) / (CPI × SPI).
  - Si la estimación original ya no es válida: EAC = AC + nueva estimación ascendente de lo que falta.
- **Estimación hasta la conclusión:** ETC = EAC − AC.
- **Variación a la conclusión:** VAC = BAC − EAC. Negativa = el proyecto terminará por encima del presupuesto.
- **Índice de desempeño del trabajo por completar:** TCPI = (BAC − EV) / (BAC − AC) para terminar dentro del BAC, o (BAC − EV) / (EAC − AC) para terminar dentro de un EAC aprobado. Un TCPI mayor que 1 indica que el trabajo restante debe hacerse con más eficiencia que la lograda hasta ahora.
### 4.4 Ejemplo resuelto
Un proyecto tiene un BAC de S/ 100 000. Al cierre del cuarto mes, el plan decía que debía haberse completado trabajo por S/ 50 000 (PV), pero solo se ha completado el 40 % del proyecto y se han gastado S/ 50 000.
- EV = 40 % × 100 000 = S/ 40 000; AC = S/ 50 000; PV = S/ 50 000.
- CV = 40 000 − 50 000 = −S/ 10 000 (sobrecosto).
- SV = 40 000 − 50 000 = −S/ 10 000 (atraso).
- CPI = 40 000 / 50 000 = 0,8: por cada sol gastado se obtienen 80 céntimos de trabajo.
- SPI = 40 000 / 50 000 = 0,8: se avanza al 80 % del ritmo planificado.
- EAC (si sigue el CPI actual) = 100 000 / 0,8 = S/ 125 000.
- ETC = 125 000 − 50 000 = S/ 75 000.
- VAC = 100 000 − 125 000 = −S/ 25 000.
- EAC con CPI y SPI = 50 000 + 60 000 / (0,8 × 0,8) = 50 000 + 93 750 = S/ 143 750.
- EAC si lo restante sigue el presupuesto = 50 000 + 60 000 = S/ 110 000.
- TCPI para cumplir el BAC = (100 000 − 40 000) / (100 000 − 50 000) = 1,2: el trabajo restante tendría que hacerse con un 20 % más de eficiencia.
### 4.5 Reglas para medir el avance (EV)
- **0/100:** el valor se gana solo al terminar la actividad; para actividades cortas.
- **50/50:** la mitad al empezar y la mitad al terminar.
- **Porcentaje completado:** según una estimación del avance físico.
- **Hitos ponderados:** cada hito alcanzado gana un porcentaje fijo del presupuesto.

## 5. Control de costos
Se comparan el gasto y el avance con la línea base, se analizan las causas de las variaciones (tendencias del CPI y del SPI), se pronostica el costo final y se recomiendan acciones correctivas o solicitudes de cambio. El valor ganado no reemplaza el análisis de la ruta crítica: un SPI cercano a 1 puede ocultar el atraso de una actividad crítica compensado por el adelanto de actividades no críticas.

## Fuentes
- PMI. A Guide to the Project Management Body of Knowledge (PMBOK® Guide), 6.ª ed. (2017), capítulo 7 "Gestión de los costos del proyecto", y 8.ª ed. (2025), dominio de finanzas.
- PMI. The Standard for Earned Value Management. 2019.
- Fleming, Q. W. y Koppelman, J. M. Earned Value Project Management. PMI (4.ª ed., 2010).
- Kerzner, H. Project Management: A Systems Approach to Planning, Scheduling, and Controlling. Wiley (13.ª ed., 2022).
