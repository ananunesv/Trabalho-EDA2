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
    from config import TOP_N, FATOR_RECENCIA
except ImportError:  # fallback se rodar fora do diretório do projeto
    TOP_N = 10
    FATOR_RECENCIA = 0.8


def _floresta_para_grafo(floresta) -> Grafo:
    """Converte a lista de arestas `(u, v, peso)` da árvore num `Grafo` navegável.

    A DFS precisa de um objeto com `.vertices()` e `.vizinhos()`; o Kruskal
    devolve apenas a lista de arestas. Esta é a "cola" entre os dois módulos.
    """
    arvore = Grafo(direcionado=False)
    for u, v, peso in floresta:
        arvore.adicionar_aresta(u, v, peso)
    return arvore


def _pesos_por_recencia(dados, usuario_id, sementes, fator=FATOR_RECENCIA):
    """Peso de recência por semente: a interação mais recente vale 1.0 e as
    anteriores decaem geometricamente (``fator ** posição``). Usa o timestamp
    mais recente de cada semente para ordená-las.

    Devolve None (recência desligada — todas valem 1.0) quando ``fator >= 1.0``
    ou quando não há timestamps utilizáveis (ex.: dados de teste sintéticos).
    Nesse caso a DFS calcula score_ranking == gargalo, como antes da recência.
    """
    if fator >= 1.0:
        return None

    ult_ts = {}
    for it in dados["interacoes"]:
        if it.get("usuario_id") != usuario_id or it.get("peso", 0) <= 0:
            continue
        nid = it.get("noticia_id")
        ts = it.get("timestamp")
        if nid not in sementes or ts is None:
            continue
        if nid not in ult_ts or ts > ult_ts[nid]:
            ult_ts[nid] = ts

    if not ult_ts:
        return None

    # Sementes da mais recente para a mais antiga; sem timestamp vão para o fim.
    com_ts = sorted(ult_ts, key=lambda nid: ult_ts[nid], reverse=True)
    sem_ts = [s for s in sementes if s not in ult_ts]
    ordenadas = com_ts + sem_ts
    return {nid: fator ** pos for pos, nid in enumerate(ordenadas)}


def recomendar_de_dados(dados, usuario_id, top_n=TOP_N, limiar_jaccard=0.0, ocultas=None):
    """Executa todo o pipeline de grafos sobre dados em memória.

    Args:
        dados:  dict com chaves 'usuarios', 'noticias', 'interacoes'
                (formato de `repositorio.carregar_grafo_dados`).
        usuario_id:     id do usuário-alvo.
        top_n:          tamanho do feed recomendado.
        limiar_jaccard: arestas da projeção com Jaccard <= limiar são filtradas.
        ocultas:        ids que o usuário pediu para "pular" (botão Procurar mais).
                        Entram em `lidas` — somem do resultado mas continuam
                        servindo de ponte na árvore — SEM virar sementes nem
                        dislike. Conectividade da pipeline preservada.

    Returns:
        Lista de dicts ordenada por relevância (maior primeiro):
            {'noticia_id', 'score', 'saltos', 'recencia'}
        Vazia se o usuário não tem sementes que alcancem notícias novas.
    """
    ocultas = set(ocultas or ())
    bipartido = GrafoBipartido.construir(
        dados["usuarios"], dados["noticias"], dados["interacoes"]
    )

    # Sementes = notícias lidas positivamente que NÃO foram dislikadas.
    # (Abrir para ler grava um 'clique'; um dislike posterior tira a notícia das
    # sementes — não faz sentido recomendar a partir de algo rejeitado.)
    leituras = set(bipartido.leituras_de(usuario_id).keys())
    dislikes = bipartido.dislikes_de(usuario_id)
    sementes = leituras - dislikes
    # `ocultas` excluem do resultado (como as lidas) mas NÃO viram sementes.
    lidas = leituras | dislikes | ocultas  # nada que o usuário já viu/pulou volta

    if not sementes:
        return []  # cold start: quem chama decide o fallback

    # Bipartido → projeção texto↔texto (Jaccard ponderado, com filtragem).
    projecao = projetar(bipartido, limiar_jaccard=limiar_jaccard)

    # Projeção → árvore (floresta) geradora máxima via Kruskal.
    floresta = kruskal_max_floresta(projecao.arestas(), set(projecao.vertices()))
    arvore = _floresta_para_grafo(floresta)

    # Recência das sementes: a leitura mais recente pesa mais (ver _pesos_por_recencia).
    pesos_semente = _pesos_por_recencia(dados, usuario_id, sementes)

    # DFS a partir das sementes → gargalo do caminho, ponderado pela recência.
    recomendacoes = recomendar_por_dfs(arvore, sementes, lidas, pesos_semente)
    if not recomendacoes:
        return []

    # Heap Max ordena pelo par (score_ranking, -saltos): o gargalo ponderado pela
    # recência domina, menos saltos desempata. Tuplas são comparáveis, então o
    # heap funciona sem mudanças.
    heap = MaxHeap()
    for rec in recomendacoes:
        prioridade = (rec["score_ranking"], -rec["saltos"])
        heap.inserir(rec["noticia"], prioridade)

    por_noticia = {r["noticia"]: r for r in recomendacoes}

    resultado = []
    for elemento in heap.top_n(top_n):
        nid = elemento["item"]
        r = por_noticia[nid]
        # 'score' = gargalo puro (afinidade) para exibição; a ordem vem do
        # score_ranking (gargalo x recência).
        resultado.append(
            {"noticia_id": nid, "score": r["score"], "saltos": r["saltos"],
             "recencia": r["recencia"]}
        )
    return resultado


