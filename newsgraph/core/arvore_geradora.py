"""Kruskal — árvore geradora máxima (uma única árvore).

Ordena as arestas por peso decrescente e adiciona a próxima se ela não fechar
ciclo (union-find), até obter uma árvore com N−1 arestas. Não remove arestas da
árvore — o esqueleto conexo permanece intacto (sem poda / sem detecção de
comunidades).
"""
