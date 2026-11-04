import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // 127.0.0.1 fijo: en Windows "localhost" a veces queda solo en IPv6 (::1) y el navegador no conecta.
  // npm run dev:red usa --host y abre el chat a la red local.
  server: { host: "127.0.0.1", port: 5173 },
});
