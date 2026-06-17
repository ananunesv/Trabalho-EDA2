"""Esquema das tabelas (v2.0).

Três entidades persistidas:
- usuarios(id, nome, criado_em)                                   — vértices-usuário
- noticias(id, titulo, resumo, link, fonte, data_publicacao, coletado_em) — vértices-notícia
- interacoes(id, usuario_id, noticia_id, tipo_acao, peso, timestamp)      — arestas do bipartido
"""
