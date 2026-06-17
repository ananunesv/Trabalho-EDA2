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
    Calcula a floresta geradora máxima.
    arestas: lista de tuplas (u, v, peso)
    retorna: lista de tuplas (u, v, peso) que compõem a floresta
    """
    # Ordenar arestas por peso decrescente para árvore máxima
    arestas_ordenadas = sorted(arestas, key=lambda x: x[2], reverse=True)
    
    uf = UnionFind(vertices)
    floresta = []
    
    for u, v, peso in arestas_ordenadas:
        # Se os vértices estão em componentes diferentes, adiciona a aresta
        if uf.union(u, v):
            floresta.append((u, v, peso))
            
    return floresta
