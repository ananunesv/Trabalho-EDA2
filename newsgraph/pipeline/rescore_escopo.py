"""Re-pontua o escopo financeiro das notícias já gravadas no banco.

Necessário porque `salvar_noticia` usa ON CONFLICT DO NOTHING: notícias inseridas
antes do filtro (ou antes de um ajuste no léxico) ficam com score_economico=0 e
em_escopo=TRUE por padrão. Este script recalcula score_economico/em_escopo de
TODAS as notícias e atualiza as linhas.

Uso:
    PYTHONPATH=. python -m pipeline.rescore_escopo            # dry-run (só relatório)
    PYTHONPATH=. python -m pipeline.rescore_escopo --apply    # grava as mudanças
"""

import argparse

from persistencia.conexao import get_conexao
from pipeline.filtro_escopo import score_economico, em_escopo

try:
    from config import LIMIAR_ESCOPO
except ImportError:
    LIMIAR_ESCOPO = 2


def main(apply=False):
    conn = get_conexao()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, titulo, resumo FROM noticias;")
            linhas = cur.fetchall()

            dentro = fora = mudancas = 0
            for nid, titulo, resumo in linhas:
                sc = score_economico(titulo or "", resumo or "")
                escopo = sc >= LIMIAR_ESCOPO
                dentro += int(escopo)
                fora += int(not escopo)
                if apply:
                    cur.execute(
                        "UPDATE noticias SET score_economico=%s, em_escopo=%s WHERE id=%s;",
                        (sc, escopo, nid),
                    )
                    mudancas += 1

        if apply:
            conn.commit()
            print(f"OK. {mudancas} notícias re-pontuadas (limiar={LIMIAR_ESCOPO}).")
        else:
            print("DRY-RUN (nada gravado). Use --apply para gravar.")
        print(f"Total: {len(linhas)} | em escopo: {dentro} | fora: {fora}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-pontua o escopo financeiro das notícias.")
    parser.add_argument("--apply", action="store_true", help="grava as mudanças no banco")
    args = parser.parse_args()
    main(apply=args.apply)
