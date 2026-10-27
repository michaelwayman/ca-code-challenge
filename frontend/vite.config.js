import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// One self-contained script that Django serves as a static file.
export default defineConfig({
  plugins: [react()],
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    lib: { entry: "src/main.jsx", formats: ["iife"], name: "BrandListBundle", fileName: () => "brandlist.js" },
  },
});
