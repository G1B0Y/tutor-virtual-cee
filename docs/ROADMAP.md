# Tutor Virtual 24/7 – Roadmap

Plan de trabajo del MVP del Tutor Virtual del CEE FIIS-UNI (Grupo 5). Se desarrolla **en local (PC de Alfredo)** hasta la demo de PC3 y recién después se ensaya en un servidor simulado y en el equipo del CEE. Cada fase termina con algo que se puede ver y probar.

- Alcance: el **MVP ajustado del 11/10/2026** (RF-M01 a RF-M07, RNF-M01 a RNF-M07). Ver `docs/PROYECTO_TUTOR_VIRTUAL.md`.
- Fechas fijas del curso: **PC3 (MVP validado) 17/11/2026**, **PC4 (tutor implementado) 08/12/2026**, informe y exposición final 14–20/12/2026.
- Estado de cada fase: ⬜ por hacer · 🟨 en curso · ✅ hecha. El estado actual también va en `CLAUDE.md`.

## Resumen

| Fase | Fechas | Contenido | Entregable que se revisa | Estado |
| --- | --- | --- | --- | --- |
| 0. Preparación | 01–02/11 | Repo, documentos base, esqueleto y entorno local con Docker | `docker compose up` levanta PostgreSQL + pgvector y Ollama; la API responde `/salud` | ✅ |
| 1. Base de conocimiento | 02–05/11 | Modelo de datos, script de ingesta de PDFs y FAQs, vigencia y retiro | Cargar un corpus de prueba y ver documentos, versiones y fragmentos en la base | 🟨 |
| 2. RAG y benchmark | 04–08/11 | Búsqueda por similitud, umbral de rechazo, set de 30 preguntas, comparación de 2 embeddings y 2 LLM | Informe de benchmark: recall@5, aciertos con fuente, rechazos, tiempos y RAM | 🟨 |
| 3. API | 06–10/11 | FastAPI: consulta, salud, consultas no resueltas, cola de 1 generación, límites y registro | API documentada en `/docs` (OpenAPI) y probada con pytest | 🟨 |
| 4. Chat (widget) | 08–12/11 | React + TS + Vite: chat, fuentes, "no encontrado", ocupado, aviso de asistente; campus simulado | El chat funciona embebido en una página que simula el campus, en PC y celular | 🟨 |
| 5. Pruebas y ensayo PC3 | 12–16/11 | Set de preguntas, fuera de alcance, prompt injection, Ollama caído, concurrencia 1/3/5/9 | Informe de pruebas y demo ensayada | ⬜ |
| **Hito PC3** | **17/11** | Demo del MVP al ingeniero | MVP v1.0 aprobado o lista de observaciones | ⬜ |
| 6. Correcciones y servidor simulado | 18–22/11 | Observaciones de PC3; VM Ubuntu Server 24.04 con 4 vCPU y 8 GB, Nginx + TLS, systemd | MVP v1.1 corriendo en la VM y reiniciándose solo | ⬜ |
| 7. Despliegue en el CEE | 23/11–06/12 | Pruebas de carga en el equipo real, instalación, piloto, respaldo y manuales | Tutor operando en el CEE (o brecha documentada si TI no lo autoriza) | ⬜ |
| **Hito PC4** | **08/12** | Tutor implementado | Acta de implementación | ⬜ |
| 8. Cierre | 07–20/12 | Informe final y exposición | Informe + presentación | ⬜ |

## Detalle por fase

### Fase 0 – Preparación (01–02/11)

