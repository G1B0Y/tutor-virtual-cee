import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Construye dist-embebido/tutor-cee.js: un solo archivo (JS + estilos + logo) para pegar en el Campus.
export default defineConfig({
  plugins: [react()],
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  build: {
    outDir: "dist-embebido",
    emptyOutDir: true,
    copyPublicDir: false,
    assetsInlineLimit: 100_000, // el logo va dentro del archivo
    lib: { entry: "src/embebido.tsx", name: "TutorCEE", formats: ["iife"], fileName: () => "tutor-cee.js" },
  },
});
