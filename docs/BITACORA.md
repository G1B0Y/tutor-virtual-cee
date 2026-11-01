# Bitácora del proyecto

Una entrada por sesión de trabajo, de la más reciente a la más antigua. El estado actual siempre está en `CLAUDE.md` y el plan en `docs/ROADMAP.md`; aquí queda el historial.

## 01/11/2026

- Alfredo compartió el zip "DOCUMENTACION-BOTVIRTUALCEE" (8 archivos: Gantt, ficha técnica, matriz de riesgos, requerimientos MVP, informe de investigación v1 y v2, informe de viabilidad del CEE y requerimientos funcionales y no funcionales). Se revisó todo y se dejó un resumen con las contradicciones y los puntos faltantes: https://claude.ai/artifact/WAMTQ1e8uDt3MGEoSwouqc
- Hallazgos principales: el equipo del CEE tiene Windows 10 (el stack asume Ubuntu y TI no autorizó migrar); no hay resultados del benchmark; no está definida la integración de sesión con el campus del Grupo 3; el Gantt sigue con "8 funcionalidades" de la v1 mientras el MVP ajustado tiene 7 requisitos.
- Alfredo preguntó cómo simular el servidor. Recomendación: VM con Ubuntu Server 24.04 (4 vCPU, 8 GB, sin GPU), campus simulado, HTTPS con mkcert y pruebas de carga con k6 o Locust.
- **Decisión:** por el plazo (avance a presentar hoy a las 6 p. m.), se desarrolla en local en la PC de Alfredo; la VM y el CEE vienen después de PC3.
- Se definió la forma de trabajo igual que en el proyecto Huarón: `CLAUDE.md` (estado actual), `docs/ROADMAP.md` (plan por fases), `docs/PROYECTO_TUTOR_VIRTUAL.md` (contexto), `docs/ARQUITECTURA.md`, `docs/BITACORA.md` y `README.md`. Documentos originales en `docs/referencia/`.
- Roadmap: Fase 0 preparación (01–02/11), 1 base de conocimiento (02–05/11), 2 RAG y benchmark (04–08/11), 3 API (06–10/11), 4 chat (08–12/11), 5 pruebas (12–16/11), PC3 17/11, 6 correcciones y VM (18–22/11), 7 despliegue en el CEE (23/11–06/12), PC4 08/12.
- Repo privado creado por Alfredo (`G1B0Y/tutor-virtual-cee`); primer commit con los documentos base en `main`.
- **Fase 0 hecha.** `docker-compose.yml` en la raíz con PostgreSQL 18 + pgvector 0.8.6, Ollama 0.34.3 (una generación, un modelo cargado) y la API; puertos solo en 127.0.0.1 y red interna para la base y Ollama. Backend FastAPI con `GET /salud` (base, pgvector y Ollama; `degradado` si algo falla) y 3 pruebas con pytest. Frontend React + TS + Vite: widget flotante dentro de un campus simulado, con aviso de asistente automatizado y estado de conexión; probado en PC y celular (375 px), con la API arriba ("Disponible") y apagada ("El tutor no está disponible", el campus sigue funcionando). CI en GitHub Actions (pytest, build del frontend y `docker compose config`). README con la instalación en Windows.
- Pendiente: Fase 1 (modelo de datos, ingesta de PDFs y FAQs).
