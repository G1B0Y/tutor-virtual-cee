# Tutor Virtual 24/7 – Roadmap

Plan de trabajo del MVP del Tutor Virtual del CEE FIIS-UNI (Grupo 5). Se desarrolla **en local (PC de Alfredo)** hasta la demo de PC3 y recién después se ensaya en un servidor simulado y en el equipo del CEE. Cada fase termina con algo que se puede ver y probar.

- Alcance: el **MVP ajustado del 11/10/2026** (RF-M01 a RF-M07, RNF-M01 a RNF-M07). Ver `docs/PROYECTO_TUTOR_VIRTUAL.md`.
- Fechas fijas del curso: **PC3 (MVP validado) 17/11/2026**, **PC4 (tutor implementado) 08/12/2026**, informe y exposición final 14–20/12/2026.
- Estado de cada fase: ⬜ por hacer · 🟨 en curso · ✅ hecha. El estado actual también va en `CLAUDE.md`.

## Resumen

| Fase | Fechas | Contenido | Entregable que se revisa | Estado |
| --- | --- | --- | --- | --- |
| 0. Preparación | 01–02/11 | Repo, documentos base, esqueleto y entorno local con Docker | `docker compose up` levanta PostgreSQL + pgvector y Ollama; la API responde `/salud` | 🟨 |
| 1. Base de conocimiento | 02–05/11 | Modelo de datos, script de ingesta de PDFs y FAQs, vigencia y retiro | Cargar un corpus de prueba y ver documentos, versiones y fragmentos en la base | ⬜ |
| 2. RAG y benchmark | 04–08/11 | Búsqueda por similitud, umbral de rechazo, set de 30 preguntas, comparación de 2 embeddings y 2 LLM | Informe de benchmark: recall@5, aciertos con fuente, rechazos, tiempos y RAM | ⬜ |
| 3. API | 06–10/11 | FastAPI: consulta, salud, consultas no resueltas, cola de 1 generación, límites y registro | API documentada en `/docs` (OpenAPI) y probada con pytest | ⬜ |
| 4. Chat (widget) | 08–12/11 | React + TS + Vite: chat, fuentes, "no encontrado", ocupado, aviso de asistente; campus simulado | El chat funciona embebido en una página que simula el campus, en PC y celular | ⬜ |
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
- [ ] Esqueleto: `backend/` (FastAPI), `frontend/` (React + TS + Vite), `ingesta/`, `benchmark/`, `infra/`.
- [ ] `docker-compose.yml` local: PostgreSQL + pgvector, Ollama, API. Ollama sin puerto publicado hacia afuera y sin salida a internet en producción.
- [ ] Descargar los modelos candidatos en Ollama y los de embeddings.
- [ ] README con la instalación en Windows (Docker Desktop + WSL2, Python, Node).

**Listo cuando:** en la PC de Alfredo, `docker compose up` levanta todo y `GET /salud` responde `ok` con el estado de la base y de Ollama.

### Fase 1 – Base de conocimiento (02–05/11) · RF-M05

- [ ] Migraciones del modelo de datos (ver `docs/ARQUITECTURA.md`): documentos, versiones, fragmentos con embedding, FAQs, consultas no resueltas, eventos técnicos.
- [ ] Script `ingesta`: PDF con texto → extracción por página → fragmentos (~500 tokens con solapamiento) → embeddings locales → pgvector.
- [ ] Metadatos por documento: curso, versión, fecha de vigencia y estado (vigente / retirado).
- [ ] Reemplazar un documento retira del índice la versión anterior.
- [ ] Carga de FAQs desde un CSV/Excel (pregunta, respuesta, fuente).
- [ ] Rechazar PDFs sin texto extraíble (escaneados) con un mensaje claro.
- [ ] Corpus de prueba mientras el CEE entrega el real (temarios y separatas de ejemplo, marcados como "PRUEBA").

**Listo cuando:** se cargan 5+ PDFs y un CSV de FAQs, se reemplaza uno y la base solo deja vigente la versión nueva.

### Fase 2 – RAG y benchmark (04–08/11) · RF-M02, RF-M03, RNF-M03, RNF-M04

- [ ] Búsqueda por similitud en pgvector (top-k = 5) con índice HNSW.
- [ ] Umbral de relevancia: por debajo, el bot se abstiene y orienta al canal humano.
- [ ] Prompt con instrucciones del sistema, fragmentos y pregunta separados (anti prompt injection).
- [ ] Respuesta con fuente: nombre del documento y página.
- [ ] Set de **30 preguntas** con respuesta esperada: 20 dentro del corpus, 10 fuera de alcance (trámites, matrícula, temas ajenos).
- [ ] Benchmark reproducible: **≥2 modelos de embeddings** y **≥2 LLM**; medir recall@5, aciertos con fuente, rechazos correctos, tiempo al primer token, tiempo total y RAM.
- [ ] Elegir modelos y fijar sus versiones; verificar licencias en la ficha oficial (RNF-23).

**Listo cuando:** recall@5 ≥ 80 % y hay un informe con los modelos elegidos y por qué.

### Fase 3 – API (06–10/11) · RF-M04, RF-M06, RF-M07, RNF-M02, RNF-M05

- [ ] `POST /consulta` (pregunta + id de conversación) → respuesta, fuentes y estado (`respondida`, `sin_evidencia`, `fuera_de_alcance`, `ocupado`).
- [ ] `GET /salud` (API, base y Ollama).
- [ ] `POST /consultas-pendientes` para dejar una consulta a atención diferida (mínimos datos) y listado para el CEE (protegido).
- [ ] Cola con **una generación activa**, cola corta, timeout y aviso de "sistema ocupado".
- [ ] Límite de solicitudes por usuario y por minuto.
- [ ] FAQs sin LLM cuando la pregunta coincide con una FAQ o cuando Ollama está caído.
- [ ] Registro de errores, tiempos y eventos sin datos sensibles.
- [ ] Validación de entradas (longitud y formato) con Pydantic; pruebas con pytest.

**Listo cuando:** la documentación OpenAPI está completa y las pruebas pasan, incluida la de Ollama apagado.

### Fase 4 – Chat (08–12/11) · RF-M01, RNF-13, RNF-24 a 26

- [ ] Widget de chat en React + TypeScript + Vite, embebible (botón flotante que abre el panel).
- [ ] Mensajes con fuentes, estado "no encontré información" con el canal humano, "sistema ocupado" y error claro si el bot no responde.
- [ ] Aviso visible: "asistente automatizado, puede equivocarse".
- [ ] Mobile-first (desde 360 px), navegación por teclado y contraste legible.
- [ ] **Campus simulado:** página HTML que embebe el widget y le pasa un token de sesión de prueba, hasta que el Grupo 3 defina la integración real.
- [ ] Si la API cae, el campus simulado sigue funcionando (RNF-03).

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
