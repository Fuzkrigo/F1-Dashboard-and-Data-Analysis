"""
FastAPI Application Entry Point.

[EN] Initializes the FastAPI application for the F1 Insights Engine.
Registers the API router and defines the root health-check endpoint.

[PT-BR] Inicializa a aplicação FastAPI do F1 Insights Engine.
Registra o roteador da API e define o endpoint raiz de verificação
de saúde.

Author: Bruno Krieger
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import routes, telemetry
from src.core.logging_config import configure_logging

configure_logging()

app = FastAPI(title="F1 Insights API")

# [EN] Allowed origins come from the ALLOWED_ORIGINS env var (comma-separated).
# The "*" default is fine for local dev; set explicit origins in production.
# [PT-BR] As origens permitidas vêm da env var ALLOWED_ORIGINS (separadas por
# vírgula). O default "*" serve para dev local; defina origens explícitas em prod.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Setup CORS to allow the HTML frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # Read-only, stateless API (no cookies/auth)
    allow_methods=["GET", "OPTIONS"],  # Security: API is Read-Only
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1")
app.include_router(telemetry.router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    Root endpoint — basic welcome message.

    [EN] Returns a simple JSON greeting to confirm the API is running.

    [PT-BR] Retorna uma saudação JSON simples para confirmar que a API
    está funcionando.

    Returns:
        dict: A welcome message. / Uma mensagem de boas-vindas.

    Author: Bruno Krieger
    """
    return {"message": "Welcome to F1 Insights API"}
