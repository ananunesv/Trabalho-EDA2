"""Testes da DFS (travessia da árvore + gargalo) — `core.busca`.

NÃO há detecção de comunidades aqui: a busca apenas navega a árvore geradora a
partir das sementes e pontua cada notícia não-lida pelo gargalo do caminho.
"""

import unittest

from core.grafo import Grafo
from core.busca import recomendar_por_dfs


def _arvore_sintetica():
    # (Semente N1) N1 --0.8-- N2 --0.5-- N3 --0.9-- N4 (Semente N4)
    #                          |
    #                        0.4
    #                          |
    #                          N5
    g = Grafo(direcionado=False)
    g.adicionar_aresta("N1", "N2", 0.8)
    g.adicionar_aresta("N2", "N3", 0.5)
    g.adicionar_aresta("N3", "N4", 0.9)
    g.adicionar_aresta("N2", "N5", 0.4)
    return g


class TestDFSGargalo(unittest.TestCase):
    def setUp(self):
        self.arvore = _arvore_sintetica()
        self.sementes = ["N1", "N4"]
        self.lidas = ["N1", "N4"]
        recs = recomendar_por_dfs(self.arvore, self.sementes, self.lidas)
        self.por_noticia = {r["noticia"]: r for r in recs}

    def test_score_gargalo_e_saltos(self):
        # N2: vizinha direta de N1 → gargalo 0.8, 1 salto.
        self.assertAlmostEqual(self.por_noticia["N2"]["score"], 0.8)
        self.assertEqual(self.por_noticia["N2"]["saltos"], 1)
        # N3: vizinha direta de N4 → gargalo 0.9, 1 salto (caminho mais curto vence).
        self.assertAlmostEqual(self.por_noticia["N3"]["score"], 0.9)
        self.assertEqual(self.por_noticia["N3"]["saltos"], 1)
        # N5: N1→N2→N5 → gargalo min(0.8, 0.4) = 0.4, 2 saltos.
        self.assertAlmostEqual(self.por_noticia["N5"]["score"], 0.4)
        self.assertEqual(self.por_noticia["N5"]["saltos"], 2)

    def test_lidas_sao_excluidas(self):
        self.assertNotIn("N1", self.por_noticia)
        self.assertNotIn("N4", self.por_noticia)

    def test_semente_fora_da_arvore_e_ignorada(self):
        # Semente inexistente não deve quebrar a busca.
        recs = recomendar_por_dfs(self.arvore, ["INEXISTENTE"], [])
        self.assertEqual(recs, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
