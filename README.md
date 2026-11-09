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
docker compose exec ollama ollama pull granite3.3:2b
```

Pesa ~1,5 GB y queda guardado en el volumen `modelos_ollama`. Mientras no esté, `/salud` dice `degradado` ("falta descargar el modelo") y el bot responde solo con FAQs o con el fragmento más cercano. Es el modelo elegido en el benchmark del 07/11/2026, junto con los embeddings `intfloat/multilingual-e5-small` (se descargan solos la primera vez).

### 5. Cargar los documentos de prueba

```bash
docker compose exec api python -m app.ingesta corpus /corpus/prueba
docker compose exec api python -m app.ingesta estado
```

Carga 6 PDF ficticios (temarios de Cadena de Suministro, Lean Six Sigma y Gestión de Proyectos con el PMBOK, separatas de inventarios y de herramientas estadísticas, y un reglamento académico) y 5 FAQs, todos marcados como **DOCUMENTO DE PRUEBA**. La primera carga descarga el modelo de embeddings (~470 MB, queda en el volumen `modelos_embeddings`). Si vuelves a correrlo, no duplica nada: los PDF que no cambiaron se saltan.

Otros comandos de la ingesta:

| Qué | Comando |
| --- | --- |
| Un PDF suelto | `docker compose exec api python -m app.ingesta documento /corpus/prueba/archivo.pdf --titulo "Título" --tipo separata --curso "Curso"` |
| Solo las FAQs (reemplaza las anteriores) | `docker compose exec api python -m app.ingesta faqs /corpus/prueba/faqs.csv` |
| Qué hay cargado | `docker compose exec api python -m app.ingesta estado` |

Los PDF de prueba se generan con `python scripts/generar_corpus_prueba.py` (necesita `pip install reportlab`, solo para desarrollo). Solo crea los que faltan; con `--todos` rehace también los existentes (cambian y la ingesta los carga como versión nueva).
| Retirar los documentos de una carpeta (no borra nada) | `docker compose exec api python -m app.ingesta retirar /corpus/complementario` |

#### Material complementario de los 3 cursos

`corpus/complementario/` tiene **12 separatas** (4 por curso) con el contenido completo de cada tema, redactado a partir de fuentes públicas confiables (Chopra y Meindl, ASCM/SCOR DS, Hyndman, PMI/PMBOK, NIST/SEMATECH, Lean Enterprise Institute, AIAG, entre otras; cada documento termina con su bibliografía). Sirve para que el tutor responda con más detalle mientras el CEE no entregue su material:

| Curso | Separatas |
| --- | --- |
| Gestión de la Cadena de Suministro | M1 Fundamentos y SCOR · M2 Pronóstico y S&OP · M3 Inventarios · M4 Indicadores |
| Lean Six Sigma Green Belt | U1 Pensamiento Lean · U2 Six Sigma y DMAIC · U3 Herramientas estadísticas · U4 Proyecto de mejora |
| Gestión de Proyectos con el PMBOK | U1 Fundamentos y alcance · U2 Cronograma · U3 Costos y valor ganado · U4 Riesgos e interesados |

```bash
docker compose exec api python -m app.ingesta corpus /corpus/complementario
```

Cada página dice **MATERIAL DE PRUEBA – no es material oficial ni validado por el CEE**. Se puede cargar junto con `corpus/prueba` (los títulos terminan en "(material complementario)" y no chocan). Cuando llegue el material del CEE se retira con `retirar` (arriba). El benchmark sigue usando solo `corpus/prueba`. Los textos están en `corpus/complementario/fuentes/*.md`; si se corrige uno, se regeneran los PDF con `python scripts/generar_corpus_complementario.py` y se vuelve a cargar la carpeta (entran como versión nueva).

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

### 7. Benchmark de modelos (Fase 2)

Compara 2 modelos de embeddings y 2 de lenguaje con el set de 30 preguntas de `benchmark/preguntas.json` (20 que los documentos responden y 10 que el tutor debe rechazar). No cambia tu base: todo corre en una transacción que se deshace al final.

```bash
# Una sola vez: el segundo modelo de lenguaje (~1,5 GB)
docker compose exec ollama ollama pull granite3.3:2b

# Rápido (1–3 min): solo la búsqueda y los umbrales propuestos
docker compose exec api python -m app.benchmark --solo-busqueda

# Completo (30–60 min): búsqueda + respuestas con cada modelo de lenguaje
docker compose exec api python -m app.benchmark
```

Antes del completo, deja **al menos 4 GB de RAM libres**: cierra el navegador, Zoom, Steam y Discord, y apaga el Supabase de Huarón (`npx supabase stop` en esa carpeta). Si falta RAM, los tiempos salen inflados o todo queda como `sin_llm`.

El informe queda en `benchmark/resultados/AAAA-MM-DD_HHMM.md` (léelo en VS Code con la vista previa de Markdown) y el detalle de cada pregunta en el `.csv` del mismo nombre (se abre en Excel). Mide:

- **recall@5**: si el fragmento con la respuesta quedó entre los 5 más cercanos (meta: 80 %).
- **Umbral propuesto** de documentos y de FAQs: lo que mejor separa las preguntas de dentro de las de fuera. Cada modelo de embeddings tiene su propia escala de distancias, así que al cambiar de modelo hay que copiar sus umbrales a `.env` (`UMBRAL_DISTANCIA`, `UMBRAL_FAQ`).
- **Aciertos con fuente**, **rechazos correctos** (por la búsqueda o por el modelo), tiempo al primer token, tiempo de respuesta (promedio y p95) y RAM de cada modelo.

Opciones: `--embeddings a,b` y `--llm x,y` para elegir modelos; `--umbral 0.5` y `--umbral-faq 0.2` para probar umbrales fijos. Al terminar vuelve a cargar el modelo del chat.

**Modelos elegidos (07/11/2026):** `intfloat/multilingual-e5-small` + `granite3.3:2b`, con `UMBRAL_DISTANCIA=0.18` y `UMBRAL_FAQ=0.10` (son los valores por defecto).

### 8. Cambiar de modelo de embeddings

Los vectores de los documentos guardados en la base dependen del modelo: al cambiarlo hay que recalcularlos (la ingesta normal se salta los PDF que no cambiaron). En `.env` cambia `EMBEDDINGS_MODELO`, sus umbrales y `MARGEN_FUENTES` (también va en la escala del modelo), y luego:

```bash
docker compose up -d
docker compose exec api python -m app.ingesta reindexar
```

### 9. Consultas pendientes (para el CEE) y límite por minuto

Lo que el tutor no supo responder queda guardado (solo la pregunta, el motivo y la fecha). Para verlo:

1. En `.env`, pon una clave larga en `CLAVE_CEE` (por ejemplo, 30 letras y números al azar) y reinicia la API con `docker compose up -d api`. Sin clave, el listado está apagado.
2. Abre http://localhost:8000/docs, sección **CEE** → `GET /consultas-pendientes` → *Try it out*, escribe la clave en `X-Clave-CEE` y *Execute*. Con `POST /consultas-pendientes/{id}/atendida` se marca una como atendida, con una nota (por ejemplo, "se agregó una FAQ").

En PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/consultas-pendientes -Headers @{ "X-Clave-CEE" = "tu-clave" }
```

Cada alumno puede hacer `LIMITE_POR_MINUTO` preguntas por minuto (8 por defecto; 0 = sin límite). Si se pasa, el chat le pide esperar unos segundos. Detrás de Nginx, en el servidor, se pone `CONFIAR_EN_PROXY=true`, para que cuente la IP de cada alumno y no la del proxy.

### 10. El chat como un solo archivo para el Campus (`tutor-cee.js`)

`npm run build` (en `frontend`) también genera `frontend/dist-embebido/tutor-cee.js`: el chat completo (estilos y logo incluidos) en un solo archivo. Se pega en Moodle (Administración del sitio → Apariencia → HTML adicional → "Antes de cerrar BODY"):

```html
<script src="https://<servidor-del-tutor>/widget/tutor-cee.js" data-api="https://<servidor-del-tutor>/api" defer></script>
```

`data-api` es la dirección de la API y la del Campus tiene que estar en `ORIGENES_PERMITIDOS` del `.env`. Para probarlo sin Moodle: `npm run build`, luego `npx vite preview --outDir . --port 4173` y abre http://127.0.0.1:4173/ejemplo-moodle.html (una página con estilos agresivos, como los de un tema de Moodle, que no deben cambiar el chat).

### 11. Por qué respondió (o no) una pregunta

```bash
docker compose exec api python -m app.diagnostico "¿Cómo se calcula el OEE?"
```

Muestra los fragmentos encontrados (distancia por significado y puntaje de la búsqueda híbrida), cuáles van al modelo, la respuesta del modelo tal cual y lo que deja el control de respaldo. No guarda nada. Con `--sin-llm` solo hace la búsqueda. Sirve para calibrar `UMBRAL_DISTANCIA`, `PESO_LEXICO`, `MARGEN_PUNTAJE` y `MINIMO_RESPALDO` en el `.env`.

### 12. Que otros lo prueben desde su PC (túnel temporal)

Para una reunión o una revisión del equipo. El chat y la API salen por un solo enlace; la base y Ollama no se exponen.
**Cualquiera con el enlace puede usar el tutor con tu PC mientras el túnel esté abierto: ciérralo al terminar (Ctrl+C).**

1. Con el tutor levantado (`docker compose up -d`, `/salud` en ok), pon `CONFIAR_EN_PROXY=true` en `.env` y aplica con
   `docker compose up -d` (así cada visitante tiene su propio límite de preguntas por minuto). Vuelve a `false` después.
2. En `frontend`: `npm ci` (la primera vez) y `npm run compartir` (deja esa terminal abierta: sirve el chat en
   http://127.0.0.1:4173 y pasa `/api` a la API).
3. En otra terminal, una de estas:
   - **Cloudflare (sin cuenta):** `winget install --id Cloudflare.cloudflared` (una vez) y
     `cloudflared tunnel --url http://127.0.0.1:4173`. Copia el enlace `https://….trycloudflare.com` que aparece.
   - **ngrok (cuenta gratuita, sin tarjeta):** `winget install ngrok.ngrok`, `ngrok config add-authtoken <tu token>`
     (el token está en el panel de ngrok; no lo pegues en el repo) y `ngrok http 127.0.0.1:4173`. Copia el enlace
     `https://….ngrok-free.app`; la primera vez muestra un aviso de ngrok y hay que darle a "Visit Site".
4. Pasa el enlace por el chat del equipo. El enlace cambia cada vez que abres el túnel.

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
| `no configuration file provided: not found` | Estás en otra carpeta (por ejemplo `frontend`) o en una rama sin el código: vuelve a la raíz del proyecto y revisa `git branch` |
| `ports are not available ... 11434` | Tienes Ollama instalado en Windows: ciérralo (ícono junto al reloj → Quit Ollama) o pon `PUERTO_OLLAMA=11435` en `.env` |
| `ports are not available ... 5432` | Tienes otro PostgreSQL instalado: detenlo o pon `PUERTO_DB=5433` en `.env` (y usa ese puerto en `TEST_DATABASE_URL`) |
| `/salud` dice `degradado` | Mira `docker compose ps` y `docker compose logs db ollama`; si dice "falta descargar el modelo", haz el paso 4 |
| El bot siempre dice "No encontré esa información" | No cargaste los documentos (paso 5): revisa con `python -m app.ingesta estado` |
| El bot responde con un fragmento y no redacta | Ollama no responde o falta el modelo (paso 4). Si `docker compose logs ollama` dice "Load failed", falta RAM: cierra programas pesados hasta tener 4 GB libres |
| No aparecen las tablas nuevas | Los SQL de `infra/db` solo corren al crear la base: `docker compose down -v` y `docker compose up -d` |

## Cómo se trabaja

Ver "Cómo trabajar en este repo" en [`CLAUDE.md`](CLAUDE.md): al terminar cada sesión se actualizan `CLAUDE.md`, el roadmap y la bitácora, y se hace commit y push.
