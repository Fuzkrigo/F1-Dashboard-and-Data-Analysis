"""
FastAPI Application Entry Point.

[EN] Initializes the FastAPI application for the F1 Insights Engine.
Registers the API router and defines the root health-check endpoint.

[PT-BR] Inicializa a aplicação FastAPI do F1 Insights Engine.
Registra o roteador da API e define o endpoint raiz de verificação
de saúde.

Author: Bruno Krieger
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import routes, telemetry

app = FastAPI(title="F1 Insights API")

# Setup CORS to allow the HTML frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits all origins (adjust to Specific URLs in prod)
    allow_credentials=True,
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
