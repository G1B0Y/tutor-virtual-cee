# Tutor Virtual 24/7 CEE – contexto para sesiones de desarrollo

Chatbot RAG en español que responde 24/7 las consultas académicas de los alumnos del **CEE FIIS-UNI** usando solo documentos validados por el CEE, y que deriva al personal humano lo que no puede responder. Proyecto del **Grupo 5** del curso Sistemas Integrados Empresariales (UNI).

- Contexto completo: `docs/PROYECTO_TUTOR_VIRTUAL.md` (léelo antes de cualquier cambio importante).
- Plan por fases y fechas: `docs/ROADMAP.md`.
- Arquitectura, stack y modelo de datos: `docs/ARQUITECTURA.md`.
- Historial de sesiones y decisiones: `docs/BITACORA.md`.
- Documentos originales del curso y del CEE: `docs/referencia/`.

## Cómo trabajar en este repo (cualquier sesión: nube o VS Code)

Las sesiones (Claude Code en la nube y en VS Code) **no comparten el historial del chat**. Este archivo, `docs/ROADMAP.md` y `docs/BITACORA.md` son la única memoria compartida.

- **Al empezar:** trae lo último (`git pull` en la rama de trabajo) y lee este archivo, el roadmap y las últimas entradas de la bitácora.
- **Al terminar cada interacción en la que cambie algo** (código, decisión, pendiente o respuesta del CEE/TI):
  1. Actualiza este archivo: "Estado", "Pendientes", "Decisiones" y "Notas para desarrollar". Debe reflejar siempre la situación actual, no la historia.
  2. Marca en `docs/ROADMAP.md` las tareas hechas y el estado de la fase.
  3. Agrega una entrada breve y fechada en `docs/BITACORA.md` (qué se hizo, qué se decidió, qué queda pendiente).
  4. Haz commit y push.
- **Rama principal:** `main`. Cada fase se trabaja en una rama `claude/...` y entra a `main` por PR. Repo privado: https://github.com/G1B0Y/tutor-virtual-cee

## Equipo

- Alfredo Coasaca: tecnología (backend, RAG, infraestructura). Es quien trabaja con Claude.
- Anyela Wurttele: gestión y liderazgo.
- Fernando Chirinos y Leonardo Mendoza: análisis, diseño e interfaz.
- Ingeniero / TI del CEE: Sr. César Dionicio.

## Reglas obligatorias

- **Costo incremental S/ 0:** nada de nube, APIs de IA de pago, hosting, dominios nuevos ni compra de hardware. Si algo exige pago o tarjeta, detenerse y consultar. Si el equipo no alcanza, se reduce el alcance.
- **Procesamiento 100 % local:** prohibidos Ollama Cloud, Chroma Cloud y cualquier fallback a servicios de IA en la nube. Ollama sin salida a internet en producción.
- **El tutor responde solo con la base de conocimiento validada.** Sin evidencia suficiente, se abstiene y orienta al canal humano; nunca inventa.
- Modelos (LLM y embeddings) solo con licencia que permita uso institucional sin costo, verificada en su ficha oficial.
- Interfaz en español; zona horaria America/Lima; fechas DD/MM/AAAA.
- Chat responsivo (desde 360 px), mobile-first.
- Ninguna credencial en el repo: variables de entorno (`.env`, con `.env.example` sin valores reales).
- Mínimos datos personales (Ley N.º 29733); no guardar conversaciones más de lo necesario.
- Commits pequeños y descriptivos, en español.
- Cada error corregido llega con una prueba nueva.
- **Entornos:** local (PC de Alfredo) → servidor simulado (VM) → equipo del CEE. Nada llega al CEE sin pasar por los dos primeros.

## Estado

