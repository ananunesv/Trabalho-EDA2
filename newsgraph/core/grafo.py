"""Núcleo de grafos — classe `Grafo` genérica (lista de adjacência).

Responsabilidade: adicionar vértices/arestas com peso, consultar vizinhos e grau.
Python puro — sem dependência de banco, Streamlit, spaCy ou LLM.
"""

class Grafo:
    """
    Estrutura base de Grafo utilizando dicionário de dicionários {u: {v: peso}}.
    Ideal para grafos esparsos e algoritmos de travessia (O(1) para verificar arestas).
    """
    def __init__(self, direcionado: bool = False):
        self.direcionado = direcionado
        self.adj = {}

    def adicionar_vertice(self, v) -> None:
        """Adiciona um vértice ao grafo, inicializando seu dicionário de vizinhos."""
        if v not in self.adj:
            self.adj[v] = {}

    def adicionar_aresta(self, u, v, peso: float = 1.0) -> None:
        """
        Adiciona uma aresta de u para v com o respectivo peso. 
        Se o grafo for não-direcionado, adiciona também de v para u.
        Cria os vértices caso não existam.
        """
        self.adicionar_vertice(u)
        self.adicionar_vertice(v)
        
        self.adj[u][v] = float(peso)
        if not self.direcionado:
            self.adj[v][u] = float(peso)

    def vizinhos(self, v) -> list:
        """Retorna os vizinhos do vértice em formato de lista de tuplas: [(vizinho, peso), ...]"""
        if v in self.adj:
            return list(self.adj[v].items())
        return []

    def vertices(self) -> list:
        """Retorna uma lista com todos os vértices do grafo."""
        return list(self.adj.keys())

    def arestas(self) -> list:
        """
        Retorna todas as arestas do grafo no formato: [(u, v, peso), ...].
        Para grafos não-direcionados, garante que a aresta só apareça uma vez na lista.
        """
        lista_arestas = []
        vistos = set()
        
        for u in self.adj:
            for v, peso in self.adj[u].items():
                if not self.direcionado:
                    # Usa frozenset para garantir que (u, v) e (v, u) sejam tratados como a mesma aresta
                    aresta_id = frozenset([u, v])
                    if aresta_id not in vistos:
                        vistos.add(aresta_id)
                        lista_arestas.append((u, v, peso))
                else:
                    lista_arestas.append((u, v, peso))
                    
        return lista_arestas

    def tem_aresta(self, u, v) -> bool:
        """Retorna True se existir uma aresta saindo de u para v."""
        return u in self.adj and v in self.adj[u]

    def peso(self, u, v) -> float:
        """Retorna o peso da aresta entre u e v. Lança exceção se não existir."""
        if self.tem_aresta(u, v):
            return self.adj[u][v]
        raise ValueError(f"Aresta entre {u} e {v} não existe.")

    def grau(self, v) -> int:
        """Retorna o grau de um vértice (quantidade de vizinhos)."""
        if v in self.adj:
            return len(self.adj[v])
        return 0

    def num_vertices(self) -> int:
        """Retorna o número total de vértices."""
        return len(self.adj)

    def num_arestas(self) -> int:
        """Retorna o número total de arestas."""
        return len(self.arestas())


# ==============================================================================
# TESTES UNITÁRIOS SINTÉTICOS
# ==============================================================================
if __name__ == "__main__":
    print("Executando testes da estrutura base do Grafo...")

    # Teste 1: Grafo Direcionado Básico (Estrutura e Contagem)
    g_dir = Grafo(direcionado=True)
    g_dir.adicionar_aresta("A", "B", 2.5)
    g_dir.adicionar_aresta("A", "C", 1.0)
    assert g_dir.num_vertices() == 3
    assert g_dir.num_arestas() == 2
    assert g_dir.tem_aresta("A", "B") is True
    assert g_dir.tem_aresta("B", "A") is False
    assert g_dir.grau("A") == 2
    assert g_dir.grau("B") == 0  # Direcionado, aresta só chega em B
    print("✔ Teste 1 (Direcionado) passou.")

    # Teste 2: Grafo Não-Direcionado Básico e Pesos
    g_undir = Grafo(direcionado=False)
    g_undir.adicionar_aresta("X", "Y", 0.8)
    assert g_undir.tem_aresta("X", "Y") is True
    assert g_undir.tem_aresta("Y", "X") is True
    assert g_undir.peso("Y", "X") == 0.8
    assert g_undir.num_arestas() == 1 # Apenas uma aresta física ligando os dois
    assert g_undir.grau("Y") == 1
    print("✔ Teste 2 (Não-Direcionado) passou.")

    # Teste 3: Sobrescrita de Pesos e Retornos em Tupla
    g_undir.adicionar_aresta("X", "Y", 0.5) # Atualiza o peso
    assert g_undir.peso("X", "Y") == 0.5
    vizinhos_x = g_undir.vizinhos("X")
    assert vizinhos_x == [("Y", 0.5)]
    print("✔ Teste 3 (Sobrescrita e Formato de Retorno) passou.")

    # Teste 4: Verificação de Listagem de Arestas
    g_undir.adicionar_aresta("Y", "Z", 1.2)
    todas_arestas = g_undir.arestas()
    assert len(todas_arestas) == 2
    # Verifica a estrutura da tupla (u, v, peso)
    assert type(todas_arestas[0]) == tuple
    assert len(todas_arestas[0]) == 3
    print("✔ Teste 4 (Listagem de Arestas) passou.")

    print("\nTodos os 4 testes concluídos com sucesso!")