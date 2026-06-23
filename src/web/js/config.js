/**
 * Frontend runtime configuration.
 *
 * [EN] Centralizes the API base URL. Detects the environment by hostname:
 * local development uses the local FastAPI; anything else uses the production
 * URL (set during deploy, R5). Keeping it here avoids hardcoding the URL in
 * app.js and makes the deploy a one-line change.
 *
 * [PT-BR] Centraliza a URL base da API. Detecta o ambiente pelo hostname:
 * desenvolvimento local usa o FastAPI local; o resto usa a URL de produção
 * (definida no deploy, R5). Manter aqui evita hardcode no app.js e torna o
 * deploy uma mudança de uma linha.
 *
 * Author: Bruno Krieger
 */

const LOCAL_HOSTS = ['localhost', '127.0.0.1', ''];

// [PT-BR] Substituir pela URL real da API no deploy (R5).
// [EN] Replace with the real API URL on deploy (R5).
const PRODUCTION_API_BASE = 'https://f1-insights-api.onrender.com/api/v1';

const isLocal = LOCAL_HOSTS.includes(window.location.hostname);

export const API_BASE = isLocal
  ? 'http://127.0.0.1:8000/api/v1'
  : PRODUCTION_API_BASE;
