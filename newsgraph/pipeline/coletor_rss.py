"""Coletor RSS (offline).

Lê os feeds de `config.FEEDS`, extrai os campos de cada item com feedparser e
devolve uma lista de dicts. A deduplicação acontece no banco, via
`ON CONFLICT (link)` em `repositorio.salvar_noticia`.
"""

from datetime import datetime

import feedparser

from config import FEEDS


def _data_publicacao(entry):
    """Converte a data do item para datetime (ou None se ausente)."""
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    if t is None:
        return None
    return datetime(*t[:6])


def coletar(feeds=None):
    """Percorre os feeds e devolve os itens normalizados."""
    feeds = feeds or FEEDS
    itens = []
    for fonte, url in feeds.items():
        d = feedparser.parse(url)
        for e in d.entries:
            link = e.get("link", "").strip()
            if not link:
                continue  # sem link não há chave de deduplicação
            itens.append(
                {
                    "titulo": e.get("title", "").strip(),
                    "resumo": e.get("summary", ""),
                    "link": link,
                    "fonte": fonte,
                    "data_publicacao": _data_publicacao(e),
                }
            )
    return itens


if __name__ == "__main__":
    itens = coletar()
    print(f"Coletados {len(itens)} itens de {len(FEEDS)} feeds.")
    for it in itens[:5]:
        print(f"  [{it['fonte']}] {it['titulo'][:70]}")
