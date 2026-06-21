# Próximos Passos — F1 Insights Engine

> Documento de orientação criado após auditoria completa contra o `CLAUDE.md` global. Lista o que ainda falta antes do deploy no GitHub e o que pode ser feito como evolução pós-deploy.

**Estado atual (2026-04-26):**
- ✅ **149 testes passando, 95% de cobertura geral**
- ✅ Lógica de negócio (ETL): 98–100% de cobertura
- ✅ Todos os arquivos acima da meta de 80% (database: 100%, telemetry: 90%, routes: 81%)
- ✅ Testes da API são autocontidos (SQLite em memória + dependency_overrides)
- ✅ Streamlit removido completamente
- ✅ Duplicatas e arquivos lixo eliminados
- ✅ `.gitignore`, `requirements.txt`, `docker-compose.yml`, `README.md` atualizados
- ✅ `PLANEJAMENTO.md` e `CHECKLIST.md` criados

---

## 🚦 Bloco 1 — ANTES do primeiro push no GitHub

> Esses itens são pré-requisitos imediatos. Faça antes do `git init`.

### 1.1 Verificação manual da limpeza

- [ ] Rodar manualmente:
  ```bash
  ls -la "F1 Dashboard and Data Analysis/"
  ```
  Confirmar que **NÃO existem**: `f1_insights.db`, `f1_data.db`, `*.log`, `_fix_pydantic.py`, `recover.py`, `test_render.txt`, `_debug_db.py`, `src/dashboard/`, `.streamlit/`.

- [ ] Verificar que o `.cache_fastf1/` está no `.gitignore` (mesmo que existindo localmente, não vai para o repo).

### 1.2 Validação final

- [ ] Subir API: `python -m uvicorn src.api.main:app --reload --port 8000`
- [ ] Repopular banco: `python -m src.etl.run_pipeline --years 2023 2024 2025`
- [ ] Subir frontend: `cd src/web && python -m http.server 3000`
- [ ] Abrir `http://localhost:3000` e testar **todas as 7 abas**: Visão Geral, Telemetria, Evolução, H2H, Pit Stops, Grid Analysis, Histórico
- [ ] Confirmar que telemetria responde sem 422

### 1.3 Git e GitHub

- [ ] `git init` na raiz
- [ ] `git add .` (verificar que `.env`, `*.db`, `*.log`, `.cache_fastf1/` estão IGNORADOS no `git status`)
- [ ] Primeiro commit: mensagem descritiva ("initial commit: F1 Insights Engine — ETL + FastAPI + HTML SPA")
- [ ] Criar repo no GitHub
- [ ] `git push -u origin main`

### 1.4 Secret scanning antes do push

- [ ] Rodar `gitleaks` ou similar para garantir que nenhum segredo foi commitado:
  ```bash
  pip install gitleaks  # ou usar Docker
  gitleaks detect --source . --verbose
  ```
- [ ] Conferir manualmente que `.env` não foi staged: `git ls-files | grep .env` → deve retornar APENAS `.env.example`

---

## 🛠️ Bloco 2 — Melhorias de qualidade de código (curto prazo, pós-deploy)

> Itens de polimento. Não bloqueiam o deploy mas são dívida técnica conhecida.

### 2.1 Migração Pydantic V2 (14 warnings)

Os schemas em `src/api/schemas.py` usam `class Config: orm_mode = True` (Pydantic V1 style), gerando 14 deprecation warnings. **Vão quebrar quando Pydantic V3 sair.**

- [ ] Substituir por `model_config = ConfigDict(from_attributes=True)` em todas as 14 classes:
  - `Circuit`, `Driver`, `Constructor`, `Race`, `RaceResult`, `RaceResultWithNames`,
    `QualifyingResult`, `DriverStanding`, `ConstructorStanding`, `PitStop`, `Season`,
    `SprintResult`, `LapTime`, `Status`

### 2.2 Limpeza de variáveis não usadas no `app.js`

A IDE está sinalizando 12 hints de variáveis declaradas mas não usadas:
- linhas 156, 172, 509–510, 652, 896, 969, 1463, 1772, 1809
- [ ] Revisar e remover ou marcar com `_` se forem placeholders intencionais

### 2.3 `routes.py` próximo do limite (149 linhas, 500 stmts)

O CLAUDE.md tem limite de 500 linhas por arquivo. Este está OK por enquanto (149 linhas físicas), mas se crescer, considerar dividir em:
- `routes/seasons_circuits.py`
- `routes/drivers_constructors.py`
- `routes/races_results.py`
- `routes/standings_pits_laps.py`

---

## 🔒 Bloco 3 — Segurança (CLAUDE.md — OWASP Top 10 2025)

### 3.1 CORS

