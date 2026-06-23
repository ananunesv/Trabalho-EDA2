# NewsGraph

Sistema de recomendação de notícias financeiras baseado em grafos, no formato de
uma newsletter interativa. Disciplina **Estruturas de Dados 2 — 2026.1**,
Temática **B** (sistema de recomendação de textos).

---

## 1. Objetivo do projeto

Dado um acervo de notícias financeiras e o histórico de interações de vários
usuários, **recomendar a cada usuário as notícias mais relevantes que ele ainda
não leu**, usando exclusivamente estruturas e algoritmos de grafos
implementados do zero.

O problema é o da Temática B: construir um **grafo bipartido usuário–texto**,
projetá-lo em um **grafo texto–texto** por uma medida de similaridade, aplicar
**filtragem** e produzir um **mecanismo de recomendação**. A hipótese central é:

> *Se duas notícias são lidas pelas mesmas pessoas, elas são parecidas. Logo, se
> você gostou de uma, deve gostar da outra.*

O sistema parte das notícias que o usuário já consumiu (sementes), navega pela
rede de similaridade e entrega um ranking (Top-N). Cada nova interação
(ler, curtir, compartilhar, descurtir) realimenta o grafo e muda a próxima
recomendação — provando, na prática, que a pipeline aprende.

---

## 2. Como rodar o projeto

Pré-requisitos: **Python 3.11** e um banco **PostgreSQL** (usamos Supabase).

```bash
# 1. Dependências
cd newsgraph
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download pt_core_news_sm               # modelo de PLN (português)

# 2. Credenciais (veja "O arquivo .env" abaixo)
cp .env.example .env                                   # depois edite o .env

# 3. Banco de dados (rode UMA vez)
psql "$DATABASE_URL" -f persistencia/init_db.sql       # cria as 3 tabelas
# (se o banco já existia sem as colunas de escopo, use:)
# psql "$DATABASE_URL" -f persistencia/migracao_escopo.sql

# 4. Carga de dados (mundo OFFLINE)
PYTHONPATH=. python -m pipeline.run_coleta             # coleta RSS + PLN + filtro de escopo
PYTHONPATH=. python -m pipeline.gerador_dados          # ~40 usuários fictícios + interações (LLM)

# 5. Aplicação (mundo ONLINE)
PYTHONPATH=. streamlit run app/main.py
```

### Opção rápida: dados de exemplo (sem coleta nem LLM)

Para um repositório **autocontido** — rodar sem credenciais do Supabase e sem
chamar RSS/LLM — use um PostgreSQL local e carregue o seed versionado
([persistencia/seed.sql](persistencia/seed.sql): 44 usuários, 70 notícias em
escopo e 481 interações fictícias):

```bash
psql "$DATABASE_URL" -f persistencia/init_db.sql   # cria as tabelas
psql "$DATABASE_URL" -f persistencia/seed.sql      # popula com os dados de exemplo
PYTHONPATH=. streamlit run app/main.py             # já recomenda
```

O seed é gerado por `persistencia/gerar_seed.py` a partir do banco real.

### O arquivo `.env`

As credenciais nunca ficam no código — moram no `.env` (que está no
`.gitignore`). Copie `.env.example` para `.env` e preencha duas variáveis:

```bash
# Conexão do PostgreSQL/Supabase.
# No Supabase: Project Settings → Database → Connection string (use a conexão
# "Session"/pooler). Se a senha tiver caractere especial, faça URL-encode
# (ex.: @ vira %40).
DATABASE_URL=postgresql://postgres.<ref>:SENHA@aws-0-<regiao>.pooler.supabase.com:5432/postgres

# Chave do Google Gemini, usada SÓ pelo gerador de dados fictícios.
# Pegue em https://aistudio.google.com → "Get API key" (tem camada gratuita).
GEMINI_API_KEY=AIza...
```

- **`DATABASE_URL`** — obrigatória para tudo (coleta, app, análise).
- **`GEMINI_API_KEY`** — só é necessária para rodar `pipeline.gerador_dados`. Se
  você já tem usuários no banco, o app roda sem ela.

