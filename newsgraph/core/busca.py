"""DFS sobre a árvore geradora.

A partir de um conjunto de sementes (notícias lidas), percorre a árvore em
profundidade e calcula, para cada notícia alcançada, o score = gargalo (menor
peso de aresta) do caminho até a semente mais próxima.
"""

def calcular_scores_gargalo(grafo_adj: dict, sementes: set) -> dict:
    """
    Percorre a árvore a partir das sementes e calcula o gargalo para cada nó.
    
    grafo_adj: dict no formato {'A': [('B', 10), ('C', 6)], 'B': [('A', 10)]}
    sementes: set com os IDs das notícias já lidas pelo usuário.
    retorna: dict com {noticia: score_gargalo}
    """
    scores = {}
    visitados = set()
    pilha = []
    
    # Inicializa a DFS a partir de todas as sementes (notícias lidas)
    for semente in sementes:
        if semente in grafo_adj:
            # Estrutura da pilha: (nó_atual, gargalo_acumulado)
            # Começa com infinito porque nenhuma aresta foi atravessada ainda
            pilha.append((semente, float('inf')))
            visitados.add(semente)
            scores[semente] = float('inf')  # Sementes têm score máximo/infinito
            
    while pilha:
        atual, gargalo_atual = pilha.pop()
        
        # Explora os vizinhos na árvore geradora
        for vizinho, peso in grafo_adj.get(atual, []):
            if vizinho not in visitados:
                visitados.add(vizinho)
                
                # O gargalo do caminho é a aresta de menor peso encontrada até aqui
                gargalo_vizinho = min(gargalo_atual, peso)
                scores[vizinho] = gargalo_vizinho
                
                pilha.append((vizinho, gargalo_vizinho))
                
    return scores