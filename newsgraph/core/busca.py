

def recomendar_por_dfs(arvore, sementes, lidas):
    """
    Percorre a árvore geradora conexa (Kruskal) a partir das sementes usando DFS.
    
    Regras de Negócio:
    1. Parte apenas de sementes (interações positivas).
    2. Calcula o score (gargalo = menor peso do caminho).
    3. Registra a distância em saltos para desempate (menos saltos = maior prioridade).
    4. Ignora textos já lidos (positivos ou negativos) no resultado final.
    """
    # Dicionário para armazenar o melhor estado de cada notícia não-lida.
    # Formato: { 'Noticia_X': {'score_gargalo': float, 'saltos': int} }
    resultados = {}

    for semente in sementes:
        # Verifica se a semente existe na árvore antes de buscar (segurança)
        if semente not in arvore.vertices():
            continue

        # Pilha para a DFS: armazena (nó_atual, saltos_acumulados, gargalo_atual, nó_pai)
        # Inicializamos o gargalo como 'inf' pois o primeiro passo definirá o teto.
        pilha = [(semente, 0, float('inf'), None)]

        while pilha:
            atual, saltos, gargalo, pai = pilha.pop()

            # Processa o nó atual se ele não for uma notícia que o usuário já leu
            if atual not in lidas:
                if atual not in resultados:
                    # Primeira vez que alcançamos esta notícia
                    resultados[atual] = {'score_gargalo': gargalo, 'saltos': saltos}
                else:
                    estado_atual = resultados[atual]
                    
                    # Regra do Caminho: Prioriza a semente mais próxima (menos saltos)
                    if saltos < estado_atual['saltos']:
                        resultados[atual] = {'score_gargalo': gargalo, 'saltos': saltos}
                    
                    # Desempate: Se a distância for igual, prefere o caminho com o maior gargalo
                    elif saltos == estado_atual['saltos']:
                        if gargalo > estado_atual['score_gargalo']:
                            resultados[atual]['score_gargalo'] = gargalo

            # Expansão DFS: Adiciona os vizinhos na pilha
            for vizinho, peso in arvore.vizinhos(atual):
                # Evita voltar de onde viemos (como é árvore, isso impede loops)
                if vizinho != pai:
                    # O gargalo do caminho é o menor peso encontrado até agora
                    novo_gargalo = min(gargalo, float(peso))
                    pilha.append((vizinho, saltos + 1, novo_gargalo, atual))

    # Formata a saída em uma lista de dicionários pronta para ser enviada à MaxHeap
    lista_recomendacoes = []
    for noticia, dados in resultados.items():
        lista_recomendacoes.append({
            'noticia': noticia,
            'score': dados['score_gargalo'],
            'saltos': dados['saltos']
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