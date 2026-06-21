"""Entrada do app (online) — Streamlit.

Mundo ONLINE: só lê do banco, monta o grafo em memória e recomenda. Nenhuma
coleta de RSS ou chamada de LLM acontece aqui.

Rodar (a partir da pasta `newsgraph/`):
    streamlit run app/main.py
Requer `DATABASE_URL` no `.env`.
"""

import os
import sys

# Garante que a raiz do projeto (newsgraph/) esteja no path: o Streamlit executa
# este arquivo diretamente e só adiciona a pasta app/ ao sys.path por padrão.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

import streamlit as st

from app.login import render_login, restaurar_sessao, logout
from app.feed import render_feed


def main():
    st.set_page_config(page_title="NewsGraph", layout="centered")

    # Reconstrói o login a partir da URL quando a sessão foi zerada por um F5.
    restaurar_sessao()

    if "usuario_id" not in st.session_state:
        render_login()
        return

    with st.sidebar:
        st.write(f"Logado como **{st.session_state['usuario_nome']}**")
        if st.button("Sair"):
            logout()

    render_feed(st.session_state["usuario_id"], st.session_state["usuario_nome"])


# `streamlit run app/main.py` executa este arquivo como __main__.
if __name__ == "__main__":
    main()
