#!/usr/bin/env bash
# Respaldo de la base del tutor (documentos, fragmentos, FAQs, consultas pendientes) y de la carpeta corpus/.
# Lo corre cron dentro de WSL todos los días (docs/DESPLIEGUE.md, sección 9). Borra los de más de DIAS días.
#   infra/cee/respaldar.sh                         -> /mnt/c/TutorCEE/respaldos
#   DESTINO=/otra/carpeta DIAS=30 infra/cee/respaldar.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
DESTINO="${DESTINO:-/mnt/c/TutorCEE/respaldos}"
DIAS="${DIAS:-14}"
fecha="$(TZ=America/Lima date +%Y-%m-%d_%H%M)"

mkdir -p "$DESTINO"
cd "$REPO"

# pg_dump corre dentro del contenedor de la base, con su propio usuario: no hace falta leer el .env.
archivo="$DESTINO/tutor_${fecha}.dump"
docker compose -f docker-compose.yml -f docker-compose.cee.yml exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$archivo.tmp"
mv "$archivo.tmp" "$archivo"

# Los PDF y FAQs del CEE (puede que no estén en Git).
tar -czf "$DESTINO/corpus_${fecha}.tar.gz" corpus

find "$DESTINO" -maxdepth 1 \( -name 'tutor_*.dump' -o -name 'corpus_*.tar.gz' \) -mtime +"$DIAS" -delete
echo "$(TZ=America/Lima date '+%d/%m/%Y %H:%M') respaldo listo: $archivo ($(du -h "$archivo" | cut -f1))"
