"""Kruskal — árvore geradora máxima (uma única árvore).

Ordena as arestas por peso decrescente e adiciona a próxima se ela não fechar
ciclo (union-find), até obter uma árvore com N−1 arestas. Não remove arestas da
árvore — o esqueleto conexo permanece intacto (sem poda / sem detecção de
comunidades).
"""

class UnionFind:
    """Implementação de Union-Find com compressão de caminho e união por rank."""
    def __init__(self, vertices: set):
        self.parent = {v: v for v in vertices}
        self.rank = {v: 0 for v in vertices}

    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])  # Compressão de caminho
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        
        if root_i != root_j:
            # União por rank
            if self.rank[root_i] < self.rank[root_j]:
                self.parent[root_i] = root_j
            elif self.rank[root_i] > self.rank[root_j]:
                self.parent[root_j] = root_i
            else:
                self.parent[root_i] = root_j
                self.rank[root_j] += 1
            return True
        return False

def kruskal_max(arestas: list, vertices: set) -> list:
    """
    Calcula a árvore geradora máxima conexa.
    Garante N-1 arestas e lança erro caso gere uma floresta.
    """
    # Ordenar arestas por peso decrescente para árvore máxima
    arestas_ordenadas = sorted(arestas, key=lambda x: x[2], reverse=True)
    
    uf = UnionFind(vertices)
    arvore = []
    num_vertices = len(vertices)
    
    for u, v, peso in arestas_ordenadas:
        # Se os vértices estão em componentes diferentes, adiciona a aresta
        if uf.union(u, v):
            arvore.append((u, v, peso))
            # Otimizacao: paramos assim que atingirmos N-1 arestas
            if len(arvore) == num_vertices - 1:
                break
    
    if len(arvore) != num_vertices - 1:
        raise ValueError(
            f"Erro: O grafo é desconexo. Gerou apenas {len(arvore)} arestas "
            f"em vez das {num_vertices - 1} necessárias para uma árvore única."
        )
    return arvore


def kruskal_max_floresta(arestas: list, vertices: set) -> list:
    """Floresta geradora máxima (uma árvore por componente conexa).

    Mesma lógica do Kruskal máximo, mas SEM exigir conexidade: percorre todas as
    arestas em ordem decrescente de peso e mantém as que ligam componentes
    distintos. Quando a projeção real é esparsa (notícias sem leitor em comum
    ficam isoladas), o grafo não é conexo e `kruskal_max` lançaria erro — aqui
    devolvemos a floresta máxima, que é exatamente a árvore geradora máxima de
    cada componente.

    Não é detecção de comunidades: não rotulamos nem interpretamos os grupos;
    apenas preservamos o esqueleto máximo de similaridade que existir. O DFS
    parte das sementes e alcança o que estiver na mesma árvore delas.
    """
    arestas_ordenadas = sorted(arestas, key=lambda x: x[2], reverse=True)

    uf = UnionFind(vertices)
    floresta = []
    max_arestas = len(vertices) - 1  # teto: vira uma única árvore se for conexo

    for u, v, peso in arestas_ordenadas:
        if uf.union(u, v):
            floresta.append((u, v, peso))
            if len(floresta) == max_arestas:
                break

    return floresta
            
