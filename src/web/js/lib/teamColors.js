/**
 * Team colors module.
 *
 * [EN] Official F1 team color mapping and a case-insensitive, substring-based
 * lookup. Pure logic (no DOM), so it can be unit-tested in isolation.
 *
 * [PT-BR] Mapeamento de cores oficiais das equipes de F1 e uma busca
 * case-insensitive baseada em substring. Lógica pura (sem DOM), testável
 * isoladamente.
 *
 * Author: Bruno Krieger
 */

export const TEAM_COLORS_MAP = {
  'red bull': '#3671C6',
  ferrari: '#F91536',
  mercedes: '#6CD3BF',
  mclaren: '#FF8000',
  'aston martin': '#229971',
  alpine: '#0090FF',
  williams: '#37BEDD',
  rb: '#6692FF',
  alphatauri: '#2B4562',
  sauber: '#52E252',
  'alfa romeo': '#900000',
  haas: '#B6BABD',
  renault: '#FFF500',
  'racing point': '#F596C8',
};

// Default cyan used when the team is unknown / empty.
// Ciano padrão usado quando a equipe é desconhecida / vazia.
export const DEFAULT_TEAM_COLOR = '#00F0FF';

/**
 * Resolve a team name to its color.
 *
 * [EN] Lowercases the name and returns the first color whose key is contained
 * in it; falls back to the default cyan.
 * [PT-BR] Coloca o nome em minúsculas e retorna a primeira cor cuja chave
 * esteja contida nele; usa o ciano padrão como fallback.
 *
 * @param {string} teamName
 * @returns {string} hex color
 */
export function getTeamColor(teamName) {
  if (!teamName) return DEFAULT_TEAM_COLOR;
  const name = String(teamName).toLowerCase();
  for (const key in TEAM_COLORS_MAP) {
    if (name.includes(key)) return TEAM_COLORS_MAP[key];
  }
  return DEFAULT_TEAM_COLOR;
}