### Atualizar os dados depois (comandos do dia a dia)

```bash
# Trazer NOTÍCIAS NOVAS (pode rodar quantas vezes quiser; deduplica por link,
# então notícias repetidas não entram de novo). Cada execução já limpa o texto
# com spaCy e aplica o filtro de escopo antes de gravar.
PYTHONPATH=. python -m pipeline.run_coleta

# MOCAR USUÁRIOS NOVOS via LLM (precisa de GEMINI_API_KEY no .env).
PYTHONPATH=. python -m pipeline.gerador_dados            # NÃO faz nada se já houver usuários
PYTHONPATH=. python -m pipeline.gerador_dados --force    # gera mais ~40 usuários + interações,
                                                         # somando aos que já existem
```

> Observação: o `gerador_dados` sem `--force` é uma proteção — ele só popula um
> banco vazio. Use `--force` para **adicionar** uma nova leva de usuários
> fictícios por cima dos atuais.

### Comandos auxiliares

```bash
# Testes (núcleo de grafos, sem banco)
PYTHONPATH=. python -m unittest tests.teste_jaccard tests.test_busca tests.test_motor
PYTHONPATH=. python tests/test_arvore_geradora.py
PYTHONPATH=. python tests/test_filtro_escopo.py

# Relatório de análise (cobertura, Jaccard, árvore, pipeline x baseline) — precisa do banco
PYTHONPATH=. python -m analise.metricas

# Re-pontuar o escopo das notícias já gravadas (após ajustar o léxico)
PYTHONPATH=. python -m pipeline.rescore_escopo --apply

# Regerar o seed.sql a partir do banco atual
PYTHONPATH=. python -m persistencia.gerar_seed
```

A **interpretação dos resultados** (com números reais e a comparação contra a
baseline de vizinhança direta) está em **[analise/ANALISE.md](analise/ANALISE.md)**.

> **Importante (Streamlit):** ao editar arquivos de `app/`, pare o servidor
> (Ctrl+C) e rode de novo. O auto-reload do Streamlit recarrega o `main.py`, mas
> nem sempre os módulos importados (`login.py`, `feed.py`).

---

## 3. Tecnologias, bibliotecas e frameworks

| Camada | Ferramenta | Para quê |
|---|---|---|
| Linguagem | **Python 3.11** | todo o projeto |
| Banco | **PostgreSQL** (Supabase) | persistência das 3 tabelas |
| Driver SQL | **psycopg2** | conexão Python ↔ PostgreSQL |
| Config | **python-dotenv** | lê `DATABASE_URL`/`GEMINI_API_KEY` do `.env` |
| Coleta | **feedparser** | lê os feeds RSS dos portais |
| PLN | **spaCy** (`pt_core_news_sm`) | limpeza, lematização, stopwords e NER |
| LLM | **google-genai** (Gemini 2.5 Flash) | gera usuários fictícios e interações coerentes |
| Interface | **Streamlit** | login, feed e botões de interação |
| Automação | **GitHub Actions** | roda a coleta a cada 3h |

**Núcleo de grafos: nenhuma biblioteca.** Grafo, Jaccard, Kruskal, union-find,
DFS e Heap Max são implementados à mão em `core/` — as bibliotecas acima cobrem
só coleta, PLN, banco e interface, nunca os algoritmos de grafo (exigência do
trabalho: bibliotecas prontas de grafos = −5,0).

---

## 4. Arquitetura e lógica completa

### 4.1 Princípio: dois mundos separados pelo banco

O sistema é dividido em dois mundos que **nunca se misturam em tempo de
execução**; o banco de dados é o único ponto de contato entre eles.

```
        MUNDO OFFLINE (pipeline/)                 MUNDO ONLINE (app/ + recomendacao/)
   ┌─────────────────────────────┐            ┌──────────────────────────────────┐
   │ coleta RSS → PLN → filtro    │            │ lê do banco → monta o grafo em    │
   │ → grava notícias             │  ──────▶   │ memória → recomenda → mostra feed │
   │ LLM → gera usuários/interações│   BANCO   │ → grava novas interações          │
   └─────────────────────────────┘ PostgreSQL └──────────────────────────────────┘
        (GitHub Actions, sem usuário)               (Streamlit, com usuário)
```

