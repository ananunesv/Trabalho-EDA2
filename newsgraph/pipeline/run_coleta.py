"""Orquestração da coleta offline.

Fluxo: abre conexão → coleta RSS → limpa/processa (spaCy + filtro de escopo)
→ salva (dedup) → commit → fecha → imprime relatório de escopo.

É o que o GitHub Actions executa a cada 12h.

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

    print("Limpando e processando texto (spaCy + filtro de escopo)...")
    itens = processar(itens)

    # Métricas do filtro antes de gravar
    em_escopo_count = sum(1 for it in itens if it.get("em_escopo", True))
    fora_count      = len(itens) - em_escopo_count
    print(f"  {em_escopo_count} em escopo financeiro / {fora_count} descartadas pelo filtro.")

    print("Gravando no banco (dedup por link)...")
    conn = get_conexao()
    try:
        with conn.cursor() as cur:
            for it in itens:
                repositorio.salvar_noticia(cur, it)

            # Relatório final via banco (inclui coletas anteriores)
            rel = repositorio.relatorio_escopo(cur)

        conn.commit()
        print(
            f"  OK. Total no banco: {rel['total']} notícias "
            f"({rel['em_escopo']} em escopo = {rel['percentual']}% | "
            f"{rel['fora_escopo']} descartadas | limiar={rel['limiar_usado']})"
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()