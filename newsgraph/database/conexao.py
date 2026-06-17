# newsgraph/database/conexao.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def obter_conexao():
    """
    Estabelece a conexão com a instância PostgreSQL hospedada no Supabase
    utilizando a URI secreta injetada pelas variáveis de ambiente da aplicação.
    """
    # A URI deve conter o formato: postgresql://postgres:[SENHA]@[HOST]:5432/postgres
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        raise ValueError("A variável de ambiente 'DATABASE_URL' não foi configurada.")
        
    try:
        conexao = psycopg2.connect(database_url)
        return conexao
    except Exception as e:
        print(f"Erro crítico ao conectar no banco de dados: {e}")
        raise e