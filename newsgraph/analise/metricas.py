"""Análise e interpretação dos resultados (Critério 5).

Calcula, sobre o grafo já montado em memória, métricas que evidenciam o
funcionamento do recomendador:

- **Cobertura**: quantas notícias em escopo a projeção/árvore consegue ligar
  (vs. ilhadas sem nenhum leitor em comum).
- **Distribuição de Jaccard**: força das similaridades na projeção (min/média/máx).
- **Estrutura da árvore**: nº de componentes e tamanho da maior árvore.
- **Efeito do gargalo / antes-e-depois**: como o feed de um usuário muda após a
  primeira leitura (mostra que a recomendação responde às interações).

Camadas:
  - funções `*_de_dados(...)` → puras, operam em memória (testáveis sem banco).
  - `relatorio(cur)`          → carrega do repositório e imprime tudo.
"""

from core.grafo_bipartido import GrafoBipartido
from core.projecao import projetar
from core.arvore_geradora import kruskal_max_floresta
from recomendacao.motor import recomendar_de_dados


def _componentes(arestas, vertices):
    """Conta componentes conexas de uma lista de arestas via união ingênua."""
    pai = {v: v for v in vertices}

    def find(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    for u, v, _ in arestas:
        ru, rv = find(u), find(v)
        if ru != rv:
            pai[ru] = rv

    grupos = {}
    for v in vertices:
        grupos.setdefault(find(v), 0)
        grupos[find(v)] += 1
    return list(grupos.values())


def metricas_projecao(dados, limiar_jaccard=0.0):
    """Métricas estruturais da projeção e da árvore geradora máxima."""
    bip = GrafoBipartido.construir(
        dados["usuarios"], dados["noticias"], dados["interacoes"]
    )
    projecao = projetar(bip, limiar_jaccard=limiar_jaccard)

    vertices = set(projecao.vertices())
    arestas = projecao.arestas()
    pesos = [p for _, _, p in arestas]

    floresta = kruskal_max_floresta(arestas, vertices)
    tamanhos_comp = _componentes(floresta, vertices)

    total_noticias = len(vertices)
    com_arestas = sum(1 for v in vertices if projecao.grau(v) > 0)

    return {
        "noticias_totais": total_noticias,
        "noticias_conectadas": com_arestas,
        "cobertura_pct": round(100 * com_arestas / total_noticias, 1) if total_noticias else 0.0,
        "arestas_projecao": len(arestas),
        "jaccard_min": round(min(pesos), 4) if pesos else 0.0,
        "jaccard_medio": round(sum(pesos) / len(pesos), 4) if pesos else 0.0,
        "jaccard_max": round(max(pesos), 4) if pesos else 0.0,
        "componentes": len(tamanhos_comp),
        "maior_arvore": max(tamanhos_comp) if tamanhos_comp else 0,
        "arestas_arvore": len(floresta),
    }


def antes_e_depois(dados, usuario_id, noticia_simulada, tipo="like", top_n=5):
    """Compara o feed do usuário antes e depois de simular uma leitura.

    Adiciona uma interação fictícia (sem tocar o banco) e mostra como o Top-N
    muda — evidência direta de que a recomendação responde ao comportamento.
    """
    from config import PESOS

    antes = recomendar_de_dados(dados, usuario_id, top_n=top_n)

    dados_dep = {
        "usuarios": dados["usuarios"],
        "noticias": dados["noticias"],
        "interacoes": dados["interacoes"]
        + [{"usuario_id": usuario_id, "noticia_id": noticia_simulada, "peso": PESOS[tipo]}],
    }
    depois = recomendar_de_dados(dados_dep, usuario_id, top_n=top_n)

    return {
        "antes": [r["noticia_id"] for r in antes],
        "depois": [r["noticia_id"] for r in depois],
    }


def relatorio(cur, usuario_id=None):
    """Imprime o relatório completo de análise lendo os dados do banco."""
    from persistencia import repositorio

    dados = repositorio.carregar_grafo_dados(cur)

    print("=" * 60)
    print("RELATÓRIO DE ANÁLISE — NewsGraph")
    print("=" * 60)
    print(f"Usuários: {len(dados['usuarios'])} | Notícias em escopo: {len(dados['noticias'])} "
          f"| Interações: {len(dados['interacoes'])}")

    m = metricas_projecao(dados)
    print("\n-- Projeção texto↔texto (Jaccard ponderado) --")
    print(f"  Cobertura: {m['noticias_conectadas']}/{m['noticias_totais']} "
          f"notícias conectadas ({m['cobertura_pct']}%)")
    print(f"  Arestas na projeção: {m['arestas_projecao']}")
    print(f"  Jaccard  min/médio/máx: {m['jaccard_min']} / {m['jaccard_medio']} / {m['jaccard_max']}")
    print("\n-- Árvore (floresta) geradora máxima — Kruskal --")
    print(f"  Componentes: {m['componentes']} | Maior árvore: {m['maior_arvore']} notícias "
          f"| Arestas na árvore: {m['arestas_arvore']}")

    if usuario_id is not None:
        recs = recomendar_de_dados(dados, usuario_id, top_n=5)
        print(f"\n-- Top-5 para o usuário {usuario_id} --")
        for r in recs:
            print(f"  notícia {r['noticia_id']}: score(gargalo)={r['score']:.3f}, saltos={r['saltos']}")

    print("=" * 60)


if __name__ == "__main__":
    import os
    if not os.environ.get("DATABASE_URL"):
        print("SKIP: DATABASE_URL não definida. Defina o .env para rodar a análise sobre o banco.")
    else:
        from persistencia.conexao import get_conexao
        conn = get_conexao()
        try:
            with conn.cursor() as cur:
                relatorio(cur)
        finally:
            conn.close()
