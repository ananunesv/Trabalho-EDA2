"""Feed + página de leitura navegável + interações.

O feed lista o Top-N do motor em cartões resumidos. "Ler mais" abre a notícia
inteira numa página própria (resumo completo em parágrafos), onde o usuário pode
navegar entre as recomendações com as setas ‹ ›, voltar para a anterior, e
curtir, compartilhar ou marcar como sem relação. Cada interação volta ao banco
via repositório e refina as sementes da próxima recomendação.
"""

import json
import re

import streamlit as st

from persistencia.conexao import get_conexao
from persistencia import repositorio
from recomendacao import motor
import config

# Tamanho do trecho exibido no cartão antes do "…"; o texto inteiro fica na
# página de leitura ("Ler mais").
_LIMITE_TRECHO = 280
_FRASES_POR_PARAGRAFO = 3

# Caracteres que o Streamlit interpreta como markdown/LaTeX. Sem escapar, um
# "US$ ... US$" no texto vira fórmula (texto verde). A barra invertida vem
# primeiro para não escapar as barras que nós mesmos inserimos.
_MD_ESPECIAIS = ("\\", "`", "*", "_", "$", "~", "[", "]")


def _escapar_md(texto):
    """Escapa caracteres de markdown para o texto da notícia sair literal."""
    for ch in _MD_ESPECIAIS:
        texto = texto.replace(ch, "\\" + ch)
    return texto


def _em_paragrafos(texto):
    """Quebra um resumo em parágrafos agrupando frases (o HTML já foi limpo)."""
    texto = (texto or "").strip()
    frases = [f for f in re.split(r"(?<=[.!?])\s+", texto) if f]
    if not frases:
        return [texto] if texto else []
    return [
        " ".join(frases[i:i + _FRASES_POR_PARAGRAFO])
        for i in range(0, len(frases), _FRASES_POR_PARAGRAFO)
    ]


def _trecho(texto):
    """Devolve (trecho, foi_truncado): notícias grandes ganham '…' no cartão."""
    texto = (texto or "").strip()
    if len(texto) <= _LIMITE_TRECHO:
        return texto, False
    corte = texto[:_LIMITE_TRECHO].rsplit(" ", 1)[0]
    return corte + "…", True


def render_feed(usuario_id, usuario_nome):
    """Renderiza o feed — ou a página de leitura, se houver notícia aberta."""
    if st.session_state.get("idx") is not None and st.session_state.get("recs"):
        _render_leitura(usuario_id)
        return

    st.title("For You")
    st.caption(f"Recomendações para **{usuario_nome}** — quanto mais você interage, melhor fica.")

    # "Pular": notícias que o usuário mandou sumir com "Procurar mais notícias".
    # Vivem só na sessão (não vão ao banco) e somem do feed sem virar lidas.
    ocultas = st.session_state.setdefault("ocultas", set())
    pagina = config.TOP_N

    conn = get_conexao()
    try:
        with conn.cursor() as cur:
            # Pede uma a mais do que cabe na página para saber se ainda há próximas.
            recomendacoes = motor.recomendar(
                cur, usuario_id, top_n=pagina + 1, ocultas=ocultas
            )
    finally:
        conn.close()

    if not recomendacoes:
        if ocultas:
            st.info("Você passou por todas as recomendações do momento.")
            if st.button("Recomeçar do topo", use_container_width=True):
                ocultas.clear()
                st.rerun()
        else:
            st.info("Nenhuma notícia disponível. Rode a coleta (pipeline.run_coleta) primeiro.")
        return

    if not any(r["personalizada"] for r in recomendacoes):
        st.warning(
            "Você ainda não interagiu com nenhuma notícia. "
            "Mostrando as mais recentes — leia uma para começar a personalizar."
        )

    tem_mais = len(recomendacoes) > pagina
    pagina_atual = recomendacoes[:pagina]

    for i, rec in enumerate(pagina_atual):
        _render_card(rec, i, pagina_atual, usuario_id)

    # "Procurar mais notícias": as exibidas agora ficam invisíveis (sem virar
    # lidas/dislike) e a próxima leva do ranking surge no lugar.
    if tem_mais:
        if st.button("Procurar mais notícias", use_container_width=True):
            ocultas.update(r["noticia_id"] for r in pagina_atual)
            st.rerun()
    else:
        st.caption("Você chegou ao fim das recomendações.")
        if ocultas and st.button("Recomeçar do topo", use_container_width=True):
            ocultas.clear()
            st.rerun()


def _render_card(rec, indice, recomendacoes, usuario_id):
    """Cartão resumido: título, trecho com '…' e botões de ação."""
    with st.container(border=True):
        st.markdown(f"### {_escapar_md(rec['titulo'])}")

        linha = rec["fonte"]
        if rec["personalizada"] and rec["score"] is not None:
            linha += f"  ·  afinidade (gargalo): **{rec['score']:.3f}**  ·  {rec['saltos']} salto(s)"
            if rec.get("recencia") is not None and rec["recencia"] < 1.0:
                linha += f"  ·  recência ×{rec['recencia']:.2f}"
        st.caption(linha)

        trecho, _ = _trecho(rec["resumo"])
        if trecho:
            st.write(_escapar_md(trecho))

        nid = rec["noticia_id"]
        if st.button("Ler mais", key=f"ler_{nid}", type="primary"):
            _abrir_leitura(recomendacoes, indice, usuario_id)


