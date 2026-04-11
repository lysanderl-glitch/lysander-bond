// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: 'https://lysander.bond',
  output: 'static',
  vite: {
    plugins: [tailwindcss()]
  }
});
