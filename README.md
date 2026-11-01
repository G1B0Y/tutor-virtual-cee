# Tutor Virtual 24/7 – CEE FIIS-UNI

Chatbot RAG local, en español y a costo S/ 0, integrado al Campus Virtual del CEE. Proyecto del Grupo 5, curso Sistemas Integrados Empresariales (UNI).

- Plan y estado: [`docs/ROADMAP.md`](docs/ROADMAP.md)
- Contexto: [`docs/PROYECTO_TUTOR_VIRTUAL.md`](docs/PROYECTO_TUTOR_VIRTUAL.md)
- Arquitectura: [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md)
- Bitácora: [`docs/BITACORA.md`](docs/BITACORA.md)

## Stack

React + TypeScript + Vite · Python + FastAPI · PostgreSQL + pgvector · Sentence Transformers · Ollama · Docker Compose · Nginx · systemd.

## Entorno local (tu PC)

> En construcción (Fase 0). Se completa al crear el esqueleto y el `docker-compose.yml`.

### Instalar una sola vez

- Docker Desktop (con WSL2 en Windows)
- Python 3.12
- Node.js LTS
- Git

### Levantar

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up -d
```

## Cómo se trabaja

Ver "Cómo trabajar en este repo" en [`CLAUDE.md`](CLAUDE.md): al terminar cada sesión se actualizan `CLAUDE.md`, el roadmap y la bitácora, y se hace commit y push.
