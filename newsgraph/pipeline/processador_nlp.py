"""Processador de PLN (offline) — spaCy (pt_core_news_sm).

Etapa entre coletar e salvar: limpa o HTML residual do resumo, normaliza
espaços e passa o texto pelo spaCy para tokenização/remoção de stopwords e NER
(empresas e termos econômicos: Selic, IPCA, tickers). É o tratamento de dados
textuais que satisfaz a exigência de PLN.

O modelo spaCy é pesado; é carregado sob demanda (lazy) e uma única vez.
"""

import re

_TAG_HTML = re.compile(r"<[^>]+>")
_ESPACOS = re.compile(r"\s+")

# Termos econômicos reconhecidos por casamento direto (complementam o NER).
TERMOS_ECONOMICOS = ("Selic", "IPCA", "IGP-M", "CDI", "PIB", "Ibovespa", "dólar", "Copom")
_TICKER = re.compile(r"\b[A-Z]{4}\d{1,2}\b")  # ex.: PETR4, VALE3, ITUB4

_nlp = None


def _carregar_nlp():
    """Carrega o modelo spaCy uma única vez."""
    global _nlp
    if _nlp is None:
        import spacy

        _nlp = spacy.load("pt_core_news_sm")
    return _nlp


def limpar_html(texto):
    """Remove tags HTML residuais e normaliza espaços em branco."""
    if not texto:
        return ""
    sem_tags = _TAG_HTML.sub(" ", texto)
    return _ESPACOS.sub(" ", sem_tags).strip()


def tokenizar(texto):
    """Tokeniza, descarta stopwords/pontuação e devolve os lemas relevantes."""
    doc = _carregar_nlp()(texto)
    return [
        tok.lemma_.lower()
        for tok in doc
        if not tok.is_stop and not tok.is_punct and not tok.is_space and tok.lemma_.strip()
    ]


def extrair_entidades(texto):
    """Extrai entidades nomeadas (ORG/LOC/MISC), termos econômicos e tickers."""
    doc = _carregar_nlp()(texto)
    entidades = {ent.text.strip() for ent in doc.ents if ent.label_ in ("ORG", "LOC", "MISC", "PER")}
    for termo in TERMOS_ECONOMICOS:
        if re.search(rf"\b{re.escape(termo)}\b", texto, flags=re.IGNORECASE):
            entidades.add(termo)
    entidades.update(_TICKER.findall(texto))
    return sorted(entidades)


def processar_item(item):
    """Limpa o resumo e anexa tokens/entidades. Devolve o próprio item."""
    resumo_limpo = limpar_html(item.get("resumo", ""))
    item["resumo"] = resumo_limpo
    base = f"{item.get('titulo', '')}. {resumo_limpo}"
    item["tokens"] = tokenizar(base)
    item["entidades"] = extrair_entidades(base)
    return item


def processar(itens):
    """Aplica `processar_item` a cada item coletado."""
    return [processar_item(it) for it in itens]


if __name__ == "__main__":
    exemplo = {
        "titulo": "Copom mantém Selic em 10,5%",
        "resumo": "<p>O <b>Banco Central</b> decidiu... PETR4 sobe.</p>",
    }
    r = processar_item(exemplo)
    print("resumo :", r["resumo"])
    print("tokens :", r["tokens"][:10])
    print("entidades:", r["entidades"])
