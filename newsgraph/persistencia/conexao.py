"""Camada de conexão — lê DATABASE_URL do ambiente e devolve a conexão.

Nenhuma credencial no código: localmente vem do `.env` (no .gitignore), no
GitHub Actions vem do secret `DATABASE_URL`.
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_conexao():
    """Abre e devolve uma conexão psycopg2 com o PostgreSQL (Supabase)."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL não definida. Crie um .env local ou um secret no GitHub."
        )
    return psycopg2.connect(url)
