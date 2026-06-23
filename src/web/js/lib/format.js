/**
 * Formatting / sanitization helpers.
 *
 * [EN] Pure helpers for escaping HTML (XSS mitigation), formatting lap times
 * and clamping numeric arrays to 3 decimals. No DOM dependencies.
 *
 * [PT-BR] Helpers puros para escapar HTML (mitigação de XSS), formatar tempos
 * de volta e arredondar arrays numéricos para 3 casas. Sem dependências de DOM.
 *
 * Author: Bruno Krieger
 */

/**
 * Escape HTML-significant characters to mitigate XSS.
 * Higieniza caracteres especiais de HTML para mitigar XSS.
 *
 * @param {*} str
 * @returns {string}
 */
export function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Format a duration in seconds as "m:ss.mmm".
 * Formata uma duração em segundos como "m:ss.mmm".
 *
 * @param {number} sec
 * @returns {string} empty string for falsy input
 */
export function formatLapTime(sec) {
  if (!sec) return '';
  const m = Math.floor(sec / 60);
  const s = (sec % 60).toFixed(3).padStart(6, '0');
  return `${m}:${s}`;
}

/**
 * Round every numeric value in an array to 3 decimals, keeping non-numbers.
 * Arredonda cada valor numérico de um array para 3 casas, mantendo não-números.
 *
 * @param {Array} arr
 * @returns {Array} empty array for falsy input
 */
export function clampDec(arr) {
  return arr
    ? arr.map((v) => (typeof v === 'number' ? Number(v.toFixed(3)) : v))
    : [];
}