- **Offline** roda agendado (Actions, de 3 em 3 horas) ou manualmente, sem ninguém
  presente: é caro (rede, spaCy, LLM) e não pode travar a navegação.
- **Online** só lê dados já limpos e responde em poucos segundos.

### 4.2 Camadas e a regra de dependência

```
app/            ← interface Streamlit (login, feed, leitura)
recomendacao/   ← motor.py: orquestra o núcleo para um usuário
core/           ← NÚCLEO DE GRAFOS (Python puro, algoritmos do zero)
persistencia/   ← repositorio.py: a ÚNICA porta para o SQL
pipeline/       ← coleta, PLN, filtro de escopo, geração via LLM
analise/        ← metricas.py: análise dos resultados
config.py       ← todos os parâmetros num lugar só
```

Regra central: **o `core/` é puro**. Ele recebe dados em memória e devolve
resultado — não importa banco, Streamlit, spaCy nem LLM. Isso garante que os
algoritmos são testáveis isoladamente (com *fixtures* sintéticas) e que ninguém
escreve SQL fora de `persistencia/repositorio.py`.

### 4.3 Modelo de dados (vértices e arestas)

Três tabelas. As duas primeiras são os **vértices** do bipartido; a terceira são
as **arestas**.

**`usuarios`** — vértice-usuário: `id`, `nome`, `criado_em`.

**`noticias`** — vértice-notícia: `id`, `titulo`, `resumo`, `link` (UNIQUE — chave
de deduplicação), `fonte`, `data_publicacao`, `coletado_em`, e dois campos do
filtro de PLN: `score_economico` (int) e `em_escopo` (bool).

**`interacoes`** — aresta usuário→notícia: `id`, `usuario_id`, `noticia_id`,
`tipo_acao`, `peso`, `timestamp`.

O **peso da ação** codifica a intensidade do interesse:

| Ação | Peso | Sinal |
|---|---|---|
| `clique` (ler) | **1** | interesse fraco |
| `like` | **4** | gostou |
| `compartilhar` | **5** | gostou muito |
| `dislike` | **−3** | rejeitou (exclui a notícia das sementes) |

Esse peso é o que alimenta o Jaccard ponderado e define as sementes do DFS.

### 4.4 O caminho dos dados (passo a passo)

```
RSS (4 portais)
  → coletor_rss.py        (feedparser; 1 dict por notícia)
  → processador_nlp.py    (limpa HTML, lematiza, NER via spaCy)
  → filtro_escopo.py      (score_economico → em_escopo)
  → repositorio.salvar_noticia  (dedup por link; grava no banco)
  ───────────────────────────────────────────────────────────── (offline)
  → gerador_dados.py      (LLM cria ~40 usuários + interações coerentes)
  ───────────────────────────────────────────────────────────── (online)
  → repositorio.carregar_grafo_dados   (lê só o que está em_escopo)
  → grafo_bipartido       (usuário↔notícia, com peso)
  → projecao + jaccard    (texto↔texto, similaridade)
  → arvore_geradora       (Kruskal: floresta geradora máxima)
  → busca                 (DFS a partir das sementes; score = gargalo × recência)
  → heap_max              (Top-N)
  → app (feed)            (mostra; cada interação volta ao banco)
```

### 4.5 O núcleo de grafos — estruturas, algoritmos e decisões

#### a) `Grafo` — lista de adjacência ([core/grafo.py](core/grafo.py))

Representação: **dicionário de dicionários** `{u: {v: peso}}`.

