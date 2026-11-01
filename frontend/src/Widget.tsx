import { useEffect, useState } from "react";
import { consultarSalud } from "./api";

type Conexion = "revisando" | "disponible" | "degradado" | "sin-conexion";

const TEXTO_CONEXION: Record<Conexion, string> = {
  revisando: "Revisando conexión…",
  disponible: "Disponible",
  degradado: "Funcionando con limitaciones",
  "sin-conexion": "El tutor no está disponible en este momento",
};

export function Widget() {
  const [abierto, setAbierto] = useState(false);
  const [conexion, setConexion] = useState<Conexion>("revisando");

  useEffect(() => {
    if (!abierto) return;
    const control = new AbortController();
    setConexion("revisando");
    consultarSalud(control.signal)
      .then((r) => setConexion(r.estado === "ok" ? "disponible" : "degradado"))
      .catch(() => {
        if (!control.signal.aborted) setConexion("sin-conexion");
      });
    return () => control.abort();
  }, [abierto]);

  return (
    <div className="tutor">
      {abierto && (
        <section className="tutor-panel" role="dialog" aria-label="Tutor Virtual del CEE">
          <header className="tutor-cabecera">
            <img className="tutor-avatar" src="/marca/cee-simbolo.png" alt="" />
            <div className="tutor-titulo">
              <strong>Tutor Virtual CEE</strong>
              <span className={`tutor-estado tutor-estado--${conexion}`}>{TEXTO_CONEXION[conexion]}</span>
            </div>
            <button type="button" className="tutor-cerrar" onClick={() => setAbierto(false)} aria-label="Cerrar">
              ×
            </button>
          </header>
          <div className="tutor-mensajes">
            <p className="tutor-mensaje tutor-mensaje--bot">
              Hola, soy el tutor virtual del CEE. Respondo con los materiales validados de tus cursos.
            </p>
          </div>
          <p className="tutor-aviso">Asistente automatizado: puede equivocarse. Revisa siempre las fuentes.</p>
          <form className="tutor-entrada" onSubmit={(e) => e.preventDefault()}>
            <input type="text" placeholder="Muy pronto podrás preguntar" disabled aria-label="Tu pregunta" />
            <button type="submit" disabled>
              Enviar
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className="tutor-boton"
        onClick={() => setAbierto((a) => !a)}
        aria-expanded={abierto}
        aria-label={abierto ? "Cerrar el tutor virtual" : "Abrir el tutor virtual"}
      >
        {abierto ? "×" : <img src="/marca/cee-simbolo.png" alt="" />}
      </button>
    </div>
  );
}
