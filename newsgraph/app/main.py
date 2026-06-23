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

# No Streamlit Cloud não existe .env: traz o DATABASE_URL dos Secrets do app
# para o os.environ, que é onde persistencia.conexao procura. Localmente o
# bloco é ignorado (sem secrets) e o .env continua valendo.
try:
    if "DATABASE_URL" in st.secrets:
        os.environ.setdefault("DATABASE_URL", str(st.secrets["DATABASE_URL"]))
except Exception:
    pass

from PIL import Image

from app.login import render_login, restaurar_sessao, logout
from app.feed import render_feed

# Pasta servida pelo static serving do Streamlit (.streamlit/config.toml →
# enableStaticServing = true). Os arquivos ficam acessíveis em /app/static/<arquivo>.
_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# O logo como ícone do atalho de tela inicial no celular: apple-touch-icon (iOS) +
# web manifest (Android). O Streamlit não expõe API para isso, então injetamos as
# tags no <head> da PÁGINA (não do iframe do componente) via JS. A aba do navegador
# (favicon) já é resolvida pelo page_icon do set_page_config.
_ICONES_MOBILE_JS = """
<script>
(function () {
  try {
    var doc = window.parent.document;
    if (doc.getElementById('ng-brand-icons')) return;  // injeta uma vez só
    var marca = doc.createElement('meta');
    marca.id = 'ng-brand-icons';
    doc.head.appendChild(marca);
    function add(rel, href, attrs) {
      var l = doc.createElement('link');
      l.rel = rel; l.href = href;
      if (attrs) Object.keys(attrs).forEach(function (k) { l.setAttribute(k, attrs[k]); });
      doc.head.appendChild(l);
    }
    add('apple-touch-icon', 'app/static/icon-180.png', {sizes: '180x180'});
    add('manifest', 'app/static/manifest.json');
    function meta(name, content) {
      var m = doc.createElement('meta');
      m.name = name; m.content = content; doc.head.appendChild(m);
    }
    meta('apple-mobile-web-app-capable', 'yes');
    meta('apple-mobile-web-app-title', 'NewsGraph');
    meta('theme-color', '#0a466b');
  } catch (e) { /* origem cruzada: ignora silenciosamente */ }
})();
</script>
"""


def _injetar_icones_mobile():
    """Coloca o logo como ícone do atalho de tela inicial (iOS + Android)."""
    if st.session_state.get("_icones_ok"):
        return
    st.iframe(_ICONES_MOBILE_JS, height=1)
    st.session_state["_icones_ok"] = True


def main():
    st.set_page_config(
        page_title="NewsGraph",
        page_icon=Image.open(os.path.join(_STATIC_DIR, "icon-192.png")),
        layout="centered",
    )
    _injetar_icones_mobile()

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