**Decisão: lista de adjacência (e não matriz).** O grafo é **esparso** — cada
notícia se liga só a algumas dezenas de outras (as que têm leitor em comum), não
a todas. Numa matriz de adjacência o custo de espaço é sempre **O(V²)** (com as 300
notícias-alvo do dataset, 90 000 células, quase todas zero; o acervo real hoje tem
~136 em escopo) e percorrer os vizinhos de um vértice
custa **O(V)**. Com lista de adjacência o espaço é **O(V + E)** (só as arestas que
existem) e percorrer vizinhos é **O(grau)** — exatamente o que o DFS e o Kruskal
precisam. Usamos *dict de dict* (em vez de *dict de lista*) para também ter
`tem_aresta(u,v)` e `peso(u,v)` em **O(1)**.

#### b) `GrafoBipartido` ([core/grafo_bipartido.py](core/grafo_bipartido.py))

Modela o grafo usuário↔notícia. Internamente guarda três mapas:
`_leitores` (`{noticia: {usuario: peso}}`, alimenta o Jaccard), `_leituras`
(`{usuario: {noticia: peso}}`, dá as sementes) e `_dislikes`
(`{usuario: {noticias}}`). Interação com peso ≤ 0 (dislike) **não vira aresta
positiva**: vai para `_dislikes` e serve só para excluir a notícia.

#### c) Jaccard ponderado ([core/jaccard.py](core/jaccard.py))

Similaridade entre duas notícias A e B a partir de quem as leu:

```
J(A,B) = Σ_u min(w_A(u), w_B(u))  /  Σ_u max(w_A(u), w_B(u))
```

onde `w_X(u)` é o peso da interação do usuário `u` com a notícia `X` (0 se não
interagiu). Exemplo: A lida pelos usuários {1:like(4), 2:clique(1)} e B por
{1:like(4)}. Σmin = min(4,4)+min(1,0) = 4; Σmax = max(4,4)+max(1,0) = 5; logo
**J = 4/5 = 0.8**.

**Decisão: Jaccard ponderado (e não similaridade semântica do texto).** A
Temática B permite "similaridade semântica e/ou coocorrência de usuários".
Escolhemos **coocorrência de leitores** porque (1) é o que melhor representa o
comportamento real numa newsletter, (2) é determinística e sem parâmetro a
calibrar, e (3) o peso da ação enriquece a medida — uma notícia *curtida* em
comum pesa mais que uma só *clicada*. Quando todos os pesos são iguais, a fórmula
**se reduz ao Jaccard clássico** `|A∩B| / |A∪B|` (verificado em teste).

#### d) Projeção texto↔texto ([core/projecao.py](core/projecao.py))

Transforma o bipartido num grafo só de notícias: para cada par (i, j) calcula
`J(i,j)` e cria uma aresta com esse peso. Custo **O(n²)** pares; com filtro: se as
duas notícias não têm nenhum leitor em comum, o Jaccard é 0 e o par é pulado
(interseção vazia testada antes do cálculo). É a primeira **técnica de
filtragem**: arestas de peso 0 não entram, e há um `limiar_jaccard` opcional para
descartar similaridades fracas.

#### e) Kruskal — floresta geradora máxima ([core/arvore_geradora.py](core/arvore_geradora.py))

A projeção é densa demais (milhares de arestas). Reduzimos ao **esqueleto** das
ligações mais fortes:

1. ordena as arestas por peso **decrescente** (queremos as similaridades
   máximas — daí *máxima*, não mínima);
2. percorre em ordem e adiciona uma aresta só se ela **liga dois grupos ainda
   separados**, usando **union-find** (a segunda estrutura auxiliar) com
   compressão de caminho e união por rank — detecção de ciclo em ~O(α(n)),
   praticamente constante;
3. o resultado é uma árvore com **N−1 arestas**, sem ciclos, conexa.

**Decisão: floresta, não uma única árvore.** Com dados reais, muitas notícias não
compartilham nenhum leitor e a projeção fica **desconexa**. `kruskal_max` exige
conexidade (e lança erro se faltar aresta — usado nos testes do caso ideal), mas o
motor usa **`kruskal_max_floresta`**, que devolve a árvore geradora máxima de
**cada componente**. Isso **não é detecção de comunidades** (Temática D): não
rotulamos nem interpretamos os grupos como tópicos; apenas preservamos o esqueleto
de similaridade que existir, e o DFS alcança o que estiver na mesma árvore das
sementes.

