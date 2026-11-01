# Tutor Virtual 24/7 – Arquitectura, stack y modelo de datos

Propuesta inicial (01/11/2026), sobre el stack definido en el Informe v2. Se ajusta con los resultados del benchmark (Fase 2).

## Arquitectura general

```
Alumno (navegador, PC o celular)
  └─ Campus Virtual (Grupo 3) ── widget React + TS
        └─ Nginx (proxy, HTTPS, límite de solicitudes)
              └─ FastAPI (monolito modular)
                    ├─ FAQs ─────────────── respuesta directa sin LLM
                    ├─ Embeddings (Sentence Transformers, local)
                    ├─ PostgreSQL + pgvector ── búsqueda top-5 + umbral
                    │      └─ sin evidencia → abstención + consulta pendiente
                    └─ Ollama (LLM local, 1 generación activa, cola corta)
```

Todo corre en contenedores con Docker Compose. Solo Nginx se publica; PostgreSQL y Ollama quedan en la red interna. En producción, systemd levanta Compose al arrancar el equipo.

## Flujo de una consulta

1. El widget envía la pregunta, el id de conversación y el token de sesión.
2. La API valida la entrada (longitud, formato) y el límite por usuario.
3. Si coincide con una FAQ, responde sin LLM.
4. Calcula el embedding y busca los 5 fragmentos más cercanos entre los documentos **vigentes**.
5. Si el mejor puntaje está bajo el umbral → `sin_evidencia`: mensaje con el canal humano y opción de dejar la consulta.
6. Si hay evidencia → prompt con tres partes separadas (instrucciones, fragmentos, pregunta) → Ollama, con cola de una generación y timeout.
7. Responde con el texto y las fuentes (documento y página); registra tiempos y estado.

## Estructura del repositorio

```
backend/        FastAPI: app/, rag/, api/, tests/
ingesta/        script de carga de PDFs y FAQs
benchmark/      set de preguntas, scripts y resultados
frontend/       widget React + TS + Vite y campus simulado
infra/          docker-compose.yml, Nginx, systemd, scripts de respaldo
docs/           CLAUDE.md complementa: ROADMAP, PROYECTO, ARQUITECTURA, BITACORA, referencia/
```

## Modelo de datos (borrador)

| Tabla | Campos principales | Notas |
| --- | --- | --- |
| `documentos` | id, titulo, curso, tipo (separata, temario, manual, faq), creado_en | Un documento lógico |
| `versiones_documento` | id, documento_id, version, archivo, hash, vigente_desde, estado (vigente / retirado) | Al cargar una nueva, la anterior pasa a retirado |
| `fragmentos` | id, version_id, pagina, orden, texto, embedding `vector(n)` | `n` según el modelo de embeddings elegido; índice HNSW coseno |
| `faqs` | id, pregunta, respuesta, fuente, activa, embedding `vector(n)` | Respuesta directa sin LLM |
| `consultas_pendientes` | id, pregunta, motivo (sin_evidencia, fuera_de_alcance, error), contacto opcional, creada_en, atendida | Mínimos datos; retención por definir |
| `eventos` | id, tipo, estado, ms_total, ms_primer_token, modelo, creado_en | Sin texto de la pregunta ni datos personales |

La búsqueda filtra siempre por `versiones_documento.estado = 'vigente'`.

## Entornos

| Entorno | Dónde | Para qué |
| --- | --- | --- |
| Local | PC de Alfredo (Windows + Docker Desktop/WSL2) | Desarrollo hasta PC3 |
| Servidor simulado | VM Ubuntu Server 24.04, 4 vCPU, 8 GB, sin GPU | Ensayo del despliegue real (Fase 6) |
| CEE | HP ProDesk 600 G1 | Piloto y producción (Fase 7, sujeto a TI) |

## Decisiones pendientes

- Modelos de LLM y embeddings (Fase 2).
- Umbral de relevancia (Fase 2, con el set de preguntas).
- Mecanismo de sesión con el campus (Grupo 3).
- Sistema operativo del equipo del CEE (TI).
