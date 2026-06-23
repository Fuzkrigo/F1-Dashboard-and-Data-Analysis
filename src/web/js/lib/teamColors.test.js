import { describe, it, expect } from 'vitest';
import { getTeamColor, TEAM_COLORS_MAP } from './teamColors.js';

describe('getTeamColor', () => {
  it('returns the exact color for a known team', () => {
    expect(getTeamColor('Red Bull')).toBe('#3671C6');
    expect(getTeamColor('McLaren')).toBe('#FF8000');
    expect(getTeamColor('Ferrari')).toBe('#F91536');
  });

  it('is case-insensitive', () => {
    expect(getTeamColor('FERRARI')).toBe('#F91536');
    expect(getTeamColor('mercedes')).toBe('#6CD3BF');
  });

  it('matches by substring (full team name)', () => {
    expect(getTeamColor('Red Bull Racing')).toBe('#3671C6');
    expect(getTeamColor('Scuderia Ferrari')).toBe('#F91536');
  });

  it('falls back to default cyan for unknown or empty input', () => {
    expect(getTeamColor('Unknown Team')).toBe('#00F0FF');
    expect(getTeamColor('')).toBe('#00F0FF');
    expect(getTeamColor(null)).toBe('#00F0FF');
    expect(getTeamColor(undefined)).toBe('#00F0FF');
  });

  it('exposes the color map', () => {
    expect(TEAM_COLORS_MAP['mclaren']).toBe('#FF8000');
  });
});