#### f) DFS + gargalo ([core/busca.py](core/busca.py))

A partir das **sementes** (notícias que o usuário leu positivamente), uma busca
em profundidade percorre a árvore. Para cada notícia não-lida calcula:

- **gargalo** = o **menor peso de aresta** no caminho da semente até ela;
- **saltos** = número de arestas percorridas até a semente;
- **score (ranking) = gargalo × recência da semente** (ver decisão abaixo).

Como a estrutura é uma **árvore**, existe **um único caminho** entre quaisquer dois
nós (sem ciclos) — então o gargalo e o número de saltos são exatos e a DFS não
precisa de marcação de visitados complexa (basta não voltar para o pai). Quando uma
notícia é alcançável por **mais de uma semente**, fica com o caminho de **maior
score**; saltos só desempata (caminhos de score igual).

**Decisão: gargalo (mínimo do caminho), não soma nem produto.** A intuição é
*"uma recomendação é tão confiável quanto o elo mais fraco da cadeia de
similaridade que a liga ao que você já gostou"*. É uma medida conservadora:
basta uma ligação fraca no caminho para derrubar o score. As notícias lidas são
**atravessadas** (para alcançar as novas) mas **nunca recomendadas** (excluídas da
saída). Empate de score é desfeito por **menos saltos** (semente mais perto).

**Decisão: ponderar o gargalo pela recência da semente.** As sementes de um
usuário **só crescem** (ler/curtir nunca remove um sinal positivo), e somar
sementes nunca *diminui* o gargalo de quem já estava no topo. Sem recência, o #1
do feed ficaria **preso** na notícia de maior afinidade de todo o histórico até
ser aberta. Então cada semente recebe um peso: a interação **mais recente** vale
`1.0` e as anteriores decaem geometricamente (`FATOR_RECENCIA ** posição`, com
`FATOR_RECENCIA = 0.8` em [config.py](config.py)). O ranking passa a usar
`gargalo × recência`, de modo que o topo acompanha o que o usuário leu por último.
`FATOR_RECENCIA = 1.0` desliga a recência (volta ao gargalo puro) — é o valor de
comparação do Critério 5. O gargalo "cru" continua sendo o número de **afinidade**
exibido no cartão.

#### g) Heap Max — Top-N ([core/heap_max.py](core/heap_max.py))

As notícias candidatas entram num **heap binário de máximo** (a estrutura de dados
adicional exigida, além do grafo) com prioridade igual à tupla
**`(score, −saltos)`** — onde `score` é o gargalo ponderado pela recência: o score
domina e, em empate, menos saltos sobe. Extrair o Top-N custa **O(N log M)**
(M = candidatas), sem ordenar a lista inteira.

**Decisão: heap (e não `sorted`).** Para um feed de tamanho N pequeno sobre M
candidatas, o heap dá o Top-N em tempo de extração logarítmico e deixa a
estrutura adicional explícita e justificada — exatamente o que o Critério 3 pede.

### 4.6 Filtro de escopo (o elemento de PLN) ([pipeline/filtro_escopo.py](pipeline/filtro_escopo.py))

Os portais RSS misturam economia com esporte, política e variedades. Para manter o
grafo coerente, cada notícia recebe um `score_economico`:

- **lematização** (spaCy) normaliza flexões (ações↔ação, juros↔juro) e compara
  contra um **léxico financeiro** editável ([pipeline/lexico_economico.json](pipeline/lexico_economico.json));
- **NER** conta entidades dos tipos **MONEY** e **PERCENT** (valores e percentuais);
- **regex** captura tickers de ações (PETR4, VALE3…);
- `score_economico` = nº de sinais distintos; `em_escopo = score ≥ 2`.

