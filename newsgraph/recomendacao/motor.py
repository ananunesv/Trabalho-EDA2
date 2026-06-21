"""Motor de recomendação — ponto de convergência do núcleo de grafos.

Orquestra, para um `usuario_id`, todo o fluxo da Temática B:

1. monta o **grafo bipartido** usuário↔notícia a partir das interações
   (peso da ação = peso da aresta; dislike exclui);
2. projeta para **texto↔texto** por **Jaccard ponderado** sobre os leitores;
3. extrai a **árvore (floresta) geradora máxima** com Kruskal;
4. roda **DFS** a partir das notícias lidas positivamente (sementes) e calcula o
   score de cada não-lida = **gargalo** (menor peso do caminho até a semente);
5. ordena com **Heap Max** e devolve o **Top-N**, excluindo as lidas.

Desempate: menos saltos até uma semente ranqueia mais alto.

Há duas camadas:
  - `recomendar_de_dados(...)`  → pura, opera sobre dados em memória (testável
    sem banco; é onde o núcleo de grafos realmente roda).
  - `recomendar(cur, ...)`      → carrega do repositório, chama a função pura e
    enriquece o resultado com os metadados da notícia para o app.

O núcleo (`core/`) não é tocado por SQL: ele só recebe estruturas em memória.
"""

from core.grafo import Grafo
from core.grafo_bipartido import GrafoBipartido
from core.projecao import projetar
from core.arvore_geradora import kruskal_max_floresta
from core.busca import recomendar_por_dfs
from core.heap_max import MaxHeap

try:
    from config import TOP_N
except ImportError:  # fallback se rodar fora do diretório do projeto
    TOP_N = 10


def _floresta_para_grafo(floresta) -> Grafo:
    """Converte a lista de arestas `(u, v, peso)` da árvore num `Grafo` navegável.

    A DFS precisa de um objeto com `.vertices()` e `.vizinhos()`; o Kruskal
    devolve apenas a lista de arestas. Esta é a "cola" entre os dois módulos.
    """
    arvore = Grafo(direcionado=False)
    for u, v, peso in floresta:
        arvore.adicionar_aresta(u, v, peso)
    return arvore


def recomendar_de_dados(dados, usuario_id, top_n=TOP_N, limiar_jaccard=0.0):
    """Executa todo o pipeline de grafos sobre dados em memória.

    Args:
        dados:  dict com chaves 'usuarios', 'noticias', 'interacoes'
                (formato de `repositorio.carregar_grafo_dados`).
        usuario_id:     id do usuário-alvo.
        top_n:          tamanho do feed recomendado.
        limiar_jaccard: arestas da projeção com Jaccard <= limiar são filtradas.

    Returns:
        Lista de dicts ordenada por relevância (maior primeiro):
            {'noticia_id', 'score', 'saltos'}
        Vazia se o usuário não tem sementes que alcancem notícias novas.
    """
    bipartido = GrafoBipartido.construir(
        dados["usuarios"], dados["noticias"], dados["interacoes"]
    )

    # Sementes = notícias lidas positivamente que NÃO foram dislikadas.
    # (Abrir para ler grava um 'clique'; um dislike posterior tira a notícia das
    # sementes — não faz sentido recomendar a partir de algo rejeitado.)
    leituras = set(bipartido.leituras_de(usuario_id).keys())
    dislikes = bipartido.dislikes_de(usuario_id)
    sementes = leituras - dislikes
    lidas = leituras | dislikes  # nada que o usuário já viu volta no feed

    if not sementes:
        return []  # cold start: quem chama decide o fallback

    # Bipartido → projeção texto↔texto (Jaccard ponderado, com filtragem).
    projecao = projetar(bipartido, limiar_jaccard=limiar_jaccard)

    # Projeção → árvore (floresta) geradora máxima via Kruskal.
    floresta = kruskal_max_floresta(projecao.arestas(), set(projecao.vertices()))
    arvore = _floresta_para_grafo(floresta)

    # DFS a partir das sementes → score = gargalo do caminho; desempate por saltos.
    recomendacoes = recomendar_por_dfs(arvore, sementes, lidas)
    if not recomendacoes:
        return []

    # Heap Max ordena pelo par (score, -saltos): score domina, menos saltos
    # desempata. Tuplas são comparáveis, então o heap funciona sem mudanças.
    heap = MaxHeap()
    for rec in recomendacoes:
        prioridade = (rec["score"], -rec["saltos"])
        heap.inserir(rec["noticia"], prioridade)

    saltos_por_noticia = {r["noticia"]: r["saltos"] for r in recomendacoes}

    resultado = []
    for elemento in heap.top_n(top_n):
        nid = elemento["item"]
        score, _ = elemento["peso"]
        resultado.append(
            {"noticia_id": nid, "score": score, "saltos": saltos_por_noticia[nid]}
        )
    return resultado


def recomendar(cur, usuario_id, top_n=TOP_N, limiar_jaccard=0.0):
    """Recomenda Top-N notícias para `usuario_id`, com metadados, lendo do banco.

    Carrega os dados via repositório, roda o pipeline de grafos e enriquece cada
    recomendação com título/resumo/link/fonte para o app renderizar.

    Cold start: se o usuário ainda não tem interações positivas, devolve as
    notícias em escopo mais recentes (popularidade temporal) — sem recomendação
    personalizada, mas com feed útil para a primeira leitura fechar o ciclo.

    Returns:
        Lista de dicts: {'noticia_id', 'titulo', 'resumo', 'link', 'fonte',
                         'score', 'saltos', 'personalizada'}.
    """
    from persistencia import repositorio

    dados = repositorio.carregar_grafo_dados(cur)
    por_id = {n["id"]: n for n in dados["noticias"]}

    recs = recomendar_de_dados(dados, usuario_id, top_n, limiar_jaccard)

    if recs:
        saida = []
        for r in recs:
            n = por_id.get(r["noticia_id"])
            if not n:
                continue
            saida.append(_montar_item(n, r["score"], r["saltos"], personalizada=True))
        return saida

    # --- Fallback (cold start): mais recentes em escopo, excluindo já lidas. ---
    bipartido = GrafoBipartido.construir(
        dados["usuarios"], dados["noticias"], dados["interacoes"]
    )
    lidas = set(bipartido.leituras_de(usuario_id).keys()) | bipartido.dislikes_de(usuario_id)

    noticias_feed = repositorio.buscar_noticias(cur)  # já vem por recência
    saida = []
    for n in noticias_feed:
        if n["id"] in lidas:
            continue
        saida.append(_montar_item(n, score=None, saltos=None, personalizada=False))
        if len(saida) == top_n:
            break
    return saida


def _montar_item(noticia, score, saltos, personalizada):
    """Normaliza um dict de notícia + métricas no formato que o app consome."""
    return {
        "noticia_id": noticia["id"],
        "titulo": noticia.get("titulo", ""),
        "resumo": noticia.get("resumo", ""),
        "link": noticia.get("link", ""),
        "fonte": noticia.get("fonte", ""),
        "score": score,
        "saltos": saltos,
        "personalizada": personalizada,
    }
