"""Parâmetros do NewsGraph num único lugar (Seção 10 da arquitetura v2.0).

A comparação entre valores diferentes vira material do Critério 5.
"""

# Dados fictícios / dataset
USUARIOS_FICTICIOS = 40        # coocorrência rica sem peso computacional
NOTICIAS_NO_DATASET = 300      # roda em segundos, árvore visível

# Pesos das interações (entram no Jaccard ponderado; dislike exclui)
PESO_CLIQUE = 1                # sinal fraco positivo
PESO_LIKE = 4                  # sinal forte positivo
PESO_COMPARTILHAR = 5          # sinal mais forte
# dislike: remove a notícia das sementes/leitores

# Recomendação
TOP_N = 10                     # tamanho do feed recomendado
CRITERIO_SCORE = "gargalo"     # min do caminho até a semente
DESEMPATE = "menor_num_saltos" # mais perto = mais relevante
