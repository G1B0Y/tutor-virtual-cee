# Integración del Tutor Virtual (Grupo 5) con el Campus Virtual Moodle (Grupo 3)

Propuesta del Grupo 5 · 03/11/2026 · basada en la documentación del Grupo 3 del 01/11/2026 (Moodle 5.3 LTS, Windows, Apache 2.4, PostgreSQL 18, tema `theme_cee`).

## Idea central

El tutor **no necesita tablas nuevas en Moodle ni leer su base de datos**. Tiene su propia base (PostgreSQL + pgvector) con los documentos validados por el CEE, y su propio servicio (API + modelo local). En Moodle solo se muestra el **botón flotante del chat** en las páginas del campus.

- Para Moodle no cambia nada de su modelo de datos: no se tocan `user`, `course`, `user_enrolments` ni ninguna otra tabla.
- Se cuida la Ley 29733: el tutor no recibe datos personales que no necesita (ni nombre, ni correo, ni notas).
- Si el tutor se cae, el campus sigue funcionando: el widget solo muestra "no disponible".

## ¿Por qué no una base de datos compartida?

| Dato | Dónde vive | Dueño |
| --- | --- | --- |
| Usuarios, cursos, matrículas, notas, entregas | Base de Moodle | Grupo 3 |
| Documentos validados por el CEE, fragmentos y embeddings | Base del tutor (pgvector) | Grupo 5 |

Lo que el tutor necesita de Moodle llega por interfaces, no leyendo sus tablas:

1. **Quién pregunta y sus cursos:** en el token de cada pregunta (Fase 2).
2. **Materiales de los cursos (opcional):** por los servicios web oficiales de Moodle, de solo lectura (por ejemplo `core_course_get_contents`). Los usa una cuenta de servicio. El CEE valida cada material antes de que el tutor lo cargue.

Motivos:

- La base de Moodle solo escucha en su propia PC y no tiene pgvector.
- Sus tablas cambian entre versiones, y una actualización del campus rompería al tutor.
- Una falla del tutor no debe afectar al campus.
- Por la Ley 29733, el tutor no debe poder ver notas, correos ni contraseñas.

## Fase 1 – Para la demo de PC3 (17/11): sin programar en Moodle

1. El Grupo 5 entrega un archivo `tutor-cee.js` (el widget, con la marca del CEE).
2. El Grupo 3 lo agrega en **Administración del sitio → Apariencia → HTML adicional → "Antes de cerrar BODY"**:

   ```html
   <script src="https://<servidor-del-tutor>/widget/tutor-cee.js" defer></script>
   ```

3. La API del tutor solo acepta llamadas desde la dirección del campus (CORS).

Resultado: el botón aparece en todas las páginas del campus, en PC y celular. Como el campus exige iniciar sesión para ver cualquier página (RNF-05 del Grupo 3), solo lo ven los usuarios del campus.

## Fase 2 – Después de PC3: identidad mínima con un plugin pequeño

Para limitar las solicitudes por alumno y priorizar los materiales de **sus** cursos, hace falta saber quién pregunta, sin exponer datos personales:

- Un plugin local de Moodle (`local_tutorcee`, unas pocas decenas de líneas de PHP) carga el widget solo para usuarios con sesión iniciada. Le pasa un **token firmado** (HMAC con una clave compartida) que vence a los pocos minutos.
- El token lleva solo:
  - un id opaco del usuario (no el nombre ni el correo);
  - el rol (estudiante o docente);
  - los `shortname` de los cursos en los que está matriculado.
- La API del tutor verifica la firma y usa esos datos. No guarda nada más.

Para el plugin, Moodle ya tiene lo necesario (`$USER`, `enrol_get_users_courses()` y el hook para agregar HTML antes del cierre del body), así que no hace falta crear tablas.

## Lo que necesitamos acordar

| Tema | Pregunta para el Grupo 3 |
| --- | --- |
| **Servidor** | ¿El campus y el tutor van en la **misma PC** del CEE? Moodle recomienda 8 GB y el tutor necesita 3–4 GB para el modelo: en el HP ProDesk de 8 GB no entran los dos con holgura. |
| Dirección | ¿Cuál será la URL del campus (dominio UNI o IP de la red del CEE)? El tutor se publicaría en la misma red, por ejemplo `https://<dominio>/tutor/` detrás de su Apache, o en un puerto propio. |
| HTML adicional | ¿Pueden agregar el `<script>` en "HTML adicional" para la demo de PC3? |
| Nombres de cursos | ¿Qué `shortname` tendrán los cursos (p. ej. `GCS-2026`)? El tutor etiqueta cada documento con su curso para filtrar por matrícula en la Fase 2. |
| Materiales | Los temarios y separatas que suban los docentes a Moodle, ¿los valida el CEE? Para el tutor solo entran documentos validados; la carga sigue siendo manual. |
| Funciones de IA de Moodle | Las tienen desactivadas (RNF-10): perfecto, el tutor no las usa. |

## Qué ofrece el Grupo 5 a cambio

- El widget empaquetado (`tutor-cee.js`) y una página de prueba para que lo vean en su Moodle local.
- Si quieren, el código del plugin `local_tutorcee` para la Fase 2. Lo revisan e instalan ellos.
- Nuestra documentación: arquitectura, modelo de datos y PDF de avance.
