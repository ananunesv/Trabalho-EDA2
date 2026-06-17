"""Camada de repositório — única porta para o banco.

Expõe funções de alto nível (salvar_noticia, buscar_noticias,
registrar_interacao, carregar_grafo_dados) e é o único módulo que escreve SQL.
O resto do sistema nunca vê uma query.
"""
