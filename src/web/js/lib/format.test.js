import { describe, it, expect } from 'vitest';
import { escapeHTML, formatLapTime, clampDec } from './format.js';

describe('escapeHTML', () => {
  it('escapes HTML-significant characters', () => {
    expect(escapeHTML('<script>')).toBe('&lt;script&gt;');
    expect(escapeHTML('a & b')).toBe('a &amp; b');
    expect(escapeHTML('"quoted"')).toBe('&quot;quoted&quot;');
    expect(escapeHTML("it's")).toBe('it&#039;s');
  });

  it('returns empty string for falsy input', () => {
    expect(escapeHTML('')).toBe('');
    expect(escapeHTML(null)).toBe('');
    expect(escapeHTML(undefined)).toBe('');
  });
});

describe('formatLapTime', () => {
  it('formats seconds as m:ss.mmm', () => {
    expect(formatLapTime(90.5)).toBe('1:30.500');
    expect(formatLapTime(63.2)).toBe('1:03.200');
  });

  it('returns empty string for falsy input', () => {
    expect(formatLapTime(0)).toBe('');
    expect(formatLapTime(null)).toBe('');
  });
});

describe('clampDec', () => {
  it('rounds numbers to 3 decimals and keeps non-numbers', () => {
    expect(clampDec([1.23456, 2])).toEqual([1.235, 2]);
    expect(clampDec(['a', 1.5555])).toEqual(['a', 1.556]);
  });

  it('returns an empty array for falsy input', () => {
    expect(clampDec(null)).toEqual([]);
    expect(clampDec(undefined)).toEqual([]);
  });
});
