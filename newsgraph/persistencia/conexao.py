"""Conexão PostgreSQL (Supabase).

Gerencia a conexão com o banco. String de conexão e credenciais ficam em
variáveis de ambiente / secrets — nunca no código — lidas tanto pelo GitHub
Actions (offline) quanto pelo Streamlit (online). Driver: psycopg.
"""
