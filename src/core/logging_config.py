"""
Logging Configuration Module.

[EN] Centralizes structured logging setup for the whole application, so the
ETL pipeline and the API share the same format and levels. Modules obtain
their own logger via ``logging.getLogger(__name__)`` and the entrypoints call
``configure_logging()`` once at startup.

[PT-BR] Centraliza a configuração de logging estruturado de toda a aplicação,
para que o pipeline ETL e a API compartilhem o mesmo formato e níveis. Cada
módulo obtém seu logger via ``logging.getLogger(__name__)`` e os entrypoints
chamam ``configure_logging()`` uma vez na inicialização.

Author: Bruno Krieger
"""

import logging
import os

# Structured single-line format: timestamp | level | module | message
# Formato estruturado de uma linha: timestamp | nível | módulo | mensagem
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: int | None = None) -> None:
    """
    Configure root logging with a consistent structured format.

    [EN] Sets the level and format once for the whole process. When ``level``
    is not given, it is read from the ``LOG_LEVEL`` env var (e.g. DEBUG, INFO,
    WARNING), defaulting to INFO. Safe to call from any entrypoint.

    [PT-BR] Define o nível e o formato uma vez para todo o processo. Quando
    ``level`` não é informado, é lido da env var ``LOG_LEVEL`` (ex: DEBUG, INFO,
    WARNING), com padrão INFO. Seguro para chamar de qualquer entrypoint.

    Args:
        level (int | None): Logging level override. / Sobrescrita do nível.

    Author: Bruno Krieger
    """
    if level is None:
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format=_LOG_FORMAT, datefmt=_DATE_FORMAT)