- **01/11/2026:** documentación del zip revisada (resumen y contradicciones en https://claude.ai/artifact/WAMTQ1e8uDt3MGEoSwouqc). Roadmap y documentos base escritos y subidos al repo `G1B0Y/tutor-virtual-cee`. **Fase 0 hecha (01/11/2026):** `docker compose up -d --build` levanta PostgreSQL 18 + pgvector, Ollama y la API; `GET /salud` revisa la base y Ollama (3 pruebas con pytest). Widget React dentro del campus simulado (`frontend/`, `npm run dev`) que muestra si el tutor está disponible; probado con la API apagada. CI en GitHub Actions. **Fase 1 en curso:** tablas creadas (01/11/2026, `infra/db/002_base_conocimiento.sql`: documentos, versiones, fragmentos, FAQs, consultas pendientes, eventos; vista `fragmentos_vigentes`; función `registrar_version`) con 6 pruebas de integración. Ingesta y corpus de prueba hechos (rama `claude/primera-respuesta`).
- **Primera respuesta de punta a punta (01/11/2026, pedido de Alfredo: "documentos de prueba para ver cómo responde el bot"):** corpus ficticio en `corpus/prueba/` (4 PDF marcados "DOCUMENTO DE PRUEBA" + 5 FAQs); `python -m app.ingesta` (PDF por página → fragmentos de ~900 caracteres → embeddings → pgvector; FAQs desde CSV; rechaza PDF sin texto; no duplica si el archivo no cambió); `POST /consulta` (FAQ → búsqueda con umbral → Ollama → respuesta con fuentes, o abstención que queda en `consultas_pendientes`; una generación a la vez + cola de 3; si Ollama falla, muestra el fragmento más cercano); el chat muestra respuestas, fuentes (documento y página) y los estados. 29 pruebas (13 unitarias + 16 con la base). Probado en la nube de desarrollo con embeddings "hash" y sin modelo (estados faq y sin_llm): **la calidad real se ve recién en la PC de Alfredo**, con `qwen2.5:1.5b` y el modelo de embeddings descargados.
- **Primera prueba real en la PC de Alfredo (01/11/2026):** `/salud` ok; de 7 preguntas, la FAQ (0,07 s), inventario de seguridad, horas del programa y EOQ correctas con fuente (11–23 s con el modelo cargado); el mundial y "ignora tus instrucciones" se abstienen. Defectos encontrados y corregidos el mismo día: dos ingestas a la vez duplicaban documentos (candado), la primera pregunta tras arrancar se pasaba del timeout porque cargar el modelo tardó ~4 min (precarga + `OLLAMA_KEEP_ALIVE=-1`), el modelo agregaba explicaciones propias y escribía LaTeX (reglas 6 y 7 del prompt + `limpiar_respuesta`) y citaba fuentes de más (`margen_fuentes`). Vite solo escuchaba en IPv6 (::1): ahora `host: "127.0.0.1"`. Segunda prueba (01/11 noche): precarga y `margen_fuentes` funcionan (horas del programa cita solo el temario), pero la PC se quedó sin RAM (1,1 GB libres) y el modelo no cargó; además se corrigieron la carga triple del modelo de embeddings y el logger sin handler. Falta repetir con RAM libre.
- **Integración con el Campus (03/11/2026):** el Grupo 3 compartió su documentación (`docs/referencia/grupo3/`): Moodle 5.3 LTS en Windows (Apache 2.4 + mod_fcgid, PHP 8.3, PostgreSQL 18), una sola PC del CEE/UNI, tema `theme_cee`, roles estándar. Propuesta del Grupo 5 en `docs/INTEGRACION_CAMPUS.md`: sin tablas nuevas en Moodle; Fase 1 (PC3) = widget por "HTML adicional"; Fase 2 = plugin `local_tutorcee` con token HMAC (id opaco, rol, shortnames de cursos). Pendiente de respuesta del Grupo 3.
- Ramas por unir, en orden: PR #1 (Fase 0) → PR #2 (tablas) → PR #3 (primera respuesta).
- Según el Gantt original, el benchmark (12–25/10) y el RAG (19/10–01/11) ya deberían estar hechos, pero no hay resultados ni código: el roadmap los reprograma para 04–08/11.

## Pendientes

- [ ] Que Alfredo pruebe en su PC la primera respuesta (README, pasos 3 a 6: `ollama pull qwen2.5:1.5b`, `python -m app.ingesta corpus /corpus/prueba`, preguntar en el chat) y una PR #1 → #2 → #3.
- [ ] Alfredo: `git pull` en `claude/primera-respuesta`, `docker compose up -d --build` y volver a probar las preguntas (sobre todo Lean Six Sigma unidad 3, horas del programa y EOQ).
- [ ] Calibrar `umbral_distancia` (0.55), `umbral_faq` (0.25) y `margen_fuentes` (0.10) con el set de 30 preguntas (Fase 2): hoy son valores iniciales.
- [ ] Confirmar con el equipo si hay resultados del benchmark o preguntas del CEE ya escritas.
- [ ] Pedir al CEE el corpus inicial (temarios, separatas, FAQs) y quién es el responsable de la base de conocimiento.
- [ ] Pedir al CEE el horario y los datos del canal humano (para el mensaje de derivación).
- [ ] Acordar con el Grupo 3 (Gavino Geldres) la propuesta de `docs/INTEGRACION_CAMPUS.md`: ¿misma PC que Moodle? (8 GB no alcanzan para ambos con holgura), URL del campus, "HTML adicional" para PC3, `shortname` de los cursos.
- [ ] Empaquetar el widget como un solo `tutor-cee.js` embebible (hoy es una app de Vite).
- [ ] TI: autorización para pasar el equipo del CEE de Windows 10 a Ubuntu Server, acceso externo, HTTPS, UPS y respaldos.
- [ ] Política de retención de datos con TI/CEE.
- [ ] Alinear el Gantt con el MVP ajustado: dice "8 de 8 funcionalidades" y el MVP tiene 7 requisitos.
- [ ] Conseguir los entregables de PC2 (BPMN, diagramas de flujo, casos de uso, modelo ER, prototipo) si existen.

## Stack (definido en el Informe v2, 04/10/2026)

- **Frontend:** React + TypeScript + Vite (widget embebible).
- **Backend:** Python + FastAPI + Pydantic. Monolito modular, RAG propio, sin frameworks de agentes.
- **Datos y vectores:** PostgreSQL + pgvector (un solo motor).
- **Embeddings:** Sentence Transformers local, modelo multilingüe elegido por benchmark.
- **LLM:** Ollama local; modelo pequeño cuantizado elegido por benchmark.
- **Infraestructura:** Docker Engine + Compose, Nginx (proxy y TLS), systemd, Ubuntu Server 24.04 LTS, Git/GitHub.
- En local (Windows): Docker Desktop con WSL2.

## Decisiones tomadas

- Alcance = **MVP ajustado del 11/10/2026** (RF-M01 a M07, RNF-M01 a M07). Lo demás va a una segunda iteración.
- Una sola generación LLM activa con cola corta; capacidad real definida por medición, no por suposición.
- El 99 % de disponibilidad es meta, no compromiso; 24/7 del equipo no equivale a 24/7 del servicio.
- Cloudflare Tunnel eliminado; acceso por red interna o subdominio institucional existente.
- **01/11/2026:** se desarrolla en la PC de Alfredo hasta PC3; luego se ensaya en una VM igual al equipo del CEE (4 vCPU, 8 GB, sin GPU) y recién después en el CEE.
- **01/11/2026:** mientras el Grupo 3 no defina la integración, el chat se prueba dentro de un **campus simulado** con un token de sesión de prueba.
- **01/11/2026:** el Grupo 5 hace solo el tutor (widget + backend); el Campus Virtual es del Grupo 3.
- **01/11/2026:** el bot responde con estos estados: `respondida`, `faq` (sin LLM), `sin_evidencia` (se abstiene y registra la consulta), `sin_llm` (Ollama caído: muestra el fragmento más cercano con su fuente) y `ocupado` (cola llena). Las FAQs se responden antes de buscar en los documentos.
- **01/11/2026:** el prompt separa instrucciones, `<documentos>` y `<pregunta_del_alumno>`; el modelo debe contestar `SIN_EVIDENCIA` si los documentos no lo cubren (y entonces la API se abstiene). Defensa básica contra prompt injection.
- **01/11/2026:** modelos iniciales (mientras no haya benchmark): LLM `qwen2.5:1.5b`, embeddings `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensiones).
- **01/11/2026:** hasta que el CEE entregue el real, se usa un corpus ficticio con el aviso "DOCUMENTO DE PRUEBA" en cada página.
- **01/11/2026 (logo enviado por Alfredo):** el chat lleva la marca del CEE: rojo `#870c0e` (cabecera, botón, Enviar), negro `#141414` y gris `#747273`; el símbolo "C" del logo en el botón flotante y en la cabecera. Logos originales en `docs/referencia/marca/`.

## Notas para desarrollar

- Equipo del CEE: HP ProDesk 600 G1, i5-4590 (4 núcleos), 8 GB DDR3 (~4 GB libres), sin GPU, SSD 447 GB, Windows 10 Pro. Todo el stack debe caber en ~4 GB.
- Candidatos de LLM: `qwen2.5:1.5b` (Apache 2.0) y un segundo modelo de ~3B. **Ojo:** Qwen2.5 3B tiene la licencia "Qwen Research", no Apache: verificar si permite el uso institucional antes de elegirlo.
- Candidatos de embeddings: modelos multilingües pequeños de Sentence Transformers (p. ej. `paraphrase-multilingual-MiniLM-L12-v2`, `intfloat/multilingual-e5-small`). Verificar licencia y dimensión del vector antes de crear la columna.
- pgvector en Docker: imagen oficial `pgvector/pgvector` con la versión de PostgreSQL fijada.
- Similitud: operador de distancia coseno de pgvector e índice HNSW; las consultas se escriben a mano (no hay cliente de alto nivel).
- Versiones fijadas (01/11/2026): FastAPI 0.162.0, Uvicorn 0.54.0, psycopg 3.3.6, pydantic-settings 2.16.2, pytest 9.2.0; imagen de la API `python:3.12-slim`; `pgvector/pgvector:0.8.6-pg18`; `ollama/ollama:0.34.3`; React 19.3.1, Vite 8.3.4, TypeScript 7.0.2. Al actualizar, elegir versiones con al menos dos semanas de publicadas.
- `docker-compose.yml` está en la raíz y lee `.env` solo. Ollama corre con `OLLAMA_NUM_PARALLEL=1` y `OLLAMA_MAX_LOADED_MODELS=1`. La red `interna` es `internal: true`; Ollama y la API también están en `descarga` solo para el entorno local (Ollama baja modelos). En el servidor se quita `descarga` de Ollama.
- Puertos de la PC configurables en `.env`: `PUERTO_DB` (5432), `PUERTO_OLLAMA` (11434), `PUERTO_API` (8000). Dentro de Docker no cambian. En la PC de Alfredo hay un Ollama de Windows que ocupa el 11434 (01/11/2026).
- `.gitattributes` marca PDF, imágenes y Office como binarios: los PDF de reportlab no tienen bytes nulos y Git en Windows (autocrlf) les cambiaba los saltos de línea (pypdf avisaba "incorrect startxref pointer"). Prueba en `test_rag_unidad.py`.
- PostgreSQL 18 guarda los datos en `/var/lib/postgresql` (no en `/var/lib/postgresql/data` como las versiones anteriores).
- `infra/db/*.sql` solo corre al crear el volumen por primera vez; para repetirlo: `docker compose down -v`. Mientras no haya datos reales está bien; antes de cargar el corpus real hay que pasar a migraciones que se apliquen sobre una base existente.
- Docker **no publica puertos** de un contenedor que solo está en una red `internal: true`: por eso en local la base también va en la red `descarga` (si no, el 5432 no responde desde la PC). En el servidor se quita.
- Pruebas de integración: `backend/tests/integracion/` (se saltan si no hay `TEST_DATABASE_URL`; cada prueba en una transacción que se deshace). El CI levanta la base con `docker compose up -d --wait db` y las corre.
- Embeddings de 384 dimensiones (`vector(384)`) por los dos modelos candidatos.
- `/salud` siempre responde 200 si la API vive; `estado: degradado` cuando falla la base u Ollama (el chat lo usa para avisar).
- En la nube de desarrollo de Claude, `docker build` necesita el certificado del proxy: la imagen de la API se construye aparte con `--network host` y `PIP_CERT`, y se levanta con `docker compose up -d --no-build`. En la PC del usuario no hace falta.
- **RAG (`backend/app/rag/`):** `embeddings.py` (`crear_embeddings(proveedor, modelo)`: `sentence-transformers` real o `hash` solo para pruebas/CI, sin descargas; prefijos "query:"/"passage:" si el modelo es e5), `fragmentar.py` (por página, oraciones, máx. 900 caracteres, solape de 1 oración, nunca cruza páginas), `busqueda.py` (`fragmentos_vigentes` ordenado por `<=>`; FAQs activas), `prompt.py`, `llm.py` (`LLMOllama`, `/api/chat` sin streaming, temperatura 0.1, `num_ctx` 4096; 404 = modelo no descargado). Flujo en `app/consulta.py` (`responder`, `Turno` con semáforos: 1 generación + cola). Cada consulta deja una fila en `eventos` (sin el texto de la pregunta).
- Umbrales en `app/config.py` (variables de entorno): `UMBRAL_DISTANCIA` 0.55, `UMBRAL_FAQ` 0.25, `MARGEN_FUENTES` 0.10 (`seleccionar` en `consulta.py`: solo fragmentos hasta mejor distancia + margen; son los que van al modelo y se citan), `PRECARGAR_LLM` true (al arrancar la API, un hilo carga primero el modelo de embeddings y luego llama `/api/generate` sin prompt; Ollama con `OLLAMA_KEEP_ALIVE=-1` no lo descarga), `FRAGMENTOS_POR_CONSULTA` 4, `COLA_MAXIMA` 3, `TIMEOUT_LLM` 120 s, `MENSAJE_DERIVACION`.
- Ingesta: `cargar_documento` toma `pg_advisory_xact_lock(hashtext('ingesta:' || titulo))` antes de buscar el documento (dos ingestas a la vez duplicaban documentos; prueba con dos conexiones reales en `test_ingesta_concurrente.py`).
- `crear_embeddings` guarda un modelo por proceso con un candado (`_cache` + `_candado_cache`): sin él, varias consultas al arrancar cargaban cada una su copia. El logger `tutor` de `main.py` tiene su propio handler (si no, los INFO no salían en `docker compose logs api`).
- RAM en la PC de Alfredo: con 1 GB libre, Docker manda el modelo a disco y Ollama no termina de cargarlo ("Load failed", todo en sin_llm). Para probar: cerrar apps pesadas y apagar el Supabase de Huarón (`npx supabase stop`). El benchmark debe medir RAM.
- Respuestas del modelo: `limpiar_respuesta` (`prompt.py`) convierte LaTeX (\\[ \\frac \\sqrt \\times…) a texto simple.
- Frontend: Vite con `host: "127.0.0.1"` (en Windows `localhost` quedaba solo en ::1); CORS acepta `localhost:5173` y `127.0.0.1:5173`.
- Ingesta: `python -m app.ingesta corpus <dir>` lee `corpus.json` (título, tipo, curso por archivo + `faqs.csv`); también `documento`, `faqs` y `estado`. Hash SHA-256 del archivo: si el vigente es igual, se salta.
- Dependencias de ML aparte en `backend/requirements-ml.txt` (torch CPU desde download.pytorch.org + sentence-transformers); el Dockerfile las instala si `INCLUIR_ML=si` (por defecto). El CI no las instala: las pruebas usan embeddings "hash" y un LLM falso.
- El modelo de embeddings se descarga la primera vez al volumen `modelos_embeddings` (`/root/.cache/huggingface`); el corpus se monta en `/corpus` (solo lectura).
- En la nube de desarrollo de Claude están bloqueados huggingface.co, registry.ollama.ai y download.pytorch.org: ahí no se pueden probar los modelos reales (usar `EMBEDDINGS_PROVEEDOR=hash` y la imagen con `INCLUIR_ML=no`). Nunca presentar esas respuestas como calidad del bot.
- Marca: `frontend/public/marca/cee-simbolo.png` (192 px, recortado del logo de fondo rojo, solo la "C" sin texto). Colores como variables `--cee-*` en `frontend/src/estilos.css`; usar esas variables, no colores sueltos.
