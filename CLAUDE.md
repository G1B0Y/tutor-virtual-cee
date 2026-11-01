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
- **Rama principal:** `main`. Repo privado: https://github.com/G1B0Y/tutor-virtual-cee

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

- **01/11/2026:** documentación del zip revisada (resumen y contradicciones en https://claude.ai/artifact/WAMTQ1e8uDt3MGEoSwouqc). Roadmap y documentos base escritos y subidos al repo `G1B0Y/tutor-virtual-cee`. **Fase 0 en curso:** falta el esqueleto y el `docker-compose.yml`.
- Según el Gantt original, el benchmark (12–25/10) y el RAG (19/10–01/11) ya deberían estar hechos, pero no hay resultados ni código: el roadmap los reprograma para 04–08/11.

## Pendientes

- [ ] Esqueleto del proyecto y `docker-compose.yml` local (Fase 0).
- [ ] Confirmar con el equipo si hay resultados del benchmark o preguntas del CEE ya escritas.
- [ ] Pedir al CEE el corpus inicial (temarios, separatas, FAQs) y quién es el responsable de la base de conocimiento.
- [ ] Pedir al CEE el horario y los datos del canal humano (para el mensaje de derivación).
- [ ] Acordar con el Grupo 3 cómo se integra el chat al campus (widget, sesión, token).
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

## Notas para desarrollar

- Equipo del CEE: HP ProDesk 600 G1, i5-4590 (4 núcleos), 8 GB DDR3 (~4 GB libres), sin GPU, SSD 447 GB, Windows 10 Pro. Todo el stack debe caber en ~4 GB.
- Candidatos de LLM: `qwen2.5:1.5b` (Apache 2.0) y un segundo modelo de ~3B. **Ojo:** Qwen2.5 3B tiene la licencia "Qwen Research", no Apache: verificar si permite el uso institucional antes de elegirlo.
- Candidatos de embeddings: modelos multilingües pequeños de Sentence Transformers (p. ej. `paraphrase-multilingual-MiniLM-L12-v2`, `intfloat/multilingual-e5-small`). Verificar licencia y dimensión del vector antes de crear la columna.
- pgvector en Docker: imagen oficial `pgvector/pgvector` con la versión de PostgreSQL fijada.
- Similitud: operador de distancia coseno de pgvector e índice HNSW; las consultas se escriben a mano (no hay cliente de alto nivel).
