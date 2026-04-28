import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],

  // TEACH: When Electron loads the built app, it uses file:// URLs.
  // base: "./" makes all asset paths relative, so they work from any directory.
  // In dev mode (npm run dev), Vite serves on http://localhost:5173 — Electron
  // connects to that instead.
  base: "./",

  server: {
    port: 5173,
    // Allow Electron to connect from its own origin
    cors: true,
  },

  build: {
    // Output to dist/ — electron-builder picks this up
    outDir: "dist",
    emptyOutDir: true,
    // Don't minify in development builds so errors are readable
    minify: "esbuild",
  },

  // TEACH: Three.js uses WebGL which needs certain browser APIs.
  // These optimiseDeps settings tell Vite to pre-bundle Three.js and R3F
  // during dev startup so you don't get hot-reload lag on first import.
  optimizeDeps: {
    include: [
      "three",
      "@react-three/fiber",
      "@react-three/drei",
      "@react-three/postprocessing",
      "postprocessing",
    ],
    exclude: ["@react-three/fiber/native"],
  },
})
