"""Motor de recomendação.

Orquestra o núcleo de grafos para um usuario_id:
1. identifica as sementes (lidas positivamente; dislike exclui);
2. monta bipartido → projeção (Jaccard) → Kruskal (árvore geradora máxima);
3. roda o DFS a partir das sementes e calcula o score = gargalo do caminho;
4. empilha no Heap Max e extrai o Top-N;
5. exclui as lidas da saída.

Desempate: menor nº de saltos até uma semente.
"""
