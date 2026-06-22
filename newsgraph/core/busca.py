

def recomendar_por_dfs(arvore, sementes, lidas, pesos_semente=None):
    """
    Percorre a árvore geradora conexa (Kruskal) a partir das sementes usando DFS.

    Regras de Negócio:
    1. Parte apenas de sementes (interações positivas).
    2. Calcula o gargalo (menor peso do caminho) de cada notícia não-lida.
    3. Pondera o gargalo pela RECÊNCIA da semente de origem: score_ranking =
       gargalo * peso_semente. Assim o topo do feed acompanha o que o usuário leu
       por último, em vez de ficar preso na maior afinidade de todo o histórico.
    4. Quando uma notícia é alcançável por mais de uma semente, fica com o caminho
       de MAIOR score_ranking; saltos só desempata (caminhos de score igual).
    5. Ignora textos já lidos (positivos ou negativos) no resultado final.

    Args:
        pesos_semente: dict {semente: peso_recencia em (0, 1]}. Ausente/None →
            todas as sementes valem 1.0 (score_ranking == gargalo; comportamento
            idêntico ao de antes da recência — é o caso dos testes sintéticos).
    """
    lidas = set(lidas)

    # Dicionário para armazenar o melhor estado de cada notícia não-lida.
    # Formato: { 'Noticia_X': {'gargalo', 'saltos', 'recencia', 'score_ranking'} }
    resultados = {}

    for semente in sementes:
        # Verifica se a semente existe na árvore antes de buscar (segurança)
        if semente not in arvore.vertices():
            continue

        # Peso de recência desta semente (1.0 quando não há ponderação).
        w = 1.0 if pesos_semente is None else pesos_semente.get(semente, 1.0)

        # Pilha para a DFS: armazena (nó_atual, saltos_acumulados, gargalo_atual, nó_pai)
        # Inicializamos o gargalo como 'inf' pois o primeiro passo definirá o teto.
        pilha = [(semente, 0, float('inf'), None)]

        while pilha:
            atual, saltos, gargalo, pai = pilha.pop()

            # Processa o nó atual se ele não for uma notícia que o usuário já leu
            if atual not in lidas:
                score_ranking = gargalo * w
                anterior = resultados.get(atual)
                # Fica com o caminho de maior score_ranking; em empate, menos saltos.
                if (
                    anterior is None
                    or score_ranking > anterior['score_ranking']
                    or (score_ranking == anterior['score_ranking']
                        and saltos < anterior['saltos'])
                ):
                    resultados[atual] = {
                        'gargalo': gargalo,
                        'saltos': saltos,
                        'recencia': w,
                        'score_ranking': score_ranking,
                    }

            # Expansão DFS: Adiciona os vizinhos na pilha
            for vizinho, peso in arvore.vizinhos(atual):
                # Evita voltar de onde viemos (como é árvore, isso impede loops)
                if vizinho != pai:
                    # O gargalo do caminho é o menor peso encontrado até agora
                    novo_gargalo = min(gargalo, float(peso))
                    pilha.append((vizinho, saltos + 1, novo_gargalo, atual))

    # Formata a saída em uma lista de dicionários pronta para ser enviada à MaxHeap.
    # 'score' continua sendo o gargalo puro (afinidade) para exibição; o motor
    # ordena por 'score_ranking' (gargalo ponderado pela recência).
    lista_recomendacoes = []
    for noticia, dados in resultados.items():
        lista_recomendacoes.append({
            'noticia': noticia,
            'score': dados['gargalo'],
            'saltos': dados['saltos'],
            'recencia': dados['recencia'],
            'score_ranking': dados['score_ranking'],
        })

    return lista_recomendacoes


# ==============================================================================
# TESTES UNITÁRIOS SINTÉTICOS (Requisito da Issue #8)
# ==============================================================================
if __name__ == "__main__":
    print("Iniciando testes da DFS (Travessia + Gargalo)...")

    # Mock super simples da interface Grafo para rodar o teste isolado
    class GrafoMock:
        def __init__(self): self.adj = {}
        def adicionar_aresta(self, u, v, peso):
            if u not in self.adj: self.adj[u] = {}
            if v not in self.adj: self.adj[v] = {}
            self.adj[u][v] = peso
            self.adj[v][u] = peso
        def vertices(self): return list(self.adj.keys())
        def vizinhos(self, v): return list(self.adj.get(v, {}).items())

    # Criando uma árvore sintética com valores conhecidos
    # (Semente 1) N1 ---0.8--- N2 ---0.5--- N3 ---0.9--- N4 (Semente 2)
    #                          |
    #                         0.4
    #                          |
    #                          N5
    
    arvore = GrafoMock()
    arvore.adicionar_aresta('N1', 'N2', 0.8)
    arvore.adicionar_aresta('N2', 'N3', 0.5)
    arvore.adicionar_aresta('N3', 'N4', 0.9)
    arvore.adicionar_aresta('N2', 'N5', 0.4)

    sementes = ['N1', 'N4']
    lidas = ['N1', 'N4', 'N_DISLIKE_QUALQUER']

    resultados = recomendar_por_dfs(arvore, sementes, lidas)
    res_dict = {item['noticia']: item for item in resultados}

    # Asserts baseados nos cálculos manuais solicitados pela gerência
    assert res_dict['N2']['score'] == 0.8 and res_dict['N2']['saltos'] == 1, "Erro em N2"
    assert res_dict['N3']['score'] == 0.9 and res_dict['N3']['saltos'] == 1, "Erro em N3"
    assert res_dict['N5']['score'] == 0.4 and res_dict['N5']['saltos'] == 2, "Erro em N5"
    assert 'N1' not in res_dict and 'N4' not in res_dict, "Erro: Lidas não foram filtradas!"

    print("✔ Todos os cálculos bateram perfeitamente com a prova real (manual).")
    print("✔ O código usou apenas navegação conexa, sem vestígios de detecção de comunidade.")
    print("✔ DFS Sintética aprovada!")