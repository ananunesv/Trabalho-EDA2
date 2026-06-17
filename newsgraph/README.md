# NewsGraph

Sistema de recomendação de notícias financeiras baseado em grafos, no formato
de newsletter interativa. Disciplina **Estruturas de Dados 2 — 2026.1**,
Temática B (recomendação de textos). Arquitetura **v2.0**.

## Princípio central

Dois mundos que nunca se misturam em tempo de execução, com o banco de dados
como único ponto de contato (acessado só pela camada de repositório):

- **OFFLINE (pipeline):** coleta RSS, limpeza/PLN (spaCy) e geração de dados
  fictícios (LLM). Roda via GitHub Actions, sem usuário presente.
- **ONLINE (app):** lê do banco, monta o grafo em memória, recomenda e serve a
  interface (Streamlit).

## Fluxo de recomendação

1. Grafo bipartido usuário–texto (interações = arestas; o peso da ação é o peso
   da aresta; dislike exclui).
2. Projeção texto–texto por **Jaccard ponderado** sobre os leitores (conexa).
3. **Kruskal** → uma única árvore geradora máxima (não é podada).
4. **DFS** a partir das notícias lidas; score = **gargalo** do caminho.
5. **Heap Max** → Top-N; as lidas são excluídas da saída.

## Estrutura

```
newsgraph/
├── .github/workflows/coleta.yml   # cron 12h: pipeline offline
├── pipeline/        # OFFLINE: coletor_rss, processador_nlp, gerador_dados
├── persistencia/    # repositorio, modelos, conexao (única porta para o banco)
├── core/            # NÚCLEO DE GRAFOS (do zero) — sem banco/Streamlit/PLN/LLM
│   ├── grafo.py  grafo_bipartido.py  projecao.py  jaccard.py
│   └── arvore_geradora.py  busca.py  heap_max.py
├── recomendacao/    # motor.py — árvore + DFS das lidas + gargalo → Top-N
├── app/             # ONLINE (Streamlit): main, login, feed
├── analise/         # metricas.py — cobertura, diversidade, antes/depois
├── tests/
├── config.py        # parâmetros num único lugar
└── requirements.txt
```

A pasta `core/` é sagrada: só Python puro e estruturas próprias — nenhum import
de banco, Streamlit, spaCy ou LLM.

## Estruturas/algoritmos implementados do zero

Grafo (lista de adjacência) · Jaccard ponderado · Kruskal (AGM máxima,
union-find) · DFS (travessia + gargalo) · Heap Max (Top-N).