Atualmente `allow_origins=["*"]` em `src/api/main.py:23`. Aceitável para projeto de estudo, mas em deploy real:
- [ ] Restringir a `["http://localhost", "https://seu-dominio.com"]`
- [ ] Mover para variável de ambiente

### 3.2 Headers de segurança

- [ ] Adicionar middleware com:
  - `Content-Security-Policy` (CSP)
  - `X-Frame-Options: DENY`
  - `Strict-Transport-Security` (em HTTPS)
  - `X-Content-Type-Options: nosniff`

### 3.3 Rate limiting na API

- [ ] Adicionar `slowapi` ou similar nos endpoints públicos para evitar DoS
- [ ] Configurar limite razoável (ex: 60 req/min por IP)

### 3.4 Logs estruturados

Atualmente apenas o log default do uvicorn. CLAUDE.md pede:
- [ ] Logs em formato JSON (lib `python-json-logger`)
- [ ] Correlation ID por request
- [ ] Logar tentativas de acesso a IDs inválidos (sinal de varredura)

---

## 🧪 Bloco 4 — Testes (cobertura adicional)

### 4.1 `routes.py` (81% → 90%)

Linhas faltantes são paths de "404 não encontrado" raros e detalhes de algumas queries. Subir para 90%:
- [ ] Testes para 404 explicitamente em `/results/`, `/qualifying/`, etc. com IDs inexistentes
- [ ] Testes de paginação (limit/skip extremos)

### 4.2 `telemetry.py` (90% → 95%)

Cobrir paths de erro do FastF1 mais finamente:
- [ ] Mock de `pd.isna(LapTime)` retornando True (driver válido mas sem volta válida)
- [ ] Mock de erro `KeyError` específico do FastF1

### 4.3 Testes E2E do frontend

Atualmente zero cobertura do JS. CLAUDE.md menciona testes E2E para "fluxos críticos do usuário".
- [ ] Considerar Playwright ou Cypress para automação
- [ ] Testar pelo menos: Overview load, troca de season, geração de telemetria

---

## 🚀 Bloco 5 — DevOps e CI/CD (médio prazo)

### 5.1 GitHub Actions — CI

- [ ] Criar `.github/workflows/ci.yml` rodando em cada PR:
  - Lint (`ruff` ou `flake8`)
  - Testes (`pytest --cov`)
  - Falhar se cobertura < 80%
  - Secret scanning (gitleaks)

### 5.2 Pre-commit hooks

- [ ] Configurar `pre-commit` com:
  - `ruff` (lint + format Python)
  - `prettier` (lint JS/CSS/HTML)
  - `gitleaks` (secrets)
  - `pytest -x` rápido (smoke)

### 5.3 Deploy

Opções gratuitas para projeto de portfólio:
- [ ] **API:** Render.com (free tier) ou Fly.io
- [ ] **Frontend:** Cloudflare Pages, Netlify, ou GitHub Pages
- [ ] **Banco:** Supabase ou Neon (Postgres free tier)
- [ ] Configurar `API_BASE` no `app.js` via variável de build/deploy (não hardcoded)

---

## 📝 Bloco 6 — Documentação adicional

- [ ] Adicionar **diagrama de arquitetura** ao README (ferramenta: Mermaid, embedded no Markdown)
- [ ] **CONTRIBUTING.md** se for aceitar PRs externos
- [ ] **CHANGELOG.md** para versionamento (Keep a Changelog format)
- [ ] **LICENSE** (MIT recomendado para portfólio)

---

## 🎓 Bloco 7 — Melhorias de produto (longo prazo)

Ideias para evolução futura:

- [ ] **Cache na API**: Redis para queries frequentes (standings de seasons antigas não mudam)
- [ ] **WebSocket** para telemetria ao vivo durante GPs reais
- [ ] **Comparação histórica**: "Como Hamilton em Mônaco 2019 vs Verstappen em Mônaco 2024"
- [ ] **Predição com ML**: modelo simples prevendo posição final baseado em grid + práticas
- [ ] **Mobile app**: React Native ou Flutter consumindo a mesma API
- [ ] **i18n**: suporte a EN além de PT-BR no frontend

---

## ✅ Resumo: prioridade recomendada

**Faça AGORA (Bloco 1):**
1. Verificação manual de limpeza
2. Validação E2E manual
3. `git init` + push para o GitHub

**Faça em até 2 semanas (Bloco 2 + 5.1):**
1. Migração Pydantic V2 (silenciar 14 warnings)
2. GitHub Actions com CI básico

**Faça quando quiser ir para produção real (Bloco 3 + 5.3):**
1. Hardening de segurança (CORS, headers, rate limit)
2. Deploy em plataforma cloud

**Backlog livre (Bloco 4, 6, 7):**
- Tudo o resto, atacar conforme curiosidade ou necessidade

---

**Última atualização:** 2026-04-26
**Próxima revisão sugerida:** após primeiro push no GitHub
