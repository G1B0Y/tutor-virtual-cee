# Chat del tutor servido por Nginx (despliegue en el CEE). Contexto de construcción: frontend/.
# Etapa 1: compila el chat (dist/, con la API en /api) y el widget para Moodle (dist-embebido/tutor-cee.js).
FROM node:22.14.0-alpine AS compilar
WORKDIR /frontend
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npx tsc --noEmit \
 && npx vite build --mode compartir \
 && npx vite build -c vite.embebido.config.ts

# Etapa 2: solo los archivos estáticos (la configuración llega como volumen desde infra/web/tutor-cee.conf).
FROM nginx:1.28.0-alpine
COPY --from=compilar /frontend/dist /usr/share/nginx/html
COPY --from=compilar /frontend/dist-embebido/tutor-cee.js /usr/share/nginx/html/widget/tutor-cee.js
