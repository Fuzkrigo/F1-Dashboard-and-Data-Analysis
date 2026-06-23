import { describe, it, expect } from 'vitest';
import { calcStats } from './stats.js';

describe('calcStats', () => {
  it('aggregates points, wins, podiums, DNFs, average position and races', () => {
    const results = [
      { points: 25, position: 1 },
      { points: 18, position: 2 },
      { points: 0, position: null }, // DNF
    ];
    const s = calcStats(results);
    expect(s.pts).toBe(43);
    expect(s.wins).toBe(1);
    expect(s.pods).toBe(2);
    expect(s.dnfs).toBe(1);
    expect(s.avgPos).toBe('1.5');
    expect(s.racesD).toBe(3);
  });

  it('counts only podium finishes (positions 1-3)', () => {
    const results = [
      { points: 15, position: 3 },
      { points: 10, position: 5 },
    ];
    const s = calcStats(results);
    expect(s.pods).toBe(1);
    expect(s.wins).toBe(0);
  });

  it('handles an empty list', () => {
    const s = calcStats([]);
    expect(s.pts).toBe(0);
    expect(s.wins).toBe(0);
    expect(s.pods).toBe(0);
    expect(s.dnfs).toBe(0);
    expect(s.avgPos).toBe(0);
    expect(s.racesD).toBe(0);
  });
});
