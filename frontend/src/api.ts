export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type EstadoServicio = { estado: "ok" | "error"; detalle?: string };

export type RespuestaSalud = {
  estado: "ok" | "degradado";
  servicios: { base: EstadoServicio; ollama: EstadoServicio & { modelos?: string[] } };
};

export async function consultarSalud(senal?: AbortSignal): Promise<RespuestaSalud> {
  const respuesta = await fetch(`${API_URL}/salud`, { signal: senal });
  if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
  return respuesta.json() as Promise<RespuestaSalud>;
}

export type EstadoRespuesta = "respondida" | "faq" | "orientacion" | "sin_evidencia" | "sin_llm" | "ocupado";

export type Fuente = { titulo: string; pagina: number | null };

export type RespuestaConsulta = {
  estado: EstadoRespuesta;
  respuesta: string;
  fuentes: Fuente[];
  ms: number;
};

export const LARGO_MAXIMO_PREGUNTA = 500;

/** `anterior`: la pregunta previa del alumno en este chat, para entender seguimientos ("ese curso"). */
export async function consultar(pregunta: string, anterior?: string, senal?: AbortSignal): Promise<RespuestaConsulta> {
  const respuesta = await fetch(`${API_URL}/consulta`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(anterior ? { pregunta, anterior } : { pregunta }),
    signal: senal,
  });
  if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
  return respuesta.json() as Promise<RespuestaConsulta>;
}
