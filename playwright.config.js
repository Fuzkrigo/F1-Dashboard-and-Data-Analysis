import { defineConfig } from '@playwright/test';

// [EN] Playwright config for end-to-end tests of the dashboard views.
//      Real tests + webServer wiring are added in R3.2 PR3.
// [PT-BR] Config do Playwright para testes end-to-end das telas do dashboard.
//         Os testes reais + a subida dos servicos entram na R3.2 PR3.
export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:3000',
  },
});
