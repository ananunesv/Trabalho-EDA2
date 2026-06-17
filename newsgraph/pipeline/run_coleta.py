"""Orquestração da coleta offline (Fase 7).

Fluxo: abre conexão -> coleta RSS -> limpa/processa (spaCy) -> salva (dedup) ->
commit -> fecha. É o que o GitHub Actions executa a cada 12h.

Uso local:  python -m pipeline.run_coleta
"""

from persistencia.conexao import get_conexao
from persistencia import repositorio
from pipeline.coletor_rss import coletar
from pipeline.processador_nlp import processar


def main():
    print("Coletando feeds RSS...")
    itens = coletar()
    print(f"  {len(itens)} itens coletados.")

    print("Limpando e processando texto (spaCy)...")
    itens = processar(itens)

    print("Gravando no banco (dedup por link)...")
    conn = get_conexao()
    try:
        with conn.cursor() as cur:
            for it in itens:
                repositorio.salvar_noticia(cur, it)
            cur.execute("SELECT COUNT(*) FROM noticias;")
            total = cur.fetchone()[0]
        conn.commit()
        print(f"  OK. Total de notícias no banco: {total}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
