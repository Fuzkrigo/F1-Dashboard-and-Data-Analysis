/**
 * Driver comparison statistics (Head-to-Head).
 *
 * [EN] Pure aggregation over a list of race results for one driver: points,
 * wins, podiums, DNFs, average finishing position and number of races. No DOM.
 *
 * [PT-BR] Agregação pura sobre uma lista de resultados de um piloto: pontos,
 * vitórias, pódios, DNFs, posição média de chegada e número de corridas. Sem DOM.
 *
 * Author: Bruno Krieger
 */

/**
 * @typedef {Object} DriverStats
 * @property {number} pts    Total points / Pontos totais
 * @property {number} wins   Wins (position === 1) / Vitórias
 * @property {number} pods   Podiums (positions 1-3) / Pódios
 * @property {number} dnfs   DNFs (null position) / Abandonos
 * @property {(string|number)} avgPos  Average finishing position / Posição média
 * @property {number} racesD Number of races / Número de corridas
 */

/**
 * Aggregate stats from a driver's race results.
 *
 * @param {Array<{points?: number, position?: number|null}>} rList
 * @returns {DriverStats}
 */
export function calcStats(rList) {
  const pts = rList.reduce((acc, r) => acc + (r.points || 0), 0);
  const wins = rList.filter((r) => r.position === 1).length;
  const pods = rList.filter((r) => r.position > 0 && r.position <= 3).length;

  // DNF: a null finishing position (did not finish).
  // DNF: posição de chegada nula (não terminou).
  const dnfs = rList.filter((r) => r.position == null).length;

  const validPos = rList.filter((r) => r.position > 0);
  const avgPos =
    validPos.length > 0
      ? (validPos.reduce((acc, r) => acc + r.position, 0) / validPos.length).toFixed(1)
      : 0;

  const racesD = rList.length;

  return { pts, wins, pods, dnfs, avgPos, racesD };
}
