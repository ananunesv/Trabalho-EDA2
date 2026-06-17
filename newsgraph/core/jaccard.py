"""Coeficiente de Jaccard ponderado.

Função pura: recebe os leitores de duas notícias com seus pesos de interação e
devolve J(A,B) = Σ_u min(w_A(u), w_B(u)) / Σ_u max(w_A(u), w_B(u)). Usada para
pesar as arestas da projeção (nunca no bipartido). Com pesos iguais, reduz-se
ao Jaccard clássico.
"""
