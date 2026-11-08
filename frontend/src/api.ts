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

/** Seguimientos ("ese curso", "¿y el tema dos?"): `anterior` es la pregunta previa del alumno en este chat y
 * `documento`, el documento de la respuesta previa. Solo viajan en la consulta; el servidor no los guarda. */
export async function consultar(
  pregunta: string,
  anterior?: string,
  documento?: string,
  senal?: AbortSignal,
): Promise<RespuestaConsulta> {
  const respuesta = await fetch(`${API_URL}/consulta`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pregunta, ...(anterior ? { anterior } : {}), ...(documento ? { documento } : {}) }),
    signal: senal,
  });
  if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
  return respuesta.json() as Promise<RespuestaConsulta>;
}
