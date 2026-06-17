"""Parâmetros do NewsGraph num único lugar (Seção 10 da arquitetura v2.0).

A comparação entre valores diferentes vira material do Critério 5.
"""

# Dados fictícios / dataset
USUARIOS_FICTICIOS = 40        # coocorrência rica sem peso computacional
NOTICIAS_NO_DATASET = 300      # roda em segundos, árvore visível

# Pesos das interações (entram no Jaccard ponderado; dislike exclui das sementes)
PESO_CLIQUE = 1                # sinal fraco positivo
PESO_LIKE = 4                  # sinal forte positivo
PESO_COMPARTILHAR = 5          # sinal mais forte
PESO_DISLIKE = -3             # armazenado (coluna NOT NULL); exclui a notícia das sementes/leitores

# Mapa tipo_acao -> peso, usado pelo gerador de dados e pelo app
PESOS = {
    "clique": PESO_CLIQUE,
    "like": PESO_LIKE,
    "compartilhar": PESO_COMPARTILHAR,
    "dislike": PESO_DISLIKE,
}

# Feeds RSS dos portais financeiros (Fase 4). >= 3 portais.
# URLs candidatas — confirme cada uma abrindo no navegador antes da coleta real.
FEEDS = {
    "InfoMoney": "https://www.infomoney.com.br/feed/",
    "Agencia Brasil - Economia": "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml",
    "Investing.com BR": "https://br.investing.com/rss/news.rss",
    "G1 Economia": "https://g1.globo.com/rss/g1/economia/",
}

# Recomendação
TOP_N = 10                     # tamanho do feed recomendado
CRITERIO_SCORE = "gargalo"     # min do caminho até a semente
DESEMPATE = "menor_num_saltos" # mais perto = mais relevante

# Geração de dados fictícios via LLM (Fase 6) — Google Gemini (free tier)
MODELO_LLM = "gemini-2.5-flash"  # rápido e gratuito; alternativa mais forte: gemini-2.5-pro
USUARIOS_POR_LOTE = 8            # usuários por chamada à LLM (mantém a resposta pequena)
