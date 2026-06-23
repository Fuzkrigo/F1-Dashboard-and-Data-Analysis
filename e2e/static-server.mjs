/**
 * Minimal static file server for E2E tests.
 *
 * [EN] Dependency-free (Node built-ins only) static server that serves the
 * frontend in `src/web` on port 3000. Playwright's webServer starts it so the
 * SPA is reachable at http://localhost:3000 during tests. Keeping it here (vs.
 * a third-party static server) means zero extra deps and correct MIME types for
 * ES modules — Chromium refuses to load a module served as text/plain.
 *
 * [PT-BR] Servidor estático sem dependências (apenas built-ins do Node) que
 * serve o frontend em `src/web` na porta 3000. O webServer do Playwright o sobe
 * para que a SPA fique acessível em http://localhost:3000 durante os testes.
 * Mantê-lo aqui (em vez de um servidor de terceiros) significa zero dependências
 * extras e MIME types corretos para ES modules — o Chromium recusa carregar um
 * módulo servido como text/plain.
 *
 * Author: Bruno Krieger
 */
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

// [EN] Web root = src/web (this file lives in e2e/, sibling of src/).
// [PT-BR] Raiz web = src/web (este arquivo fica em e2e/, irmão de src/).
const ROOT = fileURLToPath(new URL('../src/web', import.meta.url));
const PORT = Number(process.env.PORT) || 3000;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.png': 'image/png',
  '.map': 'application/json; charset=utf-8',
};

const server = createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(
      new URL(req.url, 'http://localhost').pathname
    );
    // [EN] Map "/" to index.html; normalize to block path traversal.
    // [PT-BR] Mapeia "/" para index.html; normaliza para barrar path traversal.
    const rel = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
    const filePath = normalize(join(ROOT, rel));

    if (filePath !== ROOT && !filePath.startsWith(ROOT + sep)) {
      res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('403 Forbidden');
      return;
    }

    const data = await readFile(filePath);
    const type = MIME[extname(filePath).toLowerCase()] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': type });
    res.end(data);
  } catch {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('404 Not Found');
  }
});

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`[static-server] serving ${ROOT} at http://localhost:${PORT}`);
});
