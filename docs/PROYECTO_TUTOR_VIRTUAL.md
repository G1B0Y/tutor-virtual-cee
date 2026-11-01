# Tutor Virtual 24/7 – Contexto completo para el desarrollo

Resumen de los documentos de `docs/referencia/`. Si algo aquí contradice a un documento original, manda el más reciente: **Requerimientos MVP (11/10/2026)** > Requerimientos funcionales y no funcionales (10/10) > Informe v2 (04/10) > Informe de viabilidad del CEE (22/09) > Avance v1 (19/09).

## 1. Objetivo

Un asistente académico conversacional que responde, a cualquier hora y en español, las consultas de los alumnos del Centro de Especialización Ejecutiva (CEE) de la FIIS-UNI, usando **solo** la información y los materiales que el CEE valida. Cuando no tiene evidencia o el tema no le corresponde, lo dice, no inventa, y deja la consulta registrada para el personal del CEE.

- Vive **dentro del Campus Virtual del CEE** (proyecto del Grupo 3), no como aplicación aparte.
- Atención **24/7**: el CEE no tiene personal todo el día, así que el bot es el primer punto de atención.
- **Costo incremental S/ 0**, con el equipo que ya tiene el CEE.

## 2. Actores

| Actor | Qué espera del sistema |
| --- | --- |
| Alumno del CEE | Respuestas claras y confiables a cualquier hora, sin salir del campus |
| Administrador de la base de conocimiento (CEE) | Cargar, versionar y retirar documentos sin tocar el código |
| Responsable de TI | Un sistema que se reinicia solo, se monitorea y se respalda sin servicios externos |
| Personal del CEE (canal humano) | Recibir las consultas que el bot no resolvió, con su contexto |

En el MVP los roles se simplifican a **alumno** y **operación restringida por TI**.

## 3. Requerimientos del MVP

### Funcionales

| ID | Requerimiento |
| --- | --- |
| RF-M01 | Chat integrado al Campus Virtual en PC y móvil; sesión institucional si el Grupo 3 entrega integración segura |
| RF-M02 | Preguntas en español sobre cursos y documentos validados; respuesta RAG con nombre de fuente y página |
| RF-M03 | Ante evidencia insuficiente o tema fuera de alcance: abstenerse, explicar límites y orientar al canal humano |
| RF-M04 | Registrar consultas no resueltas para atención diferida, con la mínima información y retención aprobada |
| RF-M05 | Carga inicial por script de PDFs con texto y FAQs; metadatos, vigencia y retiro de versiones antiguas |
| RF-M06 | API REST de consulta y de salud; límites por usuario, cola corta y aviso de sistema ocupado |
| RF-M07 | Registro mínimo de errores, tiempos y eventos técnicos, sin datos sensibles innecesarios |

### No funcionales

| ID | Requerimiento |
| --- | --- |
| RNF-M01 | 24/7 como objetivo, no SLA; registrar caídas y probar recuperación automática. 99 % condicionado al piloto |
| RNF-M02 | Una generación LLM activa; ensayar 1, 3, 5 y 9 solicitudes con cola y timeout |
| RNF-M03 | Modelo pequeño cuantizado, contexto limitado, un solo LLM cargado; medir RAM del stack |
| RNF-M04 | Sin fuentes relevantes, no inventar; evaluar con ≥ 30 preguntas del CEE, incluidas fuera de alcance |
| RNF-M05 | HTTPS, permisos mínimos; Ollama y PostgreSQL no expuestos |
| RNF-M06 | Datos y modelos procesados localmente; respaldo y restauración probada |
| RNF-M07 | Costo S/ 0 con licencias verificadas; si falla el benchmark se recorta alcance, sin comprar hardware |

Siguen aplicando del documento completo: aislamiento respecto del campus (RNF-03), degradación con FAQs si cae el modelo (RNF-04), transparencia "asistente automatizado que puede equivocarse" (RNF-13), prompt injection (RNF-17), credenciales fuera del repo (RNF-18), Ley N.º 29733 (RNF-21), accesibilidad básica WCAG 2.1 AA (RNF-26).

### Segunda iteración

RF-05 memoria extensa, RF-06 streaming, RF-11 explicaciones avanzadas, RF-12 cuestionarios, RF-15 valoración, RF-18 historial, RF-19 personalización por matrícula, RF-23 verificación tras la carga, RF-28 indicadores, RF-29 configuración administrativa.

### Fuera de alcance

Matrícula, pagos, certificados, notas, asistencia y gestión administrativa: el bot solo orienta hacia el sistema o área correspondiente.

## 4. Comportamiento esperado 24/7

| Situación | Qué debe pasar |
| --- | --- |
| Consulta sin personal del CEE | Responde con material validado; si no puede, informa el horario del canal humano y registra la consulta |
| Corte de energía o reinicio | Los servicios se levantan solos; durante la caída el chat avisa y el campus sigue funcionando |
| Muchos alumnos a la vez | Cola con aviso de espera y límite por usuario; FAQs sin LLM primero |
| Ollama caído | El chat lo informa, responde FAQs si puede y se alerta a TI |
| Caída de internet | El procesamiento es local; no afecta |

## 5. Infraestructura disponible

| Recurso | Valor |
| --- | --- |
| Equipo | HP ProDesk 600 G1 SFF |
| CPU | Intel Core i5-4590, 3.30 GHz, 4 núcleos / 4 hilos |
| RAM | 8 GB DDR3 (~4.07 GB libres observados) |
| GPU | Intel HD 4600 integrada, sin GPU dedicada |
| Disco | SSD 447 GB (~372 GB libres) |
| Red | Ethernet 1 Gbps; acceso externo no verificado |
| SO | Windows 10 Pro (sin soporte desde 2025); Ubuntu Server 24.04 solo planificado |
| Demanda estimada | 5–9 alumnos simultáneos (no equivale a 5–9 generaciones en paralelo) |

## 6. Criterios de aceptación

| Criterio | Meta |
| --- | --- |
| Recuperación (recall@5) | ≥ 80 % del set de preguntas |
| Respuestas correctas con fuente | ≥ 85 % |
| Rechazo de preguntas sin información | 100 % |
| Errores críticos | 0 |
| Disponibilidad en el piloto | ≥ 95 % del horario definido (99 % mensual = meta no comprometida) |
| Benchmark | ≥ 30 preguntas, ≥ 2 LLM, ≥ 2 embeddings; primer token, tiempo total, RAM |
| Seguridad | Solo Nginx expuesto, HTTPS, pruebas de prompt injection |
| Costo | S/ 0 incremental |

## 7. Pendiente de confirmar

Ver "Pendientes" en `CLAUDE.md` y la revisión del 01/11/2026: https://claude.ai/artifact/WAMTQ1e8uDt3MGEoSwouqc
