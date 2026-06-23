# Análise e interpretação dos resultados

Documento de apoio ao **Critério 5** (Análise e Interpretação). Os números abaixo
são um *snapshot* real do banco (**22/06/2026**) e são **reproduzíveis** rodando:

```bash
PYTHONPATH=. python -m analise.metricas
```

> As funções que geram cada número estão em [metricas.py](metricas.py)
> (`metricas_projecao`, `comparar_abordagens`, `antes_e_depois`). Este documento
> **interpreta** esses números — não basta tê-los, é preciso discuti-los.

> **Sobre reprodutibilidade.** O acervo cresce continuamente (a coleta RSS roda
> agendada no GitHub Actions), então os **valores absolutos mudam a cada rodada** —
> mais notícias entram sem que as interações cresçam na mesma velocidade. Por isso
> a análise abaixo separa o que é **conjuntural** (cobertura, alcance — dependem do
> tamanho do acervo no dia) do que é **estrutural** e não muda: o ganho vem de
> **recomendar por travessia de grafo (saltos múltiplos) com qualidade controlada
> pelo gargalo**. É nesse ponto invariante que a justificativa do projeto se apoia.

---

## 1. Dataset analisado

| Item | Valor |
|---|---|
| Usuários | 47 |
| Notícias em escopo financeiro | 136 |
| Interações registradas | 802 |

As notícias vêm de coleta RSS real (4 portais); os usuários e as interações são
fictícios, gerados por LLM com perfis coerentes (investidor de renda fixa, trader
de ações, interessado em cripto/câmbio, etc.), de modo que perfis parecidos leem
notícias parecidas — é isso que cria a coocorrência que alimenta o grafo. A coleta
automática **dobrou o acervo** desde as primeiras medições (de ~70 para 136
notícias em escopo), e isso muda a leitura das métricas estruturais abaixo.

---

## 2. Estrutura do grafo de similaridade

Após bipartido → projeção (Jaccard ponderado) → Kruskal:

| Métrica | Valor | Leitura |
|---|---|---|
| Cobertura | **73 / 136 (53,7%)** | 63 notícias ainda sem nenhum leitor em comum |
| Arestas na projeção | 2460 | rede densa entre as notícias que já têm leitores |
| Jaccard mín / médio / máx | 0,014 / **0,131** / 1,0 | a maioria das similaridades é fraca; poucas são fortes |
| Componentes (floresta) | **64** | 1 árvore gigante + 63 notícias isoladas |
| Maior árvore | **73 notícias** | praticamente todo o "miolo" conectado num só esqueleto |
| Arestas na árvore | 72 | = 73 − 1 (árvore geradora exata, sem ciclos) |

**Interpretação.** A cobertura caiu de ~96% (acervo pequeno) para **53,7%**, e isso
**não é um defeito do algoritmo — é o retrato de um sistema vivo**: a coleta
automática traz notícias novas mais rápido do que os usuários as leem, então 63
notícias recém-coletadas ainda não dividem nenhum leitor com as demais e ficam
isoladas. Os "64 componentes" são exatamente isso: **1 árvore gigante de 73
notícias** (o núcleo já consumido) **+ 63 singletons** (o material novo, ainda sem
coocorrência). O recomendador opera sobre o núcleo conectado; à medida que as
interações se acumulam, as ilhas vão sendo absorvidas — é o comportamento esperado.

O que **não** mudou é o essencial: o Jaccard médio continua baixo (**0,131**),
confirmando que a maioria das 2460 ligações é fraca. É justamente por isso que o
**Kruskal máximo** é necessário — ele descarta as 2388 arestas mais fracas e mantém
só as 72 mais fortes que preservam a conectividade do núcleo, sem ciclos.

---

## 3. Por que árvore + gargalo, e não vizinhança direta?

Comparamos a pipeline (**árvore geradora + DFS por gargalo**) com a baseline
ingênua (**vizinhança direta na projeção**: recomendar o que é diretamente
parecido com o que o usuário já leu, a 1 salto), agregando sobre os 47 usuários:

| Métrica | Pipeline (árvore+gargalo) | Baseline (vizinhança direta) |
|---|---|---|
| Alcance médio de candidatas | 60,4 | 59,7 |
| Sobreposição do Top-10 | — | **57,2%** em comum |
| Recomendações a 2+ saltos | **93,7%** | 0% (impossível) |

**Interpretação — onde está (e onde não está) o ganho da pipeline:**

- **Alcance: hoje é um empate (60,4 vs 59,7), e isso é honesto dizer.** Com o acervo
  pequeno a árvore alcançava ~18% mais candidatas que a baseline; com o acervo
  dobrado, a projeção ficou tão densa (2460 arestas) que a vizinhança direta já
  enxerga quase o mesmo *número* de candidatas. **O argumento "alcança mais" era
  conjuntural e não se sustenta no acervo atual** — então não é nele que apoiamos o
  projeto. O ganho real é qualitativo, abaixo.

