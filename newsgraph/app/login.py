"""Identificação do usuário (login simples).

Sem senha: o usuário digita o nome para entrar, ou cria uma conta nova num
pop-up. O `usuario_id` resultante alimenta o motor de recomendação. Toda a
escrita passa pela camada de repositório.
"""

import streamlit as st

from persistencia.conexao import get_conexao
from persistencia import repositorio


def render_login():
    """Renderiza a tela de login e grava `usuario_id`/`usuario_nome` na sessão."""
    st.title("NewsGraph")
    st.caption("Recomendação de notícias financeiras baseada em grafos.")

    nome = st.text_input("Insira seu nome de usuário")
    if st.button("Entrar", type="primary"):
        _entrar_por_nome(nome)

    if st.button("Criar usuário"):
        _dialog_criar_usuario()


def _entrar_por_nome(nome):
    nome = (nome or "").strip()
    if not nome:
        st.warning("Digite seu nome de usuário.")
        return

    conn = get_conexao()
    try:
        with conn.cursor() as cur:
            user = repositorio.buscar_usuario_por_nome(cur, nome)
    finally:
        conn.close()

    if user is None:
        st.error(f"Usuário '{nome}' não encontrado. Use 'Criar usuário' para criar um novo.")
        return
    _login(user["id"], user["nome"])


@st.dialog("Escolha seu nome de usuário")
def _dialog_criar_usuario():
    """Pop-up de criação de usuário."""
    novo = st.text_input("Nome de usuário", key="novo_usuario_nome")
    if st.button("Criar e entrar", type="primary"):
        nome = (novo or "").strip()
        if not nome:
            st.warning("Digite um nome.")
            return

        conn = get_conexao()
        try:
            with conn.cursor() as cur:
                existente = repositorio.buscar_usuario_por_nome(cur, nome)
                usuario_id = existente["id"] if existente else repositorio.salvar_usuario(cur, nome)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        _login(usuario_id, nome)


def _login(usuario_id, nome):
    st.session_state["usuario_id"] = usuario_id
    st.session_state["usuario_nome"] = nome
    # Guarda o id na URL para o login sobreviver ao F5 (o Streamlit zera a
    # sessão a cada recarregamento da página, mas os query params persistem).
    st.query_params["uid"] = str(usuario_id)
    st.rerun()


def restaurar_sessao():
    """Recupera o usuário a partir da URL após um F5 (sessão zerada)."""
    if "usuario_id" in st.session_state:
        return
    uid = st.query_params.get("uid")
    if not uid:
        return
    conn = get_conexao()
    try:
        with conn.cursor() as cur:
            user = repositorio.buscar_usuario_por_id(cur, int(uid))
    finally:
        conn.close()
    if user is None:
        st.query_params.clear()  # id obsoleto
        return
    st.session_state["usuario_id"] = user["id"]
    st.session_state["usuario_nome"] = user["nome"]


def logout():
    """Limpa a sessão e volta para a tela de login."""
    for chave in ("usuario_id", "usuario_nome", "recs", "idx", "quantos", "ocultas", "compartilhar", "reacao"):
        st.session_state.pop(chave, None)
    st.query_params.clear()
    st.rerun()
