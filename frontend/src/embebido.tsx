/**
 * Entrada de `tutor-cee.js`: el chat en un solo archivo para pegar en el Campus (Moodle → "HTML adicional"):
 *
 *   <script src="https://servidor-del-tutor/tutor-cee.js" data-api="https://servidor-del-tutor/api" defer></script>
 *
 * Crea su propio contenedor al final de la página y monta el chat dentro de un Shadow DOM, para que los estilos de
 * Moodle no cambien los del chat ni al revés. Si la API está caída, la página del Campus sigue funcionando.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { usarApi } from "./api";
import estilos from "./estilos.css?inline";
import { Widget } from "./Widget";

// Hay que leerlo ahora: document.currentScript solo existe mientras el script se está ejecutando.
const api = (document.currentScript as HTMLScriptElement | null)?.dataset.api;
if (api) usarApi(api);

function montar(): void {
  if (document.getElementById("tutor-cee")) return; // pegado dos veces: un solo chat
  const anfitrion = document.createElement("div");
  anfitrion.id = "tutor-cee";
  document.body.appendChild(anfitrion);
  const sombra = anfitrion.attachShadow({ mode: "open" });
  const estilo = document.createElement("style");
  estilo.textContent = estilos;
  const raiz = document.createElement("div");
  sombra.append(estilo, raiz);
  createRoot(raiz).render(
    <StrictMode>
      <Widget />
    </StrictMode>,
  );
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", montar);
else montar();
