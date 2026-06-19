
from core.grafo import Grafo
from core.grafo_bipartido import GrafoBipartido
from core.jaccard import jaccard


def projetar(bipartido: GrafoBipartido, limiar_jaccard: float = 0.0) -> Grafo:
    grafo = Grafo(direcionado=False)

    # Garante que toda notícia seja vértice, mesmo sem arestas
    for nid in bipartido.noticias:
        grafo.adicionar_vertice(nid)

    noticias = list(bipartido.noticias)
    n = len(noticias)

    # Percorre todos os pares (i, j) com i < j — O(n²) pares
    # Para n=300 notícias → ~45 000 pares; cada Jaccard é O(leitores) ≈ O(40)
    # Total ≈ 1,8 M operações simples — aceitável para o volume do projeto
    for i in range(n):
        leitores_a = bipartido.leitores_de(noticias[i])
        if not leitores_a:
            continue  # notícia sem nenhum leitor positivo — pula

        for j in range(i + 1, n):
            leitores_b = bipartido.leitores_de(noticias[j])
            if not leitores_b:
                continue

            # Otimização: antes de calcular Jaccard (O(leitores)),
            # verifica se há algum leitor em comum (interseção não vazia).
            # Se não há leitor compartilhado, Jaccard = 0 → pulamos.
            if not (set(leitores_a) & set(leitores_b)):
                continue

            peso = jaccard(leitores_a, leitores_b)

            if peso > limiar_jaccard:
                grafo.adicionar_aresta(noticias[i], noticias[j], peso)

    return grafo

if __name__ == "__main__":
    from core.grafo_bipartido import GrafoBipartido

    # Dados fictícios mínimos
    usuarios   = [{"id": 1}, {"id": 2}, {"id": 3}]
    noticias   = [{"id": 10}, {"id": 20}, {"id": 30}, {"id": 40}]
    interacoes = [
        # Notícias 10 e 20 compartilham usuários 1 e 2
        {"usuario_id": 1, "noticia_id": 10, "peso": 4},
        {"usuario_id": 2, "noticia_id": 10, "peso": 1},
        {"usuario_id": 1, "noticia_id": 20, "peso": 4},
        {"usuario_id": 2, "noticia_id": 20, "peso": 1},
        # Notícia 30 compartilha só o usuário 3 com a 40
        {"usuario_id": 3, "noticia_id": 30, "peso": 5},
        {"usuario_id": 3, "noticia_id": 40, "peso": 4},
        # Notícia 30 também compartilha usuário 1 com a 10
        {"usuario_id": 1, "noticia_id": 30, "peso": 1},
        # Dislike: não deve criar aresta
        {"usuario_id": 2, "noticia_id": 40, "peso": -3},
    ]

    bp = GrafoBipartido.construir(usuarios, noticias, interacoes)
    g  = projetar(bp)

    print(f"Vértices: {sorted(g.vertices())}")
    print(f"Arestas ({g.num_arestas()}):")
    for u, v, p in sorted(g.arestas(), key=lambda x: -x[2]):
        print(f"  {u} ↔ {v}  J={p:.4f}")