"""Filtro de escopo financeiro (Issue #3 — Tratamento de dados PLN).

Objetivo: remover notícias fora do mercado financeiro que acabaram entrando
na coleta RSS de portais generalistas (ex.: G1 Economia publica notícias de
saúde, política, etc. misturadas com economia).

Estratégia (100% PLN, sem LLM, sem tagueamento manual):
  1. Lematização via spaCy para normalizar flexões (ação ↔ ações, juro ↔ juros).
  2. Comparação contra léxico financeiro editável (lexico_economico.json).
  3. NER do spaCy para capturar entidades financeiras (ORG, MONEY, PERCENT).
  4. Regex para tickers de ações (PETR4, VALE3 …).
  5. score_economico = contagem total de ocorrências relevantes.
  6. em_escopo = score >= LIMIAR (padrão 2 — configurável em config.py).

Regra de exclusão:
  - score == 0 → sem nenhum termo econômico → fora.
  - score == 1 → menção solta (ex.: "dólar" num texto de esportes) → fora.
  - score >= 2 → vocabulário econômico recorrente → dentro do escopo.

Contrato de interface (o que o resto do projeto enxerga):
  score_economico(titulo: str, resumo: str) -> int
  em_escopo(titulo: str, resumo: str, limiar: int = 2) -> bool
"""

import json
import re
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------------
# Léxico — carregado UMA VEZ em nível de módulo
# ---------------------------------------------------------------------------

_LEXICO_PATH = Path(__file__).parent / "lexico_economico.json"

def _carregar_lexico() -> set[str]:
    """Lê o JSON e devolve um set com todos os lemas do léxico."""
    with open(_LEXICO_PATH, encoding="utf-8") as f:
        dados = json.load(f)

    lemas = set()
    for chave, termos in dados.items():
        if chave.startswith("_"):
            continue  # ignora campos de metadados (_comentario, _instrucao)
        for termo in termos:
            lemas.add(_normalizar(termo))
    return lemas


def _normalizar(texto: str) -> str:
    """Converte para minúsculas e remove acentos para comparação robusta."""
    texto = texto.lower().strip()
    # Remove acentos (NFD separa caractere base + diacrítico; encode ASCII descarta diacríticos)
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    return texto


_LEXICO: set[str] = _carregar_lexico()

# ---------------------------------------------------------------------------
# Regex para tickers de ações (PETR4, VALE3, ITUB4, BBAS3 …)
# ---------------------------------------------------------------------------

_TICKER = re.compile(r"\b[A-Z]{4}\d{1,2}\b")

# Rótulos de entidade do spaCy considerados financeiramente relevantes.
# Só MONEY e PERCENT: ORG casa qualquer organização (Coldplay, ABRH-SP) e
# CARDINAL casa qualquer número — ambos geram muitos falsos positivos.
_LABELS_FINANCEIROS = {"MONEY", "PERCENT"}

# ---------------------------------------------------------------------------
# Carregamento lazy do spaCy (mesmo padrão do processador_nlp.py)
# ---------------------------------------------------------------------------

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("pt_core_news_sm")
    return _nlp


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def score_economico(titulo: str, resumo: str) -> int:
    """Calcula quantos sinais financeiros existem no título + resumo.

    Cada ocorrência de:
      - lema presente no léxico econômico          → +1 por lema único encontrado
      - entidade financeira reconhecida pelo NER   → +1 por entidade única
      - ticker de ação (PETR4, VALE3 …)            → +1 por ticker único

    Retorna a soma total (int >= 0).
    Quanto maior, mais financeiro é o texto.
    """
    texto_completo = f"{titulo or ''} {resumo or ''}"

    # --- 1. Processamento spaCy (lematização + NER) ---
    doc = _get_nlp()(texto_completo)

    # Lemas relevantes encontrados no léxico (1 ponto por lema único)
    lemas_encontrados = set()
    for token in doc:
        if token.is_stop or token.is_punct or token.is_space:
            continue
        lema_norm = _normalizar(token.lemma_)
        if lema_norm in _LEXICO:
            lemas_encontrados.add(lema_norm)

    # --- 2. Entidades financeiras do NER (1 ponto por entidade única) ---
    entidades_financeiras = set()
    for ent in doc.ents:
        if ent.label_ in _LABELS_FINANCEIROS:
            entidades_financeiras.add(ent.text.strip().lower())

    # --- 3. Tickers de ações via regex (1 ponto por ticker único) ---
    tickers = set(_TICKER.findall(texto_completo))

    score = len(lemas_encontrados) + len(entidades_financeiras) + len(tickers)
    return score


def em_escopo(titulo: str, resumo: str, limiar: int = 2) -> bool:
    """Retorna True se a notícia tem vocabulário econômico recorrente.

    Args:
        titulo:  Título da notícia.
        resumo:  Resumo/corpo da notícia.
        limiar:  Quantidade mínima de sinais para considerar em escopo.
                 Padrão 2 (configurável via config.LIMIAR_ESCOPO).
                 score == 0 → sem termos econômicos.
                 score == 1 → menção solta, não recorrente.
                 score >= 2 → vocabulário financeiro presente → True.

    Returns:
        bool: True se score >= limiar, False caso contrário.
    """
    return score_economico(titulo, resumo) >= limiar


# ---------------------------------------------------------------------------
# Execução direta — testes rápidos sem pytest
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    casos = [
        # (titulo, resumo, esperado_em_escopo)
        (
            "Copom mantém Selic em 10,5% ao ano",
            "O Banco Central decidiu manter a taxa básica. PETR4 subiu 2%.",
            True,
        ),
        (
            "Brasil vence Argentina na Copa América",
            "A seleção brasileira garantiu classificação com gol de Vinicius.",
            False,
        ),
        (
            "Petrobras anuncia dividendos recordes",
            "A estatal distribuirá R$ 3,50 por ação. Ibovespa opera em alta.",
            True,
        ),
        (
            "Novo celular é lançado com câmera avançada",
            "O aparelho conta com processador rápido e bateria de longa duração.",
            False,
        ),
        (
            "PIB cresce 0,3% no terceiro trimestre",
            "Resultado ficou abaixo das expectativas do mercado segundo o IBGE.",
            True,
        ),
        (
            "Dólar sobe levemente",           # menção solta — score provável = 1
            "A moeda americana teve leve alta hoje.",
            False,  # score esperado < 2
        ),
    ]

    print(f"{'Título':<50} {'Score':>5}  {'Em escopo?':>10}  {'OK?':>4}")
    print("-" * 80)
    todos_ok = True
    for titulo, resumo, esperado in casos:
        sc = score_economico(titulo, resumo)
        resultado = em_escopo(titulo, resumo)
        ok = resultado == esperado
        if not ok:
            todos_ok = False
        status = "✔" if ok else "✘"
        print(f"{titulo:<50} {sc:>5}  {str(resultado):>10}  {status:>4}")

    print()
    if todos_ok:
        print("Todos os casos passaram.")
    else:
        print("Atenção: algum caso divergiu do esperado — revise o léxico ou o limiar.")