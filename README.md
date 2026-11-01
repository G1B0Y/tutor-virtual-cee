# Tutor Virtual 24/7 – CEE FIIS-UNI

Chatbot RAG local, en español y a costo S/ 0, integrado al Campus Virtual del CEE. Proyecto del Grupo 5, curso Sistemas Integrados Empresariales (UNI).

- Plan y estado: [`docs/ROADMAP.md`](docs/ROADMAP.md)
- Contexto: [`docs/PROYECTO_TUTOR_VIRTUAL.md`](docs/PROYECTO_TUTOR_VIRTUAL.md)
- Arquitectura: [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md)
- Bitácora: [`docs/BITACORA.md`](docs/BITACORA.md)

## Stack

React + TypeScript + Vite · Python + FastAPI · PostgreSQL + pgvector · Sentence Transformers · Ollama · Docker Compose · Nginx · systemd.

## Entorno local (tu PC)

### 1. Instalar una sola vez

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (en Windows, con WSL2 activado)
- [Node.js](https://nodejs.org/) 22 LTS
- Python 3.12 (solo para correr las pruebas del backend fuera de Docker)
- Git

### 2. Preparar el proyecto

```bash
git clone https://github.com/G1B0Y/tutor-virtual-cee.git
cd tutor-virtual-cee
cp .env.example .env              # en PowerShell: Copy-Item .env.example .env
cp frontend/.env.example frontend/.env
```

Abre `.env` y cambia `POSTGRES_PASSWORD`.

### 3. Levantar la base, Ollama y la API

```bash
docker compose up -d --build
```

La primera vez tarda bastante: descarga las imágenes y la API instala PyTorch para CPU (unos 1–2 GB). Las siguientes veces es rápido. Comprueba que todo responde:

- http://localhost:8000/salud → `"estado": "ok"` con pgvector y Ollama.
- http://localhost:8000/docs → documentación de la API (OpenAPI).

Todo queda publicado solo en `127.0.0.1`: nadie de tu red puede entrar a la base ni a Ollama.

### 4. Descargar el modelo de lenguaje (una sola vez)

```bash
docker compose exec ollama ollama pull qwen2.5:1.5b
```

Pesa ~1 GB y queda guardado en el volumen `modelos_ollama`. Mientras no esté, `/salud` dice `degradado` ("falta descargar el modelo") y el bot responde solo con FAQs o con el fragmento más cercano. El modelo definitivo se elige en el benchmark (Fase 2).

### 5. Cargar los documentos de prueba

```bash
docker compose exec api python -m app.ingesta corpus /corpus/prueba
docker compose exec api python -m app.ingesta estado
```

Carga 4 PDF ficticios (temarios de Cadena de Suministro y Lean Six Sigma, una separata de inventarios y un reglamento académico) y 5 FAQs, todos marcados como **DOCUMENTO DE PRUEBA**. La primera carga descarga el modelo de embeddings (~470 MB, queda en el volumen `modelos_embeddings`). Si vuelves a correrlo, no duplica nada: los PDF que no cambiaron se saltan.

Otros comandos de la ingesta:

| Qué | Comando |
| --- | --- |
| Un PDF suelto | `docker compose exec api python -m app.ingesta documento /corpus/prueba/archivo.pdf --titulo "Título" --tipo separata --curso "Curso"` |
| Solo las FAQs (reemplaza las anteriores) | `docker compose exec api python -m app.ingesta faqs /corpus/prueba/faqs.csv` |
| Qué hay cargado | `docker compose exec api python -m app.ingesta estado` |

Los PDF de prueba se regeneran con `python scripts/generar_corpus_prueba.py` (necesita `pip install reportlab`, solo para desarrollo).

### 6. Abrir el chat dentro del campus simulado

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run dev:red      # para abrirlo desde el celular en la misma red
```

Preguntas para probar:

| Pregunta | Qué debería pasar |
| --- | --- |
| ¿Cuál es la nota mínima para aprobar? | Responde la FAQ al instante (sin modelo) |
| ¿Cómo se calcula el inventario de seguridad? | Respuesta del modelo con la fuente: separata, pág. N |
| ¿Qué temas ve la unidad 3 de Lean Six Sigma? | Respuesta con el temario como fuente |
| ¿Cuántas horas dura el programa de Cadena de Suministro? | 96 horas, 4 módulos (temario) |
| ¿Quién ganó el último mundial? | "No encontré esa información…" y deriva al CEE (queda en `consultas_pendientes`) |

La primera respuesta del modelo tarda más (lo carga en memoria); en CPU cuenta con 10–40 s por respuesta. Si apagas la API (`docker compose stop api`), el chat dice "El tutor no está disponible" y el campus sigue funcionando.

### Comandos

| Qué | Comando |
| --- | --- |
| Levantar todo | `docker compose up -d --build` |
| Ver estado | `docker compose ps` |
| Ver registros de la API | `docker compose logs -f api` |
| Ver consultas sin respuesta | `docker compose exec db psql -U tutor -d tutor -c "select creada_en, pregunta from consultas_pendientes order by creada_en desc"` |
| Apagar | `docker compose down` |
| Borrar también la base y los modelos | `docker compose down -v` |
| Pruebas del backend | `cd backend && pip install -r requirements-dev.txt && pytest` |
| Pruebas con la base real | en PowerShell: `$env:TEST_DATABASE_URL="postgresql://tutor:<tu contraseña>@localhost:5432/tutor"; pytest` |
| Entrar a la base | `docker compose exec db psql -U tutor -d tutor` |
| Recrear la base (aplica los SQL de `infra/db`) | `docker compose down -v` y luego `docker compose up -d` (borra los datos) |
| Compilar el frontend | `cd frontend && npm run build` |

### Problemas frecuentes

| Problema | Solución |
| --- | --- |
| `required variable POSTGRES_PASSWORD is missing` | Falta el archivo `.env` en la raíz (paso 2) |
| El puerto 5432 está ocupado | Tienes otro PostgreSQL instalado: detenlo o cambia el puerto en `docker-compose.yml` |
| `/salud` dice `degradado` | Mira `docker compose ps` y `docker compose logs db ollama`; si dice "falta descargar el modelo", haz el paso 4 |
| El bot siempre dice "No encontré esa información" | No cargaste los documentos (paso 5): revisa con `python -m app.ingesta estado` |
| El bot responde con un fragmento y no redacta | Ollama no responde o falta el modelo (paso 4) |
| No aparecen las tablas nuevas | Los SQL de `infra/db` solo corren al crear la base: `docker compose down -v` y `docker compose up -d` |

## Cómo se trabaja

Ver "Cómo trabajar en este repo" en [`CLAUDE.md`](CLAUDE.md): al terminar cada sesión se actualizan `CLAUDE.md`, el roadmap y la bitácora, y se hace commit y push.