- [x] Revisar toda la documentación del zip (resumen y contradicciones: https://claude.ai/artifact/WAMTQ1e8uDt3MGEoSwouqc).
- [x] `CLAUDE.md`, `docs/ROADMAP.md`, `docs/PROYECTO_TUTOR_VIRTUAL.md`, `docs/ARQUITECTURA.md`, `docs/BITACORA.md`, `README.md`.
- [x] Documentos originales en `docs/referencia/`.
- [x] Crear el repo privado (G1B0Y/tutor-virtual-cee) y subir todo lo anterior.
- [x] Esqueleto: `backend/` (FastAPI con `/salud`), `frontend/` (widget + campus simulado), `infra/db/`. `ingesta/` y `benchmark/` se crean en sus fases.
- [x] `docker-compose.yml` local: PostgreSQL 18 + pgvector 0.8.6, Ollama 0.34.3, API. Puertos solo en 127.0.0.1; base y Ollama en una red interna.
- [ ] Descargar los modelos candidatos en Ollama y los de embeddings (pasa a la Fase 2).
- [x] README con la instalación en Windows (Docker Desktop + WSL2, Python, Node).
- [x] CI en GitHub Actions: pruebas del backend, build del frontend y validación del compose.

**Listo cuando:** en la PC de Alfredo, `docker compose up` levanta todo y `GET /salud` responde `ok` con el estado de la base y de Ollama.

### Fase 1 – Base de conocimiento (02–05/11) · RF-M05

- [x] Migraciones del modelo de datos (ver `docs/ARQUITECTURA.md`): documentos, versiones, fragmentos con embedding, FAQs, consultas no resueltas, eventos técnicos. Con 6 pruebas de integración (01/11).
- [x] Script `ingesta` (`python -m app.ingesta`): PDF con texto → extracción por página → fragmentos (~900 caracteres, solape de 1 oración) → embeddings locales → pgvector (01/11).
- [x] Metadatos por documento: curso, versión, fecha de vigencia y estado (vigente / retirado) — en la base y en `corpus.json` / opciones del script.
- [x] Reemplazar un documento retira del índice la versión anterior (`registrar_version` + vista `fragmentos_vigentes`).
- [x] Carga de FAQs desde un CSV (pregunta, respuesta, fuente). Excel queda para después si el CEE lo prefiere.
- [x] Rechazar PDFs sin texto extraíble (escaneados) con un mensaje claro.
- [x] Corpus de prueba mientras el CEE entrega el real: 4 PDF y 5 FAQs en `corpus/prueba/`, marcados "DOCUMENTO DE PRUEBA" (01/11). Falta llegar a 5+ PDF y probar el reemplazo con un archivo real.

**Listo cuando:** se cargan 5+ PDFs y un CSV de FAQs, se reemplaza uno y la base solo deja vigente la versión nueva.

### Fase 2 – RAG y benchmark (04–08/11) · RF-M02, RF-M03, RNF-M03, RNF-M04

- [x] Búsqueda por similitud en pgvector con índice HNSW (top-k = 4 por ahora, configurable).
- [x] Umbral de relevancia: por debajo, el bot se abstiene y orienta al canal humano (valor inicial 0.55; se calibra con el set de preguntas).
- [x] Prompt con instrucciones del sistema, fragmentos y pregunta separados (anti prompt injection).
- [x] Respuesta con fuente: nombre del documento y página.
- [x] Probar en la PC de Alfredo con los modelos reales y el corpus de prueba (01/11: 7 preguntas; ver bitácora). Falta repetir con los arreglos del prompt.
- [ ] Set de **30 preguntas** con respuesta esperada: 20 dentro del corpus, 10 fuera de alcance (trámites, matrícula, temas ajenos).
- [ ] Benchmark reproducible: **≥2 modelos de embeddings** y **≥2 LLM**; medir recall@5, aciertos con fuente, rechazos correctos, tiempo al primer token, tiempo total y RAM.
- [ ] Elegir modelos y fijar sus versiones; verificar licencias en la ficha oficial (RNF-23).

**Listo cuando:** recall@5 ≥ 80 % y hay un informe con los modelos elegidos y por qué.

### Fase 3 – API (06–10/11) · RF-M04, RF-M06, RF-M07, RNF-M02, RNF-M05

- [x] `POST /consulta` → respuesta, fuentes y estado (`respondida`, `faq`, `sin_evidencia`, `sin_llm`, `ocupado`). Falta el id de conversación y el token de sesión.
- [x] `GET /salud` (API, base y Ollama; avisa si falta descargar el modelo).
- [ ] `POST /consultas-pendientes` para dejar una consulta a atención diferida (mínimos datos) y listado para el CEE (protegido).
- [x] Cola con **una generación activa**, cola de 3, timeout y aviso de "sistema ocupado".
- [ ] Límite de solicitudes por usuario y por minuto.
- [x] FAQs sin LLM cuando la pregunta coincide con una FAQ; con Ollama caído, el fragmento más cercano con su fuente.
- [x] Registro de tiempos y estado de cada consulta en `eventos`, sin el texto de la pregunta. Falta el registro de errores.
- [x] Validación de entradas (2 a 500 caracteres) con Pydantic; pruebas con pytest.

**Listo cuando:** la documentación OpenAPI está completa y las pruebas pasan, incluida la de Ollama apagado.

### Fase 4 – Chat (08–12/11) · RF-M01, RNF-13, RNF-24 a 26

- [x] Widget de chat en React + TypeScript + Vite (botón flotante que abre el panel). Falta empaquetarlo para embeberlo en otra página.
- [x] Mensajes con fuentes, estado "no encontré información" con el canal humano, "sistema ocupado" y error claro si el bot no responde.
- [x] Aviso visible: "asistente automatizado, puede equivocarse".
- [ ] Mobile-first (desde 360 px), navegación por teclado y contraste legible.
- [ ] **Campus simulado:** página HTML que embebe el widget y le pasa un token de sesión de prueba, hasta que el Grupo 3 defina la integración real.
- [x] Si la API cae, el campus simulado sigue funcionando (RNF-03).

**Listo cuando:** se conversa desde el celular por la red local y desde la PC, dentro del campus simulado.

### Fase 5 – Pruebas y ensayo de PC3 (12–16/11)

- [ ] Correr el set de 30 preguntas sobre el sistema completo: ≥ 85 % correctas con fuente y 100 % de rechazos correctos.
- [ ] Pruebas de prompt injection y entradas inválidas.
- [ ] Apagar Ollama y la API durante la prueba y comprobar los mensajes del chat.
- [ ] Concurrencia 1, 3, 5 y 9 solicitudes (k6 o Locust) con la cola y los tiempos de espera.
- [ ] Informe de pruebas y guion de la demo.

### Fase 6 – Correcciones y servidor simulado (18–22/11)

- [ ] Levantar las observaciones de PC3.
- [ ] VM con Ubuntu Server 24.04, 4 vCPU, 8 GB de RAM, sin GPU (igual al equipo del CEE).
- [ ] Nginx como proxy con HTTPS (mkcert en local) y solo el puerto 443 abierto; Postgres y Ollama en la red interna.
- [ ] systemd + `restart: unless-stopped`: reiniciar la VM y comprobar que el chat vuelve solo.

### Fase 7 – Despliegue en el CEE (23/11–06/12)

- [ ] Pruebas de carga en el equipo real (latencia, RAM, límite seguro de concurrencia).
- [ ] Instalación según lo que autorice TI (Ubuntu o plan B en Windows).
- [ ] Respaldo de PostgreSQL y documentos con restauración probada.
- [ ] Piloto con horario definido (meta ≥ 95 % de disponibilidad del horario).
- [ ] Manuales: uso, actualización de la base de conocimiento, respaldo y restauración.

## Segunda iteración (fuera del MVP)

Memoria conversacional extensa, streaming, explicaciones avanzadas, cuestionarios, valoración de respuestas, historial persistente, personalización por matrícula, verificación automática tras la carga, indicadores de uso y pantalla de administración. Se retoman solo si el benchmark y el tiempo lo permiten.

## Riesgos que pueden mover el plan

| Riesgo | Efecto | Qué hacemos |
| --- | --- | --- |
| TI no autoriza Ubuntu en el equipo del CEE | Fase 7 bloqueada | Plan B: Docker Desktop + WSL2 sobre Windows, o piloto en otro equipo, documentado como brecha |
| El CEE no entrega el corpus real a tiempo | Benchmark con datos de prueba | Corpus de prueba marcado; se reemplaza al llegar el real |
| El LLM es muy lento en CPU | Respuestas de más de 30 s | Modelo más pequeño, menos contexto, FAQs sin LLM y cola |
| El Grupo 3 no define la integración con el campus | Sin sesión real | Campus simulado con token de prueba; acta de integración pendiente |
| 8 GB de RAM no alcanzan para todo el stack | Caídas o swap | Medir en la Fase 2 y limitar memoria por contenedor |
