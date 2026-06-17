"""Grafo bipartido usuário–texto.

Especialização que separa os dois conjuntos (usuários, textos) e constrói as
arestas a partir das interações. O peso da ação (clique/like/compartilhar) é o
peso da aresta; dislike exclui a notícia. Jaccard nunca é aplicado aqui.
"""