def recomendar(cur, usuario_id, top_n=TOP_N, limiar_jaccard=0.0, ocultas=None):
    """Recomenda Top-N notícias para `usuario_id`, com metadados, lendo do banco.

    Carrega os dados via repositório, roda o pipeline de grafos e enriquece cada
    recomendação com título/resumo/link/fonte para o app renderizar.

    Cold start: se o usuário ainda não tem interações positivas, devolve as
    notícias em escopo mais recentes (popularidade temporal) — sem recomendação
    personalizada, mas com feed útil para a primeira leitura fechar o ciclo.

    `ocultas`: ids que o usuário pulou (botão "Procurar mais notícias"). Somem do
    feed sem virar lidas/dislike; valem também para o fallback de cold start.

    Returns:
        Lista de dicts: {'noticia_id', 'titulo', 'resumo', 'link', 'fonte',
                         'score', 'saltos', 'recencia', 'personalizada'}.
    """
    from persistencia import repositorio

    ocultas = set(ocultas or ())
    dados = repositorio.carregar_grafo_dados(cur)
    por_id = {n["id"]: n for n in dados["noticias"]}

    recs = recomendar_de_dados(dados, usuario_id, top_n, limiar_jaccard, ocultas)

    if recs:
        saida = []
        for r in recs:
            n = por_id.get(r["noticia_id"])
            if not n:
                continue
            saida.append(_montar_item(n, r["score"], r["saltos"], personalizada=True,
                                      recencia=r.get("recencia")))
        return saida

    # --- Fallback (cold start): mais recentes em escopo, excluindo já lidas. ---
    bipartido = GrafoBipartido.construir(
        dados["usuarios"], dados["noticias"], dados["interacoes"]
    )
    lidas = set(bipartido.leituras_de(usuario_id).keys()) | bipartido.dislikes_de(usuario_id) | ocultas

    noticias_feed = repositorio.buscar_noticias(cur)  # já vem por recência
    saida = []
    for n in noticias_feed:
        if n["id"] in lidas:
            continue
        saida.append(_montar_item(n, score=None, saltos=None, personalizada=False))
        if len(saida) == top_n:
            break
    return saida


def _montar_item(noticia, score, saltos, personalizada, recencia=None):
    """Normaliza um dict de notícia + métricas no formato que o app consome."""
    return {
        "noticia_id": noticia["id"],
        "titulo": noticia.get("titulo", ""),
        "resumo": noticia.get("resumo", ""),
        "link": noticia.get("link", ""),
        "fonte": noticia.get("fonte", ""),
        "score": score,
        "saltos": saltos,
        "recencia": recencia,
        "personalizada": personalizada,
    }