**Decisões de calibragem:** o NER conta só `MONEY`/`PERCENT` — `ORG` casava
qualquer organização (até "Coldplay") e `CARDINAL` qualquer número, gerando falsos
positivos. O léxico evita termos polissêmicos ("meta", "resultado", "taxa") pela
mesma razão. O limiar 2 separa "menção solta" (1 sinal, ex.: "dólar" num texto de
esporte) de "vocabulário recorrente" (≥ 2). Notícias fora do escopo ficam no banco
com `em_escopo = FALSE` e são **filtradas na camada de repositório** — não viram
vértices nem arestas, e até as interações fictícias sobre elas são ignoradas.

### 4.7 Geração de dados fictícios (uso de LLM) ([pipeline/gerador_dados.py](pipeline/gerador_dados.py))

Sem usuários, a projeção nasce vazia (duas notícias nunca teriam leitor em comum).
O **Gemini 2.5 Flash** gera ~40 personas com perfis variados e, para cada uma,
8–20 interações coerentes com o perfil (saída estruturada validada por Pydantic),
em **lotes de 8 usuários** por chamada (`config.USUARIOS_POR_LOTE`) e com o
*thinking* do modelo desligado (custo/latência). Perfis parecidos leem notícias
parecidas → cria a **coocorrência** que alimenta o Jaccard. O LLM é usado **só na
geração de dados**, nunca na recomendação.

### 4.8 Motor de recomendação ([recomendacao/motor.py](recomendacao/motor.py))

É o ponto de convergência. Para um `usuario_id`:

1. monta bipartido → projeção → floresta geradora máxima;
2. **sementes** = notícias lidas positivamente **menos** as com dislike (abrir
   para ler conta como `clique`; um dislike posterior tira a notícia das sementes);
3. calcula o **peso de recência** de cada semente (mais recente = `1.0`, ver 4.5f);
4. roda o DFS com esses pesos, empilha no Heap Max, extrai o Top-N e **exclui as
   lidas** (e as *ocultas*, abaixo);
5. **cold start:** usuário sem interações recebe as notícias em escopo mais
   recentes (até ter histórico para personalizar).

**"Pular" sem marcar como lida (`ocultas`).** O botão *"Procurar mais notícias"*
do feed manda as recomendações atuais sumirem e traz as próximas. Para isso o
motor aceita um conjunto `ocultas`: esses ids entram na **mesma exclusão das
lidas** — somem do resultado **mas continuam atravessados como ponte na árvore**,
então as notícias "atrás" delas continuam alcançáveis. Diferente de um dislike,
elas **não viram sementes nem sinal negativo** e **não vão ao banco** (vivem só na
sessão). É o reaproveitamento direto do mecanismo "atravessa mas não recomenda" da
DFS (4.5f) — nenhuma mudança no núcleo.

Separado em camada **pura** (`recomendar_de_dados`, testável sem banco) e camada
de **banco** (`recomendar`, que enriquece o resultado com título/resumo/link).

### 4.9 Aplicação ([app/](app/))

- **Login** ([app/login.py](app/login.py)): nome de usuário ou criação de conta;
  o id fica na URL (query param) para o login sobreviver ao F5.
- **Feed** ([app/feed.py](app/feed.py)): lista o Top-N em cartões (título, fonte,
  afinidade/gargalo, saltos, recência, trecho). "Ler mais" abre a notícia inteira
  em parágrafos, com navegação por setas ‹ › entre as recomendações e os botões de
  reação (gostei/compartilhar/não tem a ver) no fim. O texto é escapado para o
  Streamlit não interpretar `US$`, `*` etc. como markdown/LaTeX.
- **Compartilhar (copiar link):** além de registrar a interação (peso 5), o botão
  abre um painel **"Copiar link da notícia"** que copia a URL para a área de
  transferência (Clipboard API, com reserva `textarea`+`execCommand`) e confirma
  com um balão **"URL copiada!"**. A cópia acontece no **clique** do botão porque
  o navegador bloqueia escrita no clipboard fora de um gesto do usuário.
