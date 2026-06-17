"""Teste rápido da camada de repositório (Fase 3).

Insere 1 usuário + 1 notícia + 1 interação e lê de volta. Tudo dentro de uma
transação que sofre ROLLBACK no fim — não polui o banco.

Pula automaticamente se DATABASE_URL não estiver definida.
Rodar:  PYTHONPATH=. python -m tests.test_repositorio
"""

import os

from persistencia.conexao import get_conexao
from persistencia import repositorio


def test_round_trip():
    if not os.environ.get("DATABASE_URL"):
        print("SKIP: DATABASE_URL não definida.")
        return

    conn = get_conexao()
    try:
        with conn.cursor() as cur:
            uid = repositorio.salvar_usuario(cur, "Usuário Teste")

            noticia = {
                "titulo": "Notícia de teste",
                "resumo": "Resumo de teste.",
                "link": "https://exemplo.test/teste-rollback",
                "fonte": "Teste",
                "data_publicacao": None,
            }
            repositorio.salvar_noticia(cur, noticia)
            cur.execute("SELECT id FROM noticias WHERE link = %s;", (noticia["link"],))
            nid = cur.fetchone()[0]

            iid = repositorio.registrar_interacao(cur, uid, nid, "like", 4)

            dados = repositorio.carregar_grafo_dados(cur)
            assert any(u["id"] == uid for u in dados["usuarios"])
            assert any(n["id"] == nid for n in dados["noticias"])
            assert any(i["id"] == iid for i in dados["interacoes"])
            print("OK: usuário, notícia e interação inseridos e lidos de volta.")
    finally:
        conn.rollback()  # nada persiste
        conn.close()


if __name__ == "__main__":
    test_round_trip()
