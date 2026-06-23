import { defineConfig, devices } from '@playwright/test';

// [EN] Playwright config for end-to-end tests of the dashboard views.
//      Starts two servers: the static frontend (:3000) and the FastAPI backend
//      (:8000, reading real data from Supabase via .env). Tests run against the
//      same stack a user would hit locally.
// [PT-BR] Config do Playwright para testes end-to-end das telas do dashboard.
//         Sobe dois servidores: o frontend estatico (:3000) e o backend FastAPI
//         (:8000, lendo dados reais do Supabase via .env). Os testes rodam contra
//         a mesma stack que um usuario acessaria localmente.
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      // [EN] Static frontend. / [PT-BR] Frontend estatico.
      command: 'node e2e/static-server.mjs',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      // [EN] FastAPI backend (venv Python on Windows). reuseExistingServer lets a
      //      manually-started API be reused locally; CI always starts a fresh one.
      // [PT-BR] Backend FastAPI (Python da venv no Windows). reuseExistingServer
      //      permite reaproveitar uma API ja iniciada localmente; no CI sempre
      //      sobe uma nova.
      command: '.venv\\Scripts\\python.exe -m uvicorn src.api.main:app --port 8000',
      url: 'http://127.0.0.1:8000/',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
