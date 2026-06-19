"""Camada de repositório — a única porta para o SQL.

Recebe um cursor (`cur`) já aberto e executa as operações. Quem chama controla
a transação (commit/rollback). O núcleo de grafos nunca toca nestas funções:
ele recebe os dados em memória de `carregar_grafo_dados`.

v2.1: salvar_noticia agora persiste score_economico e em_escopo (Issue #3).
      carregar_grafo_dados filtra WHERE em_escopo = TRUE.
"""


def salvar_noticia(cur, n):
    """Insere uma notícia. Dedup automático por `link` (ON CONFLICT DO NOTHING).

    Espera que o dict `n` já contenha os campos 'score_economico' e 'em_escopo',
    adicionados por pipeline.filtro_escopo via pipeline.processador_nlp.processar_item.

    Pode rodar a coleta quantas vezes quiser sem duplicar.
    """
    cur.execute(
        """
        INSERT INTO noticias
            (titulo, resumo, link, fonte, data_publicacao, score_economico, em_escopo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (link) DO NOTHING;
        """,
        (
            n["titulo"],
            n["resumo"],
            n["link"],
            n["fonte"],
            n["data_publicacao"],
            n.get("score_economico", 0),
            n.get("em_escopo", True),
        ),
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
    """Lista notícias em escopo para o feed (mais recentes primeiro)."""
    cur.execute(
        """
        SELECT id, titulo, resumo, link, fonte, data_publicacao, coletado_em,
               score_economico, em_escopo
        FROM   noticias
        WHERE  em_escopo = TRUE
        ORDER  BY coletado_em DESC, id DESC;
        """
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def carregar_grafo_dados(cur):
    """Devolve `usuarios`, `noticias` e `interacoes` em memória.

    Notícias fora do escopo financeiro (em_escopo = FALSE) são excluídas aqui:
    o núcleo de grafos opera apenas sobre dados limpos.
    É o que alimenta o núcleo de grafos — que nunca toca o banco.
    """
    cur.execute("SELECT id, nome, criado_em FROM usuarios;")
    u_cols = [d[0] for d in cur.description]
    usuarios = [dict(zip(u_cols, row)) for row in cur.fetchall()]

    # Filtra notícias fora do escopo financeiro (Issue #3)
    cur.execute(
        """
        SELECT id, titulo, resumo, link, fonte, data_publicacao, coletado_em,
               score_economico
        FROM   noticias
        WHERE  em_escopo = TRUE;
        """
    )
    n_cols = [d[0] for d in cur.description]
    noticias = [dict(zip(n_cols, row)) for row in cur.fetchall()]

    cur.execute(
        "SELECT id, usuario_id, noticia_id, tipo_acao, peso, timestamp FROM interacoes;"
    )
    i_cols = [d[0] for d in cur.description]
    interacoes = [dict(zip(i_cols, row)) for row in cur.fetchall()]

    return {"usuarios": usuarios, "noticias": noticias, "interacoes": interacoes}


def relatorio_escopo(cur):
    """Retorna métricas do filtro de escopo — usado em analise/metricas.py.

    Devolve um dict com:
      total        — total de notícias coletadas
      em_escopo    — quantas passaram no filtro
      fora_escopo  — quantas foram descartadas
      percentual   — % aproveitada (float)
      limiar_usado — valor de LIMIAR_ESCOPO em config.py (lido de cá para evitar import circular)
    """
    cur.execute("SELECT COUNT(*) FROM noticias;")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM noticias WHERE em_escopo = TRUE;")
    aprovadas = cur.fetchone()[0]

    fora = total - aprovadas
    pct = round(aprovadas / total * 100, 1) if total > 0 else 0.0

    # Importa só aqui para não criar dependência circular no módulo
    try:
        from config import LIMIAR_ESCOPO
    except ImportError:
        LIMIAR_ESCOPO = 2  # fallback se config ainda não tiver a constante

    return {
        "total": total,
        "em_escopo": aprovadas,
        "fora_escopo": fora,
        "percentual": pct,
        "limiar_usado": LIMIAR_ESCOPO,
    }