# PLANEJAMENTO — F1 Insights Engine

| Campo            | Valor                        |
| ---------------- | ---------------------------- |
| **Nome**         | F1 Insights Engine           |
| **Início**       | 2026-04-26                   |
| **Responsável**  | Bruno Krieger                |
| **Status atual** | Pronto para deploy no GitHub |

---

## Resumo do Problema

Dashboard analítico de Fórmula 1 que extrai dados históricos da API Jolpica e telemetria em tempo real da biblioteca FastF1, expõe via API REST (FastAPI), e apresenta ao usuário via frontend SPA nativa em HTML/CSS/JS com tema Cyber-Racing HUD.

O projeto nasceu com dois frontends paralelos (Streamlit e HTML). O HTML evoluiu para uma versão muito mais completa e visualmente rica, tornando o Streamlit obsoleto. A organização foi feita para eliminar esse legado e preparar o repositório para o primeiro push no GitHub.

---

## Decisões Arquiteturais

| Decisão                     | Escolha                               | Justificativa                                                                                            |
| --------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Frontend**                | HTML/CSS/JS puro (SPA)                | Mais performático, sem dependência de servidor Python para UI, design Cyber-HUD impossível via Streamlit |
| **Backend**                 | FastAPI + Uvicorn                     | Async nativo, tipagem forte com Pydantic, docs automáticas via Swagger                                   |
| **Banco local**             | SQLite + aiosqlite                    | Zero config para dev/estudo. Troca para PostgreSQL via env var                                           |
| **Banco prod**              | PostgreSQL 15 (Docker)                | Robusto, via docker-compose                                                                              |
| **Telemetria**              | FastF1 (endpoint dedicado)            | Biblioteca oficial para live timing F1, cache automático                                                 |
| **Orquestração**            | Docker Compose                        | db + api + web (nginx) em um único comando                                                               |
| **Frontend Docker**         | nginx:alpine                          | Leve, serve arquivos estáticos, zero overhead                                                            |
| **Multi-driver telemetria** | `telemetry_v2` (agora `telemetry.py`) | Suporte a N pilotos simultâneos via `drivers: list[str]`                                                 |

---

## Seções do CLAUDE.md aplicadas neste projeto

| Seção                              | Status                                                                                        |
| ---------------------------------- | --------------------------------------------------------------------------------------------- |
| Fluxo 9 fases                      | Aplicado parcialmente (projeto pré-existente, fase de organização pré-deploy)                 |
| SOLID / Clean Code                 | Aplicado — separação clara ETL / API / Frontend                                               |
| Limites de tamanho (50/500 linhas) | `routes.py` próximo do limite — monitorar                                                     |
| Secrets Management                 | `.env` ignorado pelo Git, `.env.example` commitado                                            |
| OWASP — Injection                  | SQLAlchemy ORM (queries parametrizadas)                                                       |
| OWASP — XSS                        | `escapeHTML()` implementado no `app.js`                                                       |
| OWASP — Broken Access Control      | API somente leitura (GET/OPTIONS)                                                             |
| LGPD                               | Não aplicável (dados públicos de F1)                                                          |
| TDD                                | 149 testes passando, 95% cobertura geral — metas do CLAUDE.md atingidas (80% geral, 95% lógica de negócio) |
| Resiliência de caminhos            | ETL e FastF1 cache usam `mkdir(parents=True, exist_ok=True)`                                  |

---

## Roadmap de Desenvolvimento

### Concluído ✓
1. ETL completo: extract (Jolpica API) → transform → load (SQLite/PostgreSQL)
2. API REST com 12 endpoints + telemetria FastF1
3. Frontend HTML SPA com 7 views: Overview, Telemetry, Evolution, H2H, Pit Stops, Grid Analysis, History
4. Docker Compose (db + api + web nginx)
5. Limpeza pré-deploy: remoção Streamlit, duplicatas, lixo
6. TDD completo: 149 testes, 95% cobertura geral, 98–100% na lógica de negócio (ETL)
   - `test_api.py` (31 testes) — API 100% autocontida, SQLite em memória + dependency_overrides
   - `test_transform.py` (42 testes) — 100% cobertura das 12 funções de transformação
   - `test_etl.py` (26 testes) — extract completo com mocks de HTTP
   - `test_load.py` (35 testes) — load completo com DB em memória
   - `test_telemetry.py` (11 testes) — FastF1 mockado, bug de HTTPException corrigido
   - `test_database.py` (4 testes) — branches SQLite/PostgreSQL e gerador get_db

### Próximos passos (pós-deploy)
7. Configurar GitHub Actions (CI: lint + testes + cobertura mínima 80%)
8. Migração Pydantic V2 (silenciar 14 deprecation warnings)
9. Avaliar deploy em plataforma gratuita (Render, Railway ou Fly.io)

---

## Riscos e Pontos de Atenção

| Risco                                           | Probabilidade   | Mitigação                                                 |
| ----------------------------------------------- | --------------- | --------------------------------------------------------- |
| FastF1 sem dados para corridas futuras          | Alta            | Mensagem amigável no frontend ("dados indisponíveis")     |
| API pública Jolpica com rate limit              | Média           | Backoff exponencial implementado no ETL (MAX_RETRIES=3)   |
| `.cache_fastf1/` crescendo (pode passar de 1GB) | Alta            | Ignorado pelo Git, limpar manualmente quando necessário   |
| `routes.py` próximo de 500 linhas               | Média           | Monitorar — dividir em módulos por domínio se ultrapassar |
| CORS com `allow_origins=["*"]`                  | Baixa em estudo | Restringir à URL do frontend em produção real             |

---

## Histórico de Mudanças do Plano

| Data       | Mudança                                         | Motivo                                                          |
| ---------- | ----------------------------------------------- | --------------------------------------------------------------- |
| 2026-04-26 | Remoção total do Streamlit                      | Frontend HTML mais completo, Streamlit obsoleto                 |
| 2026-04-26 | `telemetry_v2.py` renomeado para `telemetry.py` | Eliminar versão v1 (2 drivers fixos) em favor da v2 (N drivers) |
| 2026-04-26 | `API_BASE` corrigido de 8001 para 8000          | Porta 8001 era workaround de sessão de desenvolvimento          |
| 2026-04-26 | `fastf1` adicionado ao `requirements.txt`       | Dependência crítica ausente descoberta na auditoria             |
| 2026-04-26 | nginx adicionado ao docker-compose              | Substitui serviço Streamlit para servir o HTML                  |
| 2026-04-26 | TDD completo: 149 testes, 95% cobertura         | Metas do CLAUDE.md atingidas — bug de HTTPException corrigido em telemetry.py, testes autocontidos com SQLite em memória |
