# Arquitetura — F1 Insights Engine

Documento de referência da arquitetura do projeto: como os dados fluem da fonte
externa até o dashboard, quais são as camadas e por que cada decisão técnica foi
tomada.

---

## Visão geral

O **F1 Insights Engine** é uma plataforma analítica de dados de Fórmula 1 construída
em **arquitetura orientada a serviços**, com separação clara entre **ingestão** de
dados (offline) e **leitura** (online). Os dados históricos são extraídos de uma API
pública, normalizados por um pipeline ETL, persistidos em banco relacional e expostos
por uma API REST que alimenta um dashboard SPA.

Princípio central: **o dashboard lê de um banco já populado — não baixa tudo da fonte
a cada acesso.** A telemetria detalhada (FastF1) é a única exceção, processada sob
demanda.

---

## Diagrama de alto nível

```mermaid
flowchart LR
    subgraph Fontes["Fontes externas"]
      J["Jolpica F1 API<br/>(dados históricos)"]
      FF["FastF1<br/>(telemetria)"]
    end

    J -->|extract| ETL["ETL Pipeline<br/>extract · transform · load"]
    ETL -->|persiste| DB[("Supabase<br/>PostgreSQL gerenciado")]
    DB --> API["FastAPI REST<br/>(Render · somente leitura)"]
    FF -->|sob demanda + cache| API
    API -->|JSON| WEB["Frontend SPA<br/>(Vercel) · Plotly"]
    WEB --> USER((Usuário))
```

---

## Camadas e responsabilidades

| Camada | Diretório | Responsabilidade |
| ------ | --------- | ---------------- |
| **Ingestão (ETL)** | `src/etl/` | Extrair da API, transformar para o schema e carregar no banco de forma idempotente |
| **Persistência** | `src/db/` | Modelos ORM (SQLAlchemy async); banco no **Supabase** (PostgreSQL gerenciado) em produção, SQLite localmente |
| **API** | `src/api/` | Endpoints REST somente-leitura + endpoint de telemetria (FastF1) |
| **Apresentação** | `src/web/` | SPA nativa que consome a API e renderiza gráficos interativos (Plotly) |

### Ingestão (ETL)

Pipeline em três etapas bem separadas (Single Responsibility):

- **Extract** — busca paginada na API com *rate limiting* e *retry* com *backoff*
  exponencial.
- **Transform** — converte o JSON aninhado da API em dicionários planos alinhados ao
  schema do banco, com conversões seguras de tipos.
- **Load** — inserção **idempotente** (registros existentes são ignorados por chave
  natural), usando *caches* de lookup em memória para resolução de chaves estrangeiras
  e evitar o padrão N+1.

A orquestração (`run_pipeline`) aceita argumentos de linha de comando para seleção de
temporadas e carga opcional de tempos de volta (alto volume).

### Persistência

SQLAlchemy assíncrono. Em produção o banco é o **Supabase** (PostgreSQL gerenciado),
selecionado via `DATABASE_URL`; localmente cai para **SQLite** por padrão. O schema
cobre **14 tabelas** (13 do domínio de F1 + `telemetry_cache`, memoization da telemetria).

### API

FastAPI assíncrono, com endpoints **somente leitura** (GET), validação e serialização
via Pydantic, paginação/filtros e documentação automática (Swagger). Um endpoint
dedicado expõe telemetria detalhada via FastF1.

### Apresentação

SPA em HTML/CSS/JS puro (sem framework), com roteamento próprio e gráficos via Plotly
(carregado por CDN). Organizada em sete telas analíticas (visão geral, telemetria,
evolução, head-to-head, pit stops, grid e histórico).

---

## Modelo de dados (entidades principais)

```mermaid
erDiagram
    SEASON ||--o{ RACE : tem
    CIRCUIT ||--o{ RACE : sedia
    RACE ||--o{ RACE_RESULT : produz
    DRIVER ||--o{ RACE_RESULT : participa
    CONSTRUCTOR ||--o{ RACE_RESULT : compete
    RACE ||--o{ PIT_STOP : registra
    RACE ||--o{ LAP_TIME : registra
```

> O domínio possui 13 entidades: temporadas, circuitos, pilotos, construtores, corridas,
> resultados, classificação (qualifying), sprint, classificações de pilotos e de
> construtores, pit stops, tempos de volta e status. Há ainda a `telemetry_cache`
> (memoization da telemetria), totalizando 14 tabelas.

---

## Decisões técnicas

| Decisão | Escolha | Justificativa |
| ------- | ------- | ------------- |
| **Frontend** | HTML/CSS/JS puro | Performático, zero build, controle total do design |
| **API** | FastAPI + Uvicorn | Async nativo, tipagem forte (Pydantic), docs automáticas |
| **ORM** | SQLAlchemy async | Abstrai SQLite/PostgreSQL e mantém o código de banco agnóstico |
| **Banco** | Supabase (PostgreSQL) | Gerenciado em produção; SQLite localmente. Troca via `DATABASE_URL` |
| **Carga** | ETL idempotente | Reexecutável com segurança; *caches* de FK evitam N+1 |
| **Telemetria** | FastF1 + cache | Live timing oficial; respostas memoizadas no Supabase |
| **Deploy** | Render (API) + Vercel (front) | Container para FastF1/FastAPI; estático global para a SPA |
| **CI** | GitHub Actions | ruff + pytest (cobertura) + Vitest a cada PR |

---

## Fonte de dados

- **[Jolpica F1 API](https://github.com/jolpica/jolpica-f1)** — sucessora da Ergast;
  dados históricos de F1 (1950–presente).
- **[FastF1](https://docs.fastf1.dev/)** — telemetria detalhada (velocidade, freio,
  marcha, RPM, acelerador, DRS) e dados de sessão, disponíveis a partir de 2018.

---

## Hospedagem e operação (atual)

- **Banco** → **Supabase** (PostgreSQL gerenciado). Acesso apenas pelo backend (papel
  `postgres`); o frontend **não** lê o Supabase direto — o FastAPI é o protagonista.
- **API** → **Render** (container), lendo do Supabase. Um GitHub Action de *keep-alive*
  reduz o cold start do plano gratuito.
- **Frontend** → **Vercel** (estático global). A URL da API é resolvida por ambiente
  (`config.js`); as requisições de cada tela são paralelizadas (`Promise.all`).
- **Telemetria** → FastF1 sob demanda, com memoization no Supabase (`telemetry_cache`).
- **CI** → GitHub Actions: lint + testes + cobertura a cada PR.

### Próximos
- Ingestão agendada/incremental via GitHub Actions.
- Pré-aquecimento do cache de telemetria (o processamento do FastF1 não cabe no plano
  gratuito do Render).
- Endurecimento de segurança (RLS no Supabase) antes da divulgação ampla.
