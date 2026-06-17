"""DFS sobre a árvore geradora.

A partir de um conjunto de sementes (notícias lidas), percorre a árvore em
profundidade e calcula, para cada notícia alcançada, o score = gargalo (menor
peso de aresta) do caminho até a semente mais próxima.
"""
def enumerar_comunidades(grafo_adj: dict, vertices: set) -> list:
    visitados = set()
    comunidades = []
    
    for v in vertices:
        if v not in visitados:
            comunidade = set()
            pilha = [v]
            visitados.add(v)
            while pilha:
                atual = pilha.pop()
                comunidade.add(atual)
                for vizinho in grafo_adj.get(atual, []):
                    if vizinho not in visitados:
                        visitados.add(vizinho)
                        pilha.append(vizinho)
            comunidades.append(comunidade)
    return comunidades

def mapear_vertice_comunidade(comunidades: list) -> dict:
    """Mapeia cada vértice ao ID da comunidade para busca O(1) no motor."""
    return {v: i for i, comp in enumerate(comunidades) for v in comp}