def _render_leitura(usuario_id):
    """Página de leitura: navegação por setas + resumo completo + reações."""
    recs = st.session_state["recs"]
    idx = st.session_state["idx"]
    rec = recs[idx]

    nav_esq, nav_meio, nav_dir = st.columns([1, 2, 1])
    if nav_esq.button("‹ Anterior", disabled=(idx == 0), use_container_width=True):
        st.session_state["idx"] = idx - 1
        st.rerun()
    nav_meio.markdown(
        f"<div style='text-align:center'>notícia {idx + 1} de {len(recs)}</div>",
        unsafe_allow_html=True,
    )
    if nav_dir.button("Próxima ›", disabled=(idx == len(recs) - 1), use_container_width=True):
        st.session_state["idx"] = idx + 1
        st.rerun()

    if st.button("Voltar ao feed"):
        _fechar_leitura()
        st.rerun()

    st.title(_escapar_md(rec["titulo"]))
    st.caption(rec["fonte"])

    for paragrafo in _em_paragrafos(rec["resumo"]):
        st.write(_escapar_md(paragrafo))

    if rec["link"]:
        st.markdown(f"[Abrir matéria original]({rec['link']})")

    st.divider()
    nid = rec["noticia_id"]
    c1, c2, c3 = st.columns(3)
    if c1.button("Gostei", key=f"r_like_{nid}", type="primary", use_container_width=True):
        _registrar(usuario_id, nid, "like")
    if c2.button("Compartilhar", key=f"r_share_{nid}", type="primary", use_container_width=True):
        _compartilhar(usuario_id, nid, rec["link"])
    if c3.button("Não tem a ver", key=f"r_dislike_{nid}", type="primary", use_container_width=True):
        _registrar(usuario_id, nid, "dislike")

    # Após "Compartilhar": painel de copiar link (só para a notícia aberta agora).
    compart = st.session_state.get("compartilhar")
    if compart and compart[0] == nid:
        _painel_copiar_link(compart[1])


def _abrir_leitura(recomendacoes, indice, usuario_id):
    """Abrir para ler conta como 'clique' (sinal fraco positivo — o antigo 'Li')."""
    _gravar(usuario_id, recomendacoes[indice]["noticia_id"], "clique")
    st.session_state["recs"] = recomendacoes
    st.session_state["idx"] = indice
    st.rerun()


def _fechar_leitura():
    st.session_state["recs"] = None
    st.session_state["idx"] = None
    st.session_state.pop("compartilhar", None)


def _gravar(usuario_id, noticia_id, tipo_acao):
    """Persiste uma interação (uma transação por ação)."""
    peso = config.PESOS[tipo_acao]
    conn = get_conexao()
    try:
        with conn.cursor() as cur:
            repositorio.registrar_interacao(cur, usuario_id, noticia_id, tipo_acao, peso)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _compartilhar(usuario_id, noticia_id, link):
    """Compartilhar: registra a interação (sinal forte, peso 5) e abre o painel de
    copiar link no próximo run.

    A cópia em si precisa de um CLIQUE do usuário (o navegador bloqueia escrita no
    clipboard fora de um gesto), por isso não copiamos automático aqui — guardamos
    a URL e mostramos um botão "Copiar link" (ver _painel_copiar_link).
    """
    _gravar(usuario_id, noticia_id, "compartilhar")
    st.session_state["compartilhar"] = (noticia_id, link)
    st.rerun()


def _painel_copiar_link(url):
    """Botão que copia `url` no clipboard ao ser clicado, com balão "URL copiada!".

    Roda dentro de um iframe (st.iframe): no clique tenta a Clipboard API e cai
    num <textarea> + execCommand('copy') de reserva — ambos funcionam porque o
    clique É um gesto do usuário. A URL fica visível como rede de segurança caso
    o navegador bloqueie tudo (basta copiar à mão).
    """
    dados = json.dumps(url)  # vira uma string JS segura (escapa aspas/barras)
    st.iframe(
        f"""<!doctype html><html><head><meta charset="utf-8"></head>
        <body style="margin:0;font-family:'Source Sans Pro',sans-serif">
          <button id="b" style="width:100%;padding:0.55rem 1rem;border:none;
            border-radius:0.5rem;background:#ff4b4b;color:#fff;font-weight:600;
            font-size:0.95rem;cursor:pointer">🔗 Copiar link da notícia</button>
          <div id="m" style="margin-top:8px;font-size:0.85rem;word-break:break-all"></div>
          <script>
          const url = {dados};
          const b = document.getElementById("b");
          const m = document.getElementById("m");
          function ok() {{
            b.textContent = "✓ URL copiada!";
            b.style.background = "#16a34a";
            m.style.color = "#16a34a";
            m.textContent = url;
          }}
          function falha() {{
            m.style.color = "#b91c1c";
            m.textContent = "Não consegui copiar automaticamente — copie à mão: " + url;
          }}
          async function copiar() {{
            try {{ await navigator.clipboard.writeText(url); ok(); return; }} catch (e) {{}}
            const ta = document.createElement("textarea");
            ta.value = url; ta.style.position = "fixed"; ta.style.opacity = "0";
            document.body.appendChild(ta); ta.focus(); ta.select();
            let copiou = false;
            try {{ copiou = document.execCommand("copy"); }} catch (e) {{}}
            document.body.removeChild(ta);
            copiou ? ok() : falha();
          }}
          b.addEventListener("click", copiar);
          </script>
        </body></html>""",
        height=90,
    )


_TOAST_REACAO = {
    "like": ("👍", "Você curtiu esta notícia!"),
    "dislike": ("🚫", "Anotado — vamos evitar parecidas."),
}


def _registrar(usuario_id, noticia_id, tipo_acao):
    """Grava a interação. No feed, recarrega; na leitura, segue na mesma página."""
    _gravar(usuario_id, noticia_id, tipo_acao)
    emoji, msg = _TOAST_REACAO.get(tipo_acao, ("✅", f"Interação '{tipo_acao}' registrada."))
    st.toast(msg, icon=emoji)
    st.rerun()
