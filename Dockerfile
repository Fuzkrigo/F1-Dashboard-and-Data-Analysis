# Base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose ports (Documentary only, compose handles mapping)
EXPOSE 8000

# Default command (overridden in docker-compose).
# [EN] Shell form so $PORT (injected by PaaS like Render) is honored; falls back
#      to 8000 locally. [PT-BR] Forma shell para respeitar $PORT (injetado por
#      PaaS como o Render); cai para 8000 localmente.
CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
