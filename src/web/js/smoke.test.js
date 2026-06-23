import { describe, it, expect } from 'vitest';

// [EN] Smoke test: proves the Vitest toolchain runs. It will be replaced by
//      real unit tests once the pure-logic modules are extracted (R3.2 PR2).
// [PT-BR] Teste smoke: prova que a toolchain do Vitest roda. Sera substituido
//         por testes unitarios reais quando os modulos de logica pura forem
//         extraidos (R3.2 PR2).
describe('toolchain', () => {
  it('runs vitest', () => {
    expect(1 + 1).toBe(2);
  });
});
