# CHECKLIST — F1 Insights Engine

**Projeto:** F1 Insights Engine | **Data:** 2026-04-26

**Legenda:**
| Marcador | Significado                   |
| -------- | ----------------------------- |
| `- [ ]`  | Pendente                      |
| `- [x]`  | Concluído                     |
| `- [~]`  | Não se aplica a este projeto  |
| `- [!]`  | Bloqueado ou com problema     |
| `- [?]`  | Em dúvida, precisa de decisão |

---

## Fase 1 — Briefing e Diagnóstico
- [x] Ideia inicial recebida e escopo definido
- [x] Viabilidade técnica validada
- [x] Auditoria completa do projeto existente realizada

## Fase 2 — Resumo Executivo e Roadmap
- [x] Resumo executivo documentado (ver PLANEJAMENTO.md)
- [x] Roadmap de desenvolvimento definido
- [x] Stack e arquitetura justificadas

## Fase 3 — Documentação Técnica
- [x] Arquitetura documentada (ETL → API → Frontend)
- [x] Decisões arquiteturais registradas no PLANEJAMENTO.md
- [x] Riscos e pontos de atenção documentados
- [~] Design System formal — não aplicável (CSS custom com variáveis CSS)
- [~] Fluxogramas — não aplicável para este escopo

## Fase 4 — Apresentação
- [~] Apresentação corporativa — projeto pessoal/portfólio, não aplicável
- [~] Apresentação comercial — não aplicável

## Fase 5 — Plan Mode
- [x] Plan Mode ativado antes da implementação
- [x] Plano aprovado pelo usuário antes da execução

## Fase 6 — TDD
- [x] Testes existentes validados (test_api.py, test_etl.py)
- [x] Cobertura medida com pytest-cov (95% geral)
- [x] Meta de 80% cobertura geral atingida (95%)
- [x] Meta de 95% cobertura na lógica de negócio (transform: 100%, extract: 100%, load: 98%)
- [x] Todos os arquivos acima da meta de 80% (database: 100%, models: 93%, routes: 81%, telemetry: 90%)
- [x] Bug em telemetry.py corrigido (HTTPException sendo engolido por catch genérico)
- [x] Testes de API agora 100% autocontidos (SQLite em memória + dependency_overrides)
- [x] Total: 149 testes passando em ~8s

## Fase 7 — Implementação

### Limpeza pré-deploy
- [x] `.gitignore` atualizado (`*.db`, `*.log`, `.cache_fastf1/`)
- [x] Bancos de dados removidos do repositório (`f1_insights.db`, `f1_data.db`)
- [x] Logs removidos do repositório
- [x] `src/dashboard/` (Streamlit) removido completamente
- [x] `.streamlit/` removido
- [x] `src/api/main_v2.py` (duplicata) removido
- [x] `src/api/telemetry.py` (v1) removido
- [x] `src/api/telemetry_v2.py` renomeado para `src/api/telemetry.py`
- [x] `src/api/main.py` import atualizado (`telemetry_v2` → `telemetry`)
- [x] Arquivos lixo removidos (`_fix_pydantic.py`, `recover.py`, `test_render.txt`, `_debug_db.py`)
- [x] `src/web/js/app.js` — `API_BASE` corrigido (8001 → 8000)
- [x] `requirements.txt` atualizado (removido Streamlit/tornado/protobuf, adicionado fastf1)
- [x] `docker-compose.yml` atualizado (Streamlit → nginx)

### Estrutura final
- [x] `src/api/` — 4 arquivos (main, routes, schemas, telemetry)
- [x] `src/db/` — 2 arquivos (database, models)
- [x] `src/etl/` — 4 arquivos (extract, transform, load, run_pipeline)
- [x] `src/web/` — 3 arquivos (index.html, style.css, app.js)
- [x] `tests/` — 5 arquivos (test_api, test_database, test_etl, test_load, test_telemetry, test_transform)

## Fase 8 — Refatoração
- [x] Streamlit eliminado
- [x] Duplicatas de API eliminadas
- [x] Dependências desnecessárias removidas
- [ ] Variáveis não usadas no `app.js` (hints do TypeScript) — baixa prioridade
- [?] `routes.py` próximo de 500 linhas — avaliar divisão por domínio

## Fase 9 — Revisão de Segurança (OWASP Top 10)

### A01 — Broken Access Control
- [x] API somente leitura (GET/OPTIONS via CORS)
- [x] Sem endpoints de escrita expostos
- [~] Autenticação/autorização — não aplicável (dados públicos)

### A02 — Cryptographic Failures
- [~] Dados sensíveis em repouso — não aplicável (dados públicos F1)
- [~] TLS — gerenciado pelo reverse proxy em produção

### A03 — Injection
- [x] SQLAlchemy ORM (sem SQL raw)
- [x] Queries parametrizadas em todos os endpoints

### A04 — Insecure Design
- [x] Rate limiting no ETL (backoff exponencial)
- [ ] Rate limiting nos endpoints da API — não implementado ainda

### A05 — Security Misconfiguration
- [x] `.env` no `.gitignore`
- [x] `.env.example` com placeholders
- [ ] CORS `allow_origins=["*"]` — restringir em produção real
- [ ] Headers de segurança (CSP, X-Frame-Options) — pendente

### A06 — Vulnerable Components
- [x] Dependências com versões mínimas pinadas (pillow, urllib3)
- [x] `.snyk` configurado

### A07 — Authentication Failures
- [~] Autenticação — não aplicável para este projeto

### A08 — Software and Data Integrity
- [x] `.gitguardian.yaml` configurado para secret scanning

### A09 — Security Logging
- [ ] Logs estruturados — uvicorn default apenas
- [~] Alertas de segurança — não aplicável para projeto de estudo

### A10 — Exceptional Conditions
- [x] Erros tratados em todos os endpoints (try/except com HTTPException)
- [x] Erros do FastF1 isolados por piloto (falha em um não cancela os outros)

---

## Pré-deploy GitHub

- [x] `.gitignore` protegendo `.env`, `*.db`, `*.log`, `.cache_fastf1/`
- [x] `.env.example` commitado com placeholders
- [x] Sem secrets no código
- [x] Sem binários grandes (bancos removidos)
- [x] PLANEJAMENTO.md criado
- [x] CHECKLIST.md criado
- [x] PROXIMOS_PASSOS.md criado
- [x] README.md atualizado (Streamlit removido)
- [x] `pytest tests/` passando 100% (149 testes, 95% cobertura)
- [ ] `git init` e primeiro commit
- [ ] Repositório criado no GitHub e push inicial

---

**Progresso:** 51 de 53 itens concluídos (96%)
