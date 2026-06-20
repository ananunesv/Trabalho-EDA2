"""Constrói o grafo bipartido usuário↔notícia a partir das interações reais.

Contrato (Issue #2):
    construir_bipartido(cur) -> tuple[Grafo, set, set]

ATENÇÃO: Jaccard NÃO se aplica aqui. O bipartido só carrega pesos de interação.
Jaccard é exclusivo da projeção (Issue #4).
"""

from .grafo import Grafo
from . import repositorio

_PESOS: dict[str, int] = {
    "clique":        1,
    "like":          4,
    "compartilhar":  5,
    "dislike":      -3,
}


def construir_bipartido(cur) -> tuple[Grafo, set, set]:
    dados = repositorio.carregar_grafo_dados(cur)

    usuarios   = dados["usuarios"]
    noticias   = dados["noticias"]
    interacoes = dados["interacoes"]

    grafo = Grafo(direcionado=True)
    vertices_usuario: set[str] = set()
    vertices_noticia: set[str] = set()

    # 1. Registrar vértices
    for u in usuarios:
        vid = f"u:{u['id']}"
        grafo.adicionar_vertice(vid)
        vertices_usuario.add(vid)

    for n in noticias:
        vid = f"n:{n['id']}"
        grafo.adicionar_vertice(vid)
        vertices_noticia.add(vid)

    # 2. Acumular pesos por par (usuário, notícia)
    acumulado: dict[tuple[str, str], float] = {}

    for i in interacoes:
        v_u = f"u:{i['usuario_id']}"
        v_n = f"n:{i['noticia_id']}"
        tipo = i["tipo_acao"]

        incremento = _PESOS.get(tipo, 0)
        if incremento == 0:
            continue

        chave = (v_u, v_n)
        acumulado[chave] = acumulado.get(chave, 0.0) + incremento

    # 3. Inserir arestas com o peso final
    for (v_u, v_n), peso_total in acumulado.items():
        grafo.adicionar_aresta(v_u, v_n, peso=peso_total)

    return grafo, vertices_usuario, vertices_noticia 
