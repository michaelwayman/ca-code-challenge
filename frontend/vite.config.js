import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// One self-contained script that Django serves as a static file.
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  define: mode === "test" ? {} : { "process.env.NODE_ENV": JSON.stringify("production") },
  test: { environment: "jsdom", globals: true },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    lib: { entry: "src/main.jsx", formats: ["iife"], name: "BrandListBundle", fileName: () => "brandlist.js" },
  },
}));
