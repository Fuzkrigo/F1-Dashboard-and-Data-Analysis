# F1 Insights Engine

![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)
![HTML/JS](https://img.shields.io/badge/Frontend-HTML%2FJS%20SPA-orange.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)

Plataforma analítica de dados históricos e telemetria da Fórmula 1 (1950–Presente), construída em arquitetura orientada a serviços com ETL robusto, API REST assíncrona e dashboard SPA nativo em HTML/CSS/JS com tema Cyber-Racing HUD.

---

## Arquitetura

```
Jolpica F1 API (externa)
        │
        ▼
ETL Pipeline (src/etl/)
  Extract → Transform → Load
        │
        ▼
SQLite / PostgreSQL
        │
        ▼
FastAPI REST API (src/api/)          porta 8000
        │
        ▼
HTML/JS SPA Frontend (src/web/)      porta 3000 (local) / 80 (Docker)
```

### Estrutura de Diretórios

```
F1 Dashboard and Data Analysis/
├── src/
│   ├── api/          # FastAPI: rotas, schemas Pydantic, telemetria FastF1
│   ├── db/           # SQLAlchemy: models ORM e configuração de engine
│   ├── etl/          # Pipeline ETL com backoff exponencial e idempotência
│   └── web/          # Frontend SPA: index.html, style.css, app.js
├── tests/            # Testes pytest (API e ETL)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Como Executar Localmente

### Pré-requisitos
- Python 3.12+
- pip

### Passo 1 — Instalar dependências

```bash
pip install -r requirements.txt
```

### Passo 2 — Popular o banco via ETL

O banco começa vazio. Escolha os anos que deseja analisar.
**Atenção:** a API Jolpica tem rate-limit — comece por poucos anos.

```bash
python -m src.etl.run_pipeline --years 2023 2024 2025
```

Isso gera `f1_insights.db` na raiz automaticamente.

### Passo 3 — Iniciar a API (Terminal 1)

```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

Swagger interativo disponível em: `http://localhost:8000/docs`

### Passo 4 — Servir o Frontend (Terminal 2)

```bash
cd src/web
python -m http.server 3000
```

Abra no browser: `http://localhost:3000`

---

## Como Executar via Docker

Requer Docker e Docker Compose instalados.

```bash
# Copie e preencha as variáveis de ambiente
cp .env.example .env

# Suba todos os serviços (db PostgreSQL + api + web nginx)
docker-compose up --build
```

| Serviço | URL |
|---------|-----|
| Frontend | `http://localhost` |
| API | `http://localhost:8000` |
| Swagger | `http://localhost:8000/docs` |

---

## Testes

```bash
# Windows
$env:PYTHONPATH="."
pytest tests/ -v

# Linux/Mac
PYTHONPATH=. pytest tests/ -v
```

---

## Segurança

- **Secrets:** credenciais via `.env` (nunca commitado). Ver `.env.example`
- **SQL Injection:** SQLAlchemy ORM com queries parametrizadas
- **XSS:** `escapeHTML()` em toda injeção de strings da API no DOM
- **CORS:** API restrita a `GET` e `OPTIONS` apenas
- **Fail-Safe:** erros da API exibem mensagem amigável, sem stack trace exposto

---

Desenvolvido por [Bruno Krieger](https://github.com/BsKrieger) como projeto de portfólio.