- **Procurar mais notícias:** troca a página inteira — as recomendações exibidas
  ficam **invisíveis** (entram em `ocultas`, ver 4.8) e a próxima leva do ranking
  aparece no lugar, sem repetir. Não conta como leitura nem dislike: é só "essas
  não me interessam agora". Ao chegar ao fim, um botão **"Recomeçar do topo"**
  limpa as ocultas. Esse estado vive só na sessão (um F5 ou o logout zera).
- **Ciclo de aprendizado:** cada interação grava no banco; ao voltar ao feed ou
  recarregar, as lidas somem e novas entram, e o topo acompanha a leitura mais
  recente (recência) — a prova visível de que a pipeline de grafos funciona.

---

## 5. Resultados / Números-chave

*Snapshot do banco em 22/06/2026, reproduzível com `PYTHONPATH=. python -m analise.metricas`.
A interpretação completa está em [analise/ANALISE.md](analise/ANALISE.md). Os valores
absolutos sobem com a coleta automática; o que é **estrutural** não muda.*

| Métrica | Valor |
|---|---|
| Usuários / notícias em escopo / interações | 47 / 136 / ~800 |
| Cobertura da projeção | 73/136 (53,7%) — 1 árvore gigante + 63 notícias ainda sem leitor em comum |
| Maior árvore geradora (Kruskal) | 73 notícias, 72 arestas |
| Jaccard médio das similaridades | ~0,13 (maioria fraca → justifica o Kruskal máximo) |
| **Recomendações a 2+ saltos** | **93,7%** — a vizinhança direta (baseline) nunca alcança |
| Top-10 diferente da baseline | ~43% (57,2% de sobreposição) |
| Alcance vs baseline | 60,4 vs 59,7 (empate — o ganho é estrutural, não de alcance bruto) |

**O que isso prova.** O valor da pipeline não é alcançar *mais* notícias, e sim
alcançar as *certas que a vizinhança direta não vê*: **93,7% das recomendações vivem
a 2+ saltos** das sementes, com a relevância controlada pelo gargalo — uma notícia
distante só sobe no ranking se **todo** o caminho até ela for forte.

**Aprende com a interação** (exemplo real, usuário 57): ao curtir a notícia do topo,
ela sai do feed e o ranking se reorganiza — `[33, 90, 42, 20, 57]` → `[90, 20, 42, 57, 230]`.
E o **gargalo manda sobre a distância**: uma notícia a **3 saltos** (gargalo 0,548)
aparece **à frente** de uma a **2 saltos** (gargalo 0,536). Detalhes em
[ANALISE.md](analise/ANALISE.md) §4–5.

---

## 6. Resumo das decisões de projeto

| Decisão | Por quê |
|---|---|
| Lista de adjacência (dict de dict) | grafo esparso: O(V+E) de espaço, vizinhos em O(grau), aresta em O(1) |
| Jaccard ponderado por leitores | coocorrência real + intensidade da ação; determinístico; reduz ao clássico |
| Floresta geradora máxima | dados reais são desconexos; preserva o esqueleto sem detectar comunidades |
| Score por gargalo | mede o elo mais fraco da cadeia de similaridade; conservador |
| Recência das sementes | sementes só crescem; sem isso o #1 trava — recência destrava o topo |
| Ocultar ("Procurar mais") | pula sem virar lida/dislike; reusa o "atravessa mas não recomenda" da DFS |
| Heap Max para o Top-N | estrutura adicional exigida; Top-N sem ordenar tudo |
| Union-find no Kruskal | detecção de ciclo quase O(1) |
| Filtro de escopo por spaCy | elemento de PLN; mantém o grafo só com finanças |
| LLM só para dados fictícios | cria coocorrência; algoritmos seguem 100% do grupo |
| Banco como única fronteira | separa o caro (offline) do interativo (online) |

## 7. Estruturas e algoritmos implementados do zero

Grafo (lista de adjacência) · Grafo bipartido · Jaccard ponderado · Projeção ·
Kruskal (árvore/floresta geradora máxima) · Union-find · DFS (travessia +
gargalo) · Heap Max (Top-N).
