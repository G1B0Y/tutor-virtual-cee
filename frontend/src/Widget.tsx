import { useEffect, useRef, useState, type FormEvent } from "react";
import { consultar, consultarSalud, LARGO_MAXIMO_PREGUNTA, type EstadoRespuesta, type Fuente } from "./api";

type Conexion = "revisando" | "disponible" | "degradado" | "sin-conexion";

const TEXTO_CONEXION: Record<Conexion, string> = {
  revisando: "Revisando conexión…",
  disponible: "Disponible",
  degradado: "Funcionando con limitaciones",
  "sin-conexion": "El tutor no está disponible en este momento",
};

type Mensaje =
  | { id: number; de: "alumno"; texto: string }
  | { id: number; de: "bot"; texto: string; estado?: EstadoRespuesta | "error"; fuentes?: Fuente[] };

type MensajeNuevo = Mensaje extends infer M ? (M extends Mensaje ? Omit<M, "id"> : never) : never;

const BIENVENIDA: Mensaje = {
  id: 0,
  de: "bot",
  texto: "Hola, soy el tutor virtual del CEE. Pregúntame sobre tus cursos: temarios, módulos, separatas o el reglamento.",
};

function textoFuente(f: Fuente): string {
  return f.pagina ? `${f.titulo}, pág. ${f.pagina}` : f.titulo;
}

export function Widget() {
  const [abierto, setAbierto] = useState(false);
  const [conexion, setConexion] = useState<Conexion>("revisando");
  const [mensajes, setMensajes] = useState<Mensaje[]>([BIENVENIDA]);
  const [pregunta, setPregunta] = useState("");
  const [pensando, setPensando] = useState(false);
  const siguienteId = useRef(1);
  const finDeMensajes = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    finDeMensajes.current?.scrollIntoView?.({ block: "end" });
  }, [mensajes, pensando]);

  const agregar = (m: MensajeNuevo) =>
    setMensajes((actuales) => [...actuales, { ...m, id: siguienteId.current++ } as Mensaje]);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    const texto = pregunta.trim();
    if (texto.length < 2 || pensando) return;
    const anterior = [...mensajes].reverse().find((m) => m.de === "alumno")?.texto;
    agregar({ de: "alumno", texto });
    setPregunta("");
    setPensando(true);
    try {
      const r = await consultar(texto, anterior);
      agregar({ de: "bot", texto: r.respuesta, estado: r.estado, fuentes: r.fuentes });
      setConexion("disponible");
    } catch {
      agregar({ de: "bot", estado: "error", texto: "No pude conectarme con el tutor. Intenta de nuevo en unos minutos." });
      setConexion("sin-conexion");
    } finally {
      setPensando(false);
    }
  }

  const deshabilitado = conexion === "sin-conexion" || pensando;

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
          <div className="tutor-mensajes" aria-live="polite">
            {mensajes.map((m) => (
              <div
                key={m.id}
                className={`tutor-mensaje tutor-mensaje--${m.de}${m.de === "bot" && m.estado ? ` tutor-mensaje--${m.estado}` : ""}`}
              >
                <p>{m.texto}</p>
                {m.de === "bot" && m.fuentes && m.fuentes.length > 0 && (
                  <div className="tutor-fuentes">
                    <span>Fuentes:</span>
                    <ul>
                      {m.fuentes.map((f) => (
                        <li key={textoFuente(f)}>{textoFuente(f)}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
            {pensando && <div className="tutor-mensaje tutor-mensaje--bot tutor-pensando">Buscando en los materiales del CEE…</div>}
            <div ref={finDeMensajes} />
          </div>
          <p className="tutor-aviso">Asistente automatizado: puede equivocarse. Revisa siempre las fuentes.</p>
          <form className="tutor-entrada" onSubmit={enviar}>
            <input
              type="text"
              value={pregunta}
              onChange={(e) => setPregunta(e.target.value)}
              maxLength={LARGO_MAXIMO_PREGUNTA}
              placeholder={conexion === "sin-conexion" ? "El tutor no está disponible" : "Escribe tu pregunta"}
              disabled={deshabilitado}
              aria-label="Tu pregunta"
            />
            <button type="submit" disabled={deshabilitado || pregunta.trim().length < 2}>
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
