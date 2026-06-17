"""Camada de repositório — a única porta para o SQL.

Recebe um cursor (`cur`) já aberto e executa as operações. Quem chama controla
a transação (commit/rollback). O núcleo de grafos nunca toca nestas funções:
ele recebe os dados em memória de `carregar_grafo_dados`.
"""


def salvar_noticia(cur, n):
    """Insere uma notícia. Dedup automático por `link` (ON CONFLICT DO NOTHING).

    Pode rodar a coleta quantas vezes quiser sem duplicar.
    """
    cur.execute(
        """
        INSERT INTO noticias (titulo, resumo, link, fonte, data_publicacao)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (link) DO NOTHING;
        """,
        (n["titulo"], n["resumo"], n["link"], n["fonte"], n["data_publicacao"]),
    )


def salvar_usuario(cur, nome):
    """Insere um usuário e devolve o `id` gerado."""
    cur.execute(
        "INSERT INTO usuarios (nome) VALUES (%s) RETURNING id;",
        (nome,),
    )
    return cur.fetchone()[0]


def registrar_interacao(cur, usuario_id, noticia_id, tipo_acao, peso):
    """Registra uma aresta do bipartido (usuário -> notícia) e devolve o `id`."""
    cur.execute(
        """
        INSERT INTO interacoes (usuario_id, noticia_id, tipo_acao, peso)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
        """,
        (usuario_id, noticia_id, tipo_acao, peso),
    )
    return cur.fetchone()[0]


def buscar_noticias(cur):
    """Lista as notícias para o feed (mais recentes primeiro)."""
    cur.execute(
        """
        SELECT id, titulo, resumo, link, fonte, data_publicacao, coletado_em
        FROM noticias
        ORDER BY coletado_em DESC, id DESC;
        """
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def carregar_grafo_dados(cur):
    """Devolve `usuarios`, `noticias` e `interacoes` em memória.

    É o que alimenta o núcleo de grafos — que nunca toca o banco.
    """
    cur.execute("SELECT id, nome, criado_em FROM usuarios;")
    u_cols = [d[0] for d in cur.description]
    usuarios = [dict(zip(u_cols, row)) for row in cur.fetchall()]

    cur.execute(
        "SELECT id, titulo, resumo, link, fonte, data_publicacao, coletado_em FROM noticias;"
    )
    n_cols = [d[0] for d in cur.description]
    noticias = [dict(zip(n_cols, row)) for row in cur.fetchall()]

    cur.execute(
        "SELECT id, usuario_id, noticia_id, tipo_acao, peso, timestamp FROM interacoes;"
    )
    i_cols = [d[0] for d in cur.description]
    interacoes = [dict(zip(i_cols, row)) for row in cur.fetchall()]

    return {"usuarios": usuarios, "noticias": noticias, "interacoes": interacoes}
