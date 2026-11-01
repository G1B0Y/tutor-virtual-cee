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

La primera vez descarga las imágenes (unos minutos). Comprueba que todo responde:

- http://localhost:8000/salud → `"estado": "ok"` con pgvector y Ollama.
- http://localhost:8000/docs → documentación de la API (OpenAPI).

Todo queda publicado solo en `127.0.0.1`: nadie de tu red puede entrar a la base ni a Ollama.

### 4. Descargar un modelo en Ollama (para probar)

```bash
docker compose exec ollama ollama pull qwen2.5:1.5b
```

El modelo definitivo se elige en el benchmark (Fase 2).

### 5. Abrir el chat dentro del campus simulado

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run dev:red      # para abrirlo desde el celular en la misma red
```

Si apagas la API (`docker compose stop api`), el chat dice "El tutor no está disponible" y el campus sigue funcionando.

### Comandos

| Qué | Comando |
| --- | --- |
| Levantar todo | `docker compose up -d --build` |
| Ver estado | `docker compose ps` |
| Ver registros de la API | `docker compose logs -f api` |
| Apagar | `docker compose down` |
| Borrar también la base y los modelos | `docker compose down -v` |
| Pruebas del backend | `cd backend && pip install -r requirements-dev.txt && pytest` |
| Compilar el frontend | `cd frontend && npm run build` |

### Problemas frecuentes

| Problema | Solución |
| --- | --- |
| `required variable POSTGRES_PASSWORD is missing` | Falta el archivo `.env` en la raíz (paso 2) |
| El puerto 5432 está ocupado | Tienes otro PostgreSQL instalado: detenlo o cambia el puerto en `docker-compose.yml` |
| `/salud` dice `degradado` | Mira `docker compose ps` y `docker compose logs db ollama` |

## Cómo se trabaja

Ver "Cómo trabajar en este repo" en [`CLAUDE.md`](CLAUDE.md): al terminar cada sesión se actualizan `CLAUDE.md`, el roadmap y la bitácora, y se hace commit y push.
