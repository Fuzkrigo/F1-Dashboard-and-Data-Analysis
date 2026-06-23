/**
 * Dashboard E2E suite.
 *
 * [EN] End-to-end coverage that mirrors the manual validation of R3.2: the app
 * boots against the real API, the 7 views navigate and each one proves its
 * initial data load ran, and the Overview no longer fires the N+1 by-id cascade
 * that PR3 removed.
 *
 * [PT-BR] Cobertura end-to-end que espelha a validacao manual da R3.2: o app
 * sobe contra a API real, as 7 telas navegam e cada uma prova que sua carga de
 * dados inicial rodou, e a Visao Geral nao dispara mais a cascata N+1 por-id que
 * a PR3 removeu.
 *
 * Author: Bruno Krieger
 */
import { test, expect } from '@playwright/test';

// [EN] Each view: nav id, expected header title, and a "loaded" signal that only
//      shows up after the view's controller fetched and rendered real data.
// [PT-BR] Cada view: id do nav, titulo esperado e um sinal de "carregou" que so
//         aparece depois que o controller da tela buscou e renderizou dados reais.
const VIEWS = [
  {
    id: 'overview',
    title: 'VISÃO GERAL DO CAMPEONATO',
    ready: (page) => expect(page.locator('#kpi-races')).toHaveText(/^\d+$/),
  },
  {
    id: 'telemetry',
    title: 'TELEMETRIA E RITMO',
    ready: (page) =>
      expect
        .poll(() => page.locator('#telemetry-race option').count())
        .toBeGreaterThan(1),
  },
  {
    id: 'evolution',
    title: 'EVOLUÇÃO DO CAMPEONATO',
    ready: (page) =>
      expect(page.locator('#evolution-chart')).toHaveClass(/js-plotly-plot/, {
        timeout: 20_000,
      }),
  },
  {
    id: 'h2h',
    title: 'BATALHA HEAD-TO-HEAD',
    ready: (page) =>
      expect
        .poll(() => page.locator('#h2h-driver1 option').count())
        .toBeGreaterThan(1),
  },
  {
    id: 'pits',
    title: 'ANÁLISE DE PIT STOPS',
    ready: (page) =>
      expect
        .poll(() => page.locator('#pits-race option').count())
        .toBeGreaterThan(1),
  },
  {
    id: 'grid',
    title: 'DOMÍNIO DE PISTA',
    ready: (page) =>
      expect
        .poll(() => page.locator('#grid-race option').count())
        .toBeGreaterThan(1),
  },
  {
    id: 'history',
    title: 'ARQUIVO HISTÓRICO',
    ready: (page) => expect(page.locator('#history-total-races')).toHaveText(/^\d+$/),
  },
];

// [EN] Waits for the app to finish booting: seasons loaded, a 4-digit year set.
// [PT-BR] Espera o app terminar o boot: temporadas carregadas, ano de 4 digitos.
async function waitForBoot(page) {
  await page.goto('/');
  await expect(page.locator('#season-select')).toHaveValue(/^\d{4}$/);
}

test.describe('boot', () => {
  test('carrega as temporadas e seleciona a mais recente', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));

    await waitForBoot(page);

    const select = page.locator('#season-select');
    const years = (
      await select.locator('option').evaluateAll((opts) => opts.map((o) => o.value))
    ).map(Number);

    expect(years.length).toBeGreaterThanOrEqual(3);
    // [EN] App must auto-select the latest season. / [PT-BR] App deve selecionar a mais recente.
    expect(Number(await select.inputValue())).toBe(Math.max(...years));
    expect(errors).toEqual([]);
  });

  test('popula os KPIs da Visão Geral com dados reais', async ({ page }) => {
    await waitForBoot(page);

    await expect(page.locator('#kpi-races')).toHaveText(/^\d+$/);
    await expect(page.locator('#kpi-driver-leader')).not.toHaveText('--');
    await expect(page.locator('#kpi-team-leader')).not.toHaveText('--');
  });
});

test.describe('navegação entre as 7 views', () => {
  for (const view of VIEWS) {
    test(`abre "${view.id}" e carrega dados`, async ({ page }) => {
      await waitForBoot(page);

      await page.locator(`.nav-links li[data-view="${view.id}"]`).click();

      // [EN] Shell switched. / [PT-BR] Casca trocou.
      await expect(page.locator(`#view-${view.id}`)).toHaveClass(/active/);
      await expect(
        page.locator(`.nav-links li[data-view="${view.id}"]`)
      ).toHaveClass(/active/);
      await expect(page.locator('#page-title')).toHaveText(view.title);
      await expect(page.locator('.view.active')).toHaveCount(1);

      // [EN] Initial data load actually ran. / [PT-BR] Carga inicial de dados rodou.
      await view.ready(page);
    });
  }
});

test.describe('regressão', () => {
  test('a Visão Geral não dispara cascata N+1 por-id', async ({ page }) => {
    const byIdCascade = [];
    page.on('request', (req) => {
      // [EN] Matches the removed cascade: /api/v1/drivers/<id> or /constructors/<id>.
      //      Enriched list endpoints (/standings/drivers/) have no numeric id segment.
      // [PT-BR] Casa com a cascata removida: /api/v1/drivers/<id> ou /constructors/<id>.
      //      Endpoints de lista enriquecidos (/standings/drivers/) nao tem id numerico.
      if (/\/api\/v1\/(drivers|constructors)\/\d+/.test(req.url())) {
        byIdCascade.push(req.url());
      }
    });

    await waitForBoot(page);
    await expect(page.locator('#kpi-races')).toHaveText(/^\d+$/);

    expect(
      byIdCascade,
      `Cascata N+1 detectada:\n${byIdCascade.join('\n')}`
    ).toHaveLength(0);
  });
});
