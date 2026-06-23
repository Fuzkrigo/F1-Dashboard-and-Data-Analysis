import { defineConfig } from 'vitest/config';

// [EN] Vitest config: unit tests for the frontend's pure-logic modules.
//      Tests live next to the modules under src/web/js (colocation).
// [PT-BR] Config do Vitest: testes unitarios dos modulos de logica pura do
//         frontend. Os testes ficam ao lado dos modulos em src/web/js.
export default defineConfig({
  test: {
    include: ['src/web/js/**/*.{test,spec}.js'],
    environment: 'jsdom',
  },
});
