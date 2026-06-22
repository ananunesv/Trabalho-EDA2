# Análise e interpretação dos resultados

Documento de apoio ao **Critério 5** (Análise e Interpretação). Os números abaixo
são de um *snapshot* real do banco (junho/2026) e são **reproduzíveis** rodando:

```bash
PYTHONPATH=. python -m analise.metricas
```

> As funções que geram cada número estão em [metricas.py](metricas.py)
> (`metricas_projecao`, `comparar_abordagens`, `antes_e_depois`). Este documento
> **interpreta** esses números — não basta tê-los, é preciso discuti-los.

---

## 1. Dataset analisado

| Item | Valor |
|---|---|
| Usuários | 44 |
| Notícias em escopo financeiro | 70 |
| Interações registradas | 481 |

As notícias vêm de coleta RSS real (4 portais); os usuários e as interações são
fictícios, gerados por LLM com perfis coerentes (investidor de renda fixa, trader
de ações, interessado em cripto/câmbio, etc.), de modo que perfis parecidos leem
notícias parecidas — é isso que cria a coocorrência que alimenta o grafo.

---

## 2. Estrutura do grafo de similaridade

Após bipartido → projeção (Jaccard ponderado) → Kruskal:

| Métrica | Valor | Leitura |
|---|---|---|
| Cobertura | **67 / 70 (95,7%)** | só 3 notícias ficaram isoladas (sem nenhum leitor em comum) |
| Arestas na projeção | 1076 | rede densa de similaridades |
| Jaccard mín / médio / máx | 0,013 / **0,14** / 1,0 | a maioria das similaridades é fraca; poucas são fortes |
| Componentes (floresta) | **4** | 4 grupos naturais desconexos |
| Maior árvore | **67 notícias** | um componente gigante concentra quase tudo |
| Arestas na árvore | 66 | = 67 − 1 (árvore geradora exata, sem ciclos) |

**Interpretação.** A projeção é densa (1076 arestas para 70 notícias), mas o
Jaccard médio baixo (0,14) mostra que **a maioria das ligações é fraca** — duas
notícias quaisquer raramente têm muitos leitores fortes em comum. É justamente por
isso que o **Kruskal máximo** é necessário: ele descarta as 1010 arestas mais
fracas e mantém só as 66 mais fortes que preservam a conectividade. A cobertura de
95,7% e o fato de a maior árvore reunir 67 das 70 notícias indicam que o acervo
financeiro é **temático e coeso** — quase tudo se conecta num único esqueleto, e
os 4 componentes são naturais (notícias de nicho sem leitor em comum), não grupos
detectados artificialmente.

---

## 3. Por que árvore + gargalo, e não vizinhança direta?

Comparamos a pipeline (**árvore geradora + DFS por gargalo**) com a baseline
ingênua (**vizinhança direta na projeção**: recomendar o que é diretamente
parecido com o que o usuário já leu, a 1 salto), agregando sobre os 44 usuários:

| Métrica | Pipeline (árvore+gargalo) | Baseline (vizinhança direta) |
|---|---|---|
| Alcance médio de candidatas | **56,6** | 48,1 |
| Sobreposição do Top-10 | — | **60,2%** em comum |
| Recomendações a 2+ saltos | **70,2%** | 0% (impossível) |

**Interpretação — esta é a justificativa central do projeto:**

- **Alcance maior (56,6 vs 48,1).** A árvore alcança ~18% mais candidatas porque
  navega a similaridade **transitivamente**: chega a notícias que não dividem
  leitor com nenhuma semente diretamente, mas estão ligadas a ela por um caminho
  no esqueleto de similaridade. A baseline só enxerga o primeiro anel de vizinhos.

- **40% das recomendações são diferentes.** A sobreposição de Top-10 é de só
  60,2% — ou seja, **4 em cada 10 recomendações da pipeline a baseline não daria**.
  As duas abordagens não são equivalentes.

- **70,2% das recomendações estão a 2+ saltos.** Este é o número decisivo: a
  baseline de vizinhança direta, por definição, **nunca** consegue sugerir essas
  notícias (ela só vê 1 salto). Mais de dois terços do que a pipeline recomenda
  vive além do alcance da abordagem ingênua. É o ganho concreto de modelar a
  recomendação como travessia de grafo.

- **Por que o gargalo controla a qualidade.** Alcançar mais longe poderia
  recomendar lixo. O **score por gargalo** (menor Jaccard do caminho) impede isso:
  uma notícia a 3 saltos só sobe no ranking se **todas** as ligações do caminho
  forem fortes. Assim a pipeline ganha alcance sem perder relevância — o elo mais
  fraco da cadeia é o teto do score.

---

## 4. O sistema aprende com a interação (antes/depois)

Exemplo real (usuário "Alberto Jorge Santos"), simulando **um** like:

```
Top-5 antes : [68, 33, 76, 37, 5]
Top-5 depois: [33, 37, 5, 76, 56]
```

Ao curtir a notícia 68, ela **sai** do feed (vira lida) e uma notícia nova (56)
**entra** no Top-5, além de o ranking se reorganizar. Isto evidencia o **ciclo de
aprendizado**: cada interação vira semente (ou exclusão, no caso de dislike) e a
próxima recomendação muda. Na apresentação, isso é demonstrável ao vivo: ler/curtir
uma notícia e ver o feed se atualizar.

---

## 5. Efeito do gargalo e dos saltos no ranking

Top-6 do mesmo usuário, com o gargalo e a distância de cada recomendação:

| Saltos | Gargalo | Notícia |
|---|---|---|
| 1 | 0,550 | Os desafios de Lula no G7… |
| 1 | 0,545 | 'Prévia do PIB' do Banco Central… |
| 2 | 0,529 | Nova taxação proposta pelos EUA… |
| 1 | 0,500 | Sem reunião formal entre Lula e Trump no G7… |
| 1 | 0,500 | Brava (BRAV3): suspensão de oferta da Ecopetrol… |
| 2 | 0,429 | Por que reabrir o Estreito de Ormuz… |

**Interpretação.** O ranking é dominado pelo gargalo (0,550 → 0,429), não pela
distância: uma notícia a **2 saltos** (0,529) aparece **à frente** de notícias a 1
salto com gargalo menor. Isso confirma que o sistema prioriza a **força da cadeia
de similaridade**, não a mera proximidade — uma conexão indireta forte vale mais
que uma direta fraca. O número de saltos só desempata casos de gargalo igual.

---

## 6. Conclusões

1. O acervo financeiro forma um **grafo coeso** (95,7% de cobertura, 1 componente
   gigante com 67 notícias), validando a hipótese de coocorrência de leitores.
2. A maioria das similaridades é fraca (Jaccard médio 0,14), o que **justifica o
   Kruskal máximo**: reduzir 1076 arestas a 66 mantendo o essencial.
3. A pipeline (árvore + gargalo) **não é equivalente** à vizinhança direta:
   alcança ~18% mais candidatas, difere em 40% do Top-10 e produz **70% de
   recomendações que a baseline jamais alcançaria** — com a qualidade controlada
   pelo gargalo.
4. O sistema **responde às interações**: ler/curtir/descurtir muda o feed
   imediatamente, fechando o ciclo de recomendação.

Estes resultados, e não o app rodando isoladamente, são a evidência de que a
modelagem em grafos resolve o problema de recomendação proposto.
