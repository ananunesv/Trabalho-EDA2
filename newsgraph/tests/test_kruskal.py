from core.arvore_geradora import kruskal_max
def test_kruskal_desconexo():
    vertices = {'A', 'B', 'C', 'D', 'E'}
    # Dois componentes: {A, B, C} e {D, E}
    arestas = [
        ('A', 'B', 10), ('B', 'C', 5), ('A', 'C', 2),
        ('D', 'E', 8)
    ]
    
    floresta = kruskal_max(arestas, vertices)
    
    # Esperado: 
    # Componente 1: (A,B,10) e (B,C,5). (A,C,2) ignorado por ciclo.
    # Componente 2: (D,E,8).
    # Total: 3 arestas.
    
    print(f"Arestas selecionadas: {len(floresta)}")
    assert len(floresta) == 3
    assert ('A', 'C', 2) not in floresta
    print("Teste passou: A floresta foi gerada corretamente para grafo desconexo.")

# Executar teste
if __name__ == "__main__":
    test_kruskal_desconexo()