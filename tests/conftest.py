"""
Pytest configuration shared by the whole test suite.

[EN] Isolates the test run from a developer's local .env. Sets an EMPTY (but
present) DATABASE_URL before src.db.database is imported: python-dotenv's
load_dotenv(override=False) will not overwrite an existing value, so a real
Supabase URL in .env is ignored and tests always fall back to SQLite. This
guarantees the suite never connects to a real database.

[PT-BR] Isola a execução dos testes do .env local do dev. Define um
DATABASE_URL VAZIO (porém presente) antes de src.db.database ser importado:
o load_dotenv(override=False) do python-dotenv não sobrescreve um valor
existente, então uma URL real do Supabase no .env é ignorada e os testes
sempre caem no SQLite. Isso garante que a suíte nunca conecte a um banco real.
"""

import os

os.environ["DATABASE_URL"] = ""
os.environ.setdefault("USE_SQLITE", "True")
