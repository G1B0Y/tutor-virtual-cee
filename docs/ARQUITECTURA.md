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

Implementado el 01/11/2026 en `backend/app/consulta.py` (sin id de conversación ni token todavía). Estados de la respuesta:

| Estado | Cuándo | Qué ve el alumno |
| --- | --- | --- |
| `faq` | La pregunta se parece a una FAQ (distancia ≤ 0.25) | La respuesta de la FAQ, al instante |
| `respondida` | Hay fragmentos cercanos (distancia ≤ 0.55) y el modelo contestó | Respuesta + fuentes (documento, página) |
| `sin_evidencia` | Nada cercano, o el modelo dijo `SIN_EVIDENCIA` | "No encontré esa información" + canal humano; se guarda en `consultas_pendientes` |
| `sin_llm` | Ollama caído o sin modelo | El fragmento más cercano con su fuente |
| `ocupado` | Ya hay 1 generando y 3 esperando | "Hay muchas consultas en este momento. Intenta de nuevo en un minuto." |

## Estructura del repositorio

```
docker-compose.yml   PostgreSQL + pgvector, Ollama y API (entorno local)
backend/             FastAPI: app/ (config, salud, consulta, ingesta, rag/), tests/
corpus/prueba/       documentos y FAQs ficticios para probar (marcados "DOCUMENTO DE PRUEBA")
scripts/             utilidades de desarrollo (generar el corpus de prueba)
benchmark/           set de preguntas, scripts y resultados (Fase 2)
frontend/            widget React + TS + Vite; index.html = campus simulado
infra/db/            SQL inicial de la base (extensión pgvector; migraciones desde la Fase 1)
infra/               más adelante: Nginx, systemd y respaldos (Fase 6)
docs/                ROADMAP, PROYECTO, ARQUITECTURA, BITACORA, referencia/
```

## Modelo de datos

Una sola base: PostgreSQL 18 + pgvector. SQL en `infra/db/002_base_conocimiento.sql` (01/11/2026).

| Tabla | Campos principales | Reglas |
| --- | --- | --- |
| `documentos` | id, titulo, curso, tipo (temario, separata, presentacion, manual, reglamento, otro), creado_en | Un documento lógico |
| `versiones_documento` | id, documento_id, version, archivo, hash_sha256, paginas, vigente_desde, estado (vigente / retirado), cargado_en, retirado_en | **Una sola vigente por documento** (índice único parcial). `retirado_en` obligatorio si está retirada |
| `fragmentos` | id, version_id, orden, pagina, texto, embedding `vector(384)` | Índice HNSW coseno. Se borran con su versión |
| `faqs` | id, pregunta, respuesta, fuente, activa, embedding `vector(384)` | Respuesta directa sin LLM. Índice HNSW coseno |
| `consultas_pendientes` | id, pregunta (≤ 1000), motivo (sin_evidencia, fuera_de_alcance, error, pedido_del_alumno), contacto opcional (≤ 200), creada_en, atendida_en, nota_atencion | Mínimos datos; retención por definir con TI |
| `eventos` | id, tipo (consulta, ingesta, error, salud), estado, ms_total, ms_primer_token, modelo, creado_en | Sin texto de la pregunta ni datos personales |

- **Vista `fragmentos_vigentes`:** fragmentos de versiones vigentes con título, curso y tipo del documento. **El RAG busca solo aquí**, así nunca responde con material retirado.
- **Función `registrar_version(documento, archivo, hash, paginas)`:** en una sola transacción retira la versión vigente y crea la siguiente (número correlativo). Rechaza volver a cargar el mismo archivo si ya es el vigente.
- **Dimensión 384:** la de los dos modelos de embeddings candidatos. Si el benchmark elige otro con otra dimensión, se cambia el SQL y se recalculan los embeddings.
- Búsqueda: `ORDER BY embedding <=> :pregunta LIMIT 4` (distancia coseno: 0 = idéntico, 2 = opuesto).

## Entornos

| Entorno | Dónde | Para qué |
| --- | --- | --- |
| Local | PC de Alfredo (Windows + Docker Desktop/WSL2) | Desarrollo hasta PC3 |
| Servidor simulado | VM Ubuntu Server 24.04, 4 vCPU, 8 GB, sin GPU | Ensayo del despliegue real (Fase 6) |
| CEE | HP ProDesk 600 G1 | Piloto y producción (Fase 7, sujeto a TI) |

## Decisiones pendientes

- Modelos de LLM y embeddings (Fase 2). Mientras tanto: `qwen2.5:1.5b` y `paraphrase-multilingual-MiniLM-L12-v2`.
- Umbral de relevancia (Fase 2, con el set de preguntas).
- Mecanismo de sesión con el campus (Grupo 3).
- Sistema operativo del equipo del CEE (TI).
