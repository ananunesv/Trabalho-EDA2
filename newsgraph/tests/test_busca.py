from core.busca import enumerar_comunidades
def test_comunidades():
    # Grafo após Kruskal: {A-B, B-C} e {D-E}
    adj = {
        'A': ['B'], 'B': ['A', 'C'], 'C': ['B'],
        'D': ['E'], 'E': ['D']
    }
    vertices = {'A', 'B', 'C', 'D', 'E'}
    
    comunidades = enumerar_comunidades(adj, vertices)
    
    # Validações
    assert len(comunidades) == 2
    assert {'A', 'B', 'C'} in comunidades
    assert {'D', 'E'} in comunidades
    print("Teste de comunidades passou!")