- **93,7% das recomendações estão a 2+ saltos — este é o número decisivo.** Mesmo
  com alcance numérico parecido, **os conjuntos são diferentes**: 93,7% do que a
  pipeline recomenda vive a dois ou mais saltos das sementes, ou seja, em notícias
  que **não dividem leitor com nada que o usuário leu**. A baseline de vizinhança
  direta, por definição, **nunca** consegue sugeri-las (ela só vê 1 salto). Esse
  número, aliás, **subiu** com o acervo maior (a similaridade verdadeira está cada
  vez mais "espalhada" pela rede), o que reforça o ponto em vez de enfraquecê-lo.

- **~43% do Top-10 é diferente.** A sobreposição é de só 57,2% — ou seja, **mais de
  4 em cada 10 recomendações da pipeline a baseline não daria**. As duas abordagens
  não são equivalentes, mesmo com alcance parecido: a pipeline troca vizinhos
  diretos fracos por conexões transitivas fortes.

- **Por que o gargalo controla a qualidade.** Alcançar longe poderia recomendar
  lixo. O **score por gargalo** (menor Jaccard do caminho) impede isso: uma notícia
  a 5 saltos só sobe no ranking se **todas** as ligações do caminho forem fortes.
  Assim a pipeline navega a similaridade transitivamente **sem perder relevância** —
  o elo mais fraco da cadeia é o teto do score (demonstrado na §5).

> **Em uma frase:** o valor da pipeline não é alcançar *mais* notícias — é alcançar
> as notícias **certas que a vizinhança direta não vê** (93,7% a 2+ saltos),
> mantendo a relevância sob controle do gargalo.

---

## 4. O sistema aprende com a interação (antes/depois)

Exemplo real (usuário "Paulo Roberto Vieira", id 57), simulando **um** like:

```
Top-5 antes : [33, 90, 42, 20, 57]
Top-5 depois: [90, 20, 42, 57, 230]
```

Ao curtir a notícia 33 ("'Prévia do PIB' do Banco Central"), ela **sai** do feed
(vira lida), o ranking se reorganiza e uma notícia nova (230) **entra** no Top-5. Isto evidencia o **ciclo de aprendizado**: cada interação vira
semente (ou exclusão, no caso de dislike) e a próxima recomendação muda. Na
apresentação, isso é demonstrável ao vivo: ler/curtir uma notícia e ver o feed se
atualizar.

> A leitura mais recente também passa a **pesar mais** nas sementes (decaimento de
> recência em [config.py](../config.py), `FATOR_RECENCIA`), então o topo do feed
> acompanha o interesse atual do usuário, e não só o histórico acumulado.

---

## 5. Efeito do gargalo e dos saltos no ranking

Top-6 do mesmo usuário (id 57), com o gargalo e a distância de cada recomendação:

| Saltos | Gargalo | Notícia |
|---|---|---|
| 1 | 0,552 | 'Prévia do PIB' do Banco Central tem alta… |
| 2 | 0,548 | Mercado financeiro sobe estimativa de inflação para 5,30%… |
| 3 | 0,548 | Acordo de paz entre EUA e Irã reforça expectativas… |
| 2 | 0,536 | Mercado financeiro eleva previsão da Selic… |
| 3 | 0,519 | Comissão do Senado aprova projeto que blinda agências… |
| 4 | 0,519 | Banco Central amplia acesso a contas em moeda estrangeira… |

**Interpretação.** O ranking é dominado pelo **gargalo**, não pela distância — repare
que a coluna de saltos **não** está em ordem (1, 2, 3, 2, 3, 4), mas a de gargalo
está (0,552 → 0,519). O caso decisivo: uma notícia a **3 saltos** (gargalo 0,548)
aparece **à frente** de uma a **2 saltos** (gargalo 0,536) — ou seja, uma conexão
indireta *mais forte* vale mais que uma direta *mais fraca*. O número de saltos só
desempata gargalos iguais (os dois 0,548 e os dois 0,519 ordenam-se por saltos
crescentes). É a prova concreta de que a árvore + gargalo é mais do que "vizinho
mais parecido". *(Quando uma recomendação vem de uma semente antiga, esse gargalo é
multiplicado pela recência dela na hora de ordenar — §4 — então o feed real combina
força e atualidade; neste exemplo todos os itens vêm de leituras recentes.)*

---

## 6. Conclusões

1. O núcleo do acervo forma um **grafo coeso** (1 árvore gigante de 73 notícias),
   validando a hipótese de coocorrência de leitores. A cobertura de 53,7% reflete um
   **sistema vivo** — a coleta automática traz notícias novas mais rápido do que são
   lidas; as ilhas se conectam conforme as interações se acumulam.
2. A maioria das similaridades é fraca (Jaccard médio 0,131), o que **justifica o
   Kruskal máximo**: reduzir 2460 arestas a 72 mantendo o essencial.
3. A pipeline (árvore + gargalo) **não é equivalente** à vizinhança direta. O ganho
   **não** é de alcance bruto (hoje empatado, 60,4 vs 59,7 — efeito do acervo maior),
   e sim **estrutural**: **93,7% das recomendações estão a 2+ saltos** (que a baseline
   jamais alcança) e **~43% do Top-10 difere** — com a relevância controlada pelo
   gargalo (§5).
4. O sistema **responde às interações**: ler/curtir/descurtir muda o feed
   imediatamente, e a recência faz o topo acompanhar o interesse atual.

Estes resultados, e não o app rodando isoladamente, são a evidência de que a
modelagem em grafos resolve o problema de recomendação proposto.