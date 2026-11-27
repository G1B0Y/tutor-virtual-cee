import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// `npm run compartir` (modo "compartir"): el chat llama a la API por /api en el mismo servidor, así un solo túnel
// (ngrok o cloudflared al puerto 4173) basta para que otros abran el proyecto desde su PC. La API, la base y Ollama
// no quedan expuestos directamente.
const TUNELES = [".ngrok-free.app", ".ngrok-free.dev", ".ngrok.app", ".ngrok.dev", ".trycloudflare.com"];

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, "..", "PUERTO_");
  const proxy = {
    "/api": {
      target: `http://127.0.0.1:${env.PUERTO_API || "8000"}`,
      changeOrigin: true,
      xfwd: true, // la API ve la IP de cada visitante (con CONFIAR_EN_PROXY=true) para el límite por minuto
      rewrite: (ruta: string) => ruta.replace(/^\/api/, ""),
    },
  };
  return {
    plugins: [react()],
    // 127.0.0.1 fijo: en Windows "localhost" a veces queda solo en IPv6 (::1) y el navegador no conecta.
    // npm run dev:red usa --host y abre el chat a la red local.
    server: { host: "127.0.0.1", port: 5173, proxy, allowedHosts: TUNELES },
    preview: { host: "127.0.0.1", port: 4173, strictPort: true, proxy, allowedHosts: TUNELES },
  };
});
