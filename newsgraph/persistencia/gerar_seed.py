"""Gera um seed.sql autocontido a partir do banco atual.

Exporta um subconjunto pequeno e coerente (usuários + notícias em escopo +
interações) como comandos INSERT, para que o repositório seja autocontido: o
avaliador carrega init_db.sql + seed.sql num PostgreSQL limpo e roda o app sem
precisar das credenciais do Supabase.

Os resumos são truncados (mantêm a estrutura dos dados sem inchar o arquivo).

Uso:  PYTHONPATH=. python -m persistencia.gerar_seed
Saída: persistencia/seed.sql
"""

from pathlib import Path

from persistencia.conexao import get_conexao

_RESUMO_MAX = 600          # trunca resumos longos no seed
_SAIDA = Path(__file__).parent / "seed.sql"


def _sql(valor):
    """Converte um valor Python para literal SQL (com escape de aspas)."""
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    if isinstance(valor, (int, float)):
        return str(valor)
    texto = str(valor)
    if len(texto) > _RESUMO_MAX:
        texto = texto[:_RESUMO_MAX].rstrip() + "…"
    return "'" + texto.replace("'", "''") + "'"


def main():
    conn = get_conexao()
    linhas = [
        "-- NewsGraph — seed de dados fictícios (gerado por persistencia/gerar_seed.py).",
        "-- Carregue DEPOIS de init_db.sql, num PostgreSQL limpo:",
        "--   psql \"$DATABASE_URL\" -f persistencia/init_db.sql",
        "--   psql \"$DATABASE_URL\" -f persistencia/seed.sql",
        "-- Resumos truncados; notícias fora do escopo financeiro foram omitidas.",
        "",
        "BEGIN;",
        "",
    ]
    try:
        with conn.cursor() as cur:
            # Usuários
            cur.execute("SELECT id, nome FROM usuarios ORDER BY id;")
            us = cur.fetchall()
            linhas.append(f"-- {len(us)} usuários")
            for uid, nome in us:
                linhas.append(
                    f"INSERT INTO usuarios (id, nome) VALUES ({uid}, {_sql(nome)});"
                )
            linhas.append("")

            # Notícias em escopo
            cur.execute(
                """
                SELECT id, titulo, resumo, link, fonte, data_publicacao,
                       score_economico, em_escopo
                FROM   noticias
                WHERE  em_escopo = TRUE
                ORDER  BY id;
                """
            )
            ns = cur.fetchall()
            linhas.append(f"-- {len(ns)} notícias (em escopo financeiro)")
            for (nid, tit, res, link, fonte, dt, sc, esc) in ns:
                dt_sql = _sql(dt.isoformat()) if dt is not None else "NULL"
                linhas.append(
                    "INSERT INTO noticias (id, titulo, resumo, link, fonte, "
                    "data_publicacao, score_economico, em_escopo) VALUES ("
                    f"{nid}, {_sql(tit)}, {_sql(res)}, {_sql(link)}, {_sql(fonte)}, "
                    f"{dt_sql}, {sc}, {_sql(esc)});"
                )
            linhas.append("")

            # Interações sobre notícias em escopo
            cur.execute(
                """
                SELECT i.id, i.usuario_id, i.noticia_id, i.tipo_acao, i.peso
                FROM   interacoes i
                JOIN   noticias n ON n.id = i.noticia_id
                WHERE  n.em_escopo = TRUE
                ORDER  BY i.id;
                """
            )
            it = cur.fetchall()
            linhas.append(f"-- {len(it)} interações")
            for (iid, uid, nid, tipo, peso) in it:
                linhas.append(
                    "INSERT INTO interacoes (id, usuario_id, noticia_id, tipo_acao, peso) "
                    f"VALUES ({iid}, {uid}, {nid}, {_sql(tipo)}, {peso});"
                )
            linhas.append("")
    finally:
        conn.close()

    # Reseta as sequences para os próximos INSERTs (do app) não colidirem de id.
    linhas += [
        "-- Ajusta os contadores de id para o maior valor inserido",
        "SELECT setval('usuarios_id_seq',   (SELECT COALESCE(MAX(id), 1) FROM usuarios));",
        "SELECT setval('noticias_id_seq',   (SELECT COALESCE(MAX(id), 1) FROM noticias));",
        "SELECT setval('interacoes_id_seq', (SELECT COALESCE(MAX(id), 1) FROM interacoes));",
        "",
        "COMMIT;",
        "",
    ]

    _SAIDA.write_text("\n".join(linhas), encoding="utf-8")
    print(f"OK. seed gerado: {_SAIDA} ({len(us)} usuários, {len(ns)} notícias, {len(it)} interações)")


if __name__ == "__main__":
    main()
