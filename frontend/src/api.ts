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
