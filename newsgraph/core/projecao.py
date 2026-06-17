"""Projeção bipartido → texto–texto (conexa).

Varre o bipartido e gera o grafo texto–texto: dois textos ganham aresta se
compartilham leitores, com peso dado pelo Jaccard ponderado. Mantém a projeção
conexa — não fragmenta, entra inteira no Kruskal.
"""
