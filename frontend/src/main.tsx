import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Widget } from "./Widget";
import "./estilos.css";

const contenedor = document.getElementById("tutor-virtual");
if (contenedor) {
  createRoot(contenedor).render(
    <StrictMode>
      <Widget />
    </StrictMode>,
  );
}
