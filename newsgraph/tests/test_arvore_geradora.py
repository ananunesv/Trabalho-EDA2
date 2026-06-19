from core.arvore_geradora import kruskal_max

def test_kruskal_arvore_unica():
    # 6 Vértices (A até F) -> Precisamos de exatamente 5 arestas (N - 1)
    vertices = {'A', 'B', 'C', 'D', 'E', 'F'}
    
    # Grafo sintético totalmente conexo
    arestas = [
        ('A', 'B', 10),
        ('B', 'C', 20),
        ('C', 'D', 30),
        ('D', 'E', 40),
        ('E', 'F', 50),
        # Arestas extras que criam ciclos (serão ignoradas pelo Kruskal)
        ('A', 'C', 5),
        ('B', 'D', 2)
    ]
    
    # Executa o seu algoritmo
    arvore = kruskal_max(arestas, vertices)
    peso_total = sum(peso for _, _, peso in arvore)
    
    print(f"\nArestas selecionadas: {arvore}")
    print(f"Total de arestas: {len(arvore)}")
    print(f"Peso total: {peso_total}")
    
    # Validações dos critérios de aceite da Issue
    assert len(arvore) == 5, "Deveria ter encontrado exatamente 5 arestas!"
    assert peso_total == 150, "O peso total máximo deveria ser 150 (50+40+30+20+10)!"
    print("\n[SUCESSO] O teste passou! Árvore máxima única gerada com 5 arestas.")

if __name__ == "__main__":
    test_kruskal_arvore_unica()