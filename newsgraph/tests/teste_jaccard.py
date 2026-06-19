
import unittest


# ===========================================================================
# jaccard()
# ===========================================================================

class TestJaccardPuro(unittest.TestCase):
    def setUp(self):
        from core.jaccard import jaccard
        self.J = jaccard

    def test_conjuntos_iguais_retorna_1(self):
        self.assertAlmostEqual(self.J({1: 4, 2: 1}, {1: 4, 2: 1}), 1.0)

    def test_conjuntos_disjuntos_retorna_0(self):
        self.assertAlmostEqual(self.J({1: 4}, {2: 1}), 0.0)

    def test_sobreposicao_parcial(self):
        resultado = self.J({1: 4, 2: 1}, {1: 2})
        self.assertAlmostEqual(resultado, 0.4)

    def test_ambos_vazios_retorna_0(self):
        """Sem leitores dos dois lados → J = 0.0 (sem divisão por zero)."""
        self.assertAlmostEqual(self.J({}, {}), 0.0)

    def test_um_vazio_retorna_0(self):
        """Um dos lados sem leitores → J = 0.0."""
        self.assertAlmostEqual(self.J({1: 5}, {}), 0.0)
        self.assertAlmostEqual(self.J({}, {1: 5}), 0.0)

    def test_simetria(self):
        a = {1: 4, 2: 1, 3: 5}
        b = {2: 3, 3: 5, 4: 1}
        self.assertAlmostEqual(self.J(a, b), self.J(b, a))

    def test_resultado_entre_0_e_1(self):
        casos = [
            ({1: 1}, {1: 100}),
            ({1: 4, 2: 4, 3: 4}, {1: 1}),
            ({1: 5, 2: 5}, {2: 5, 3: 5}),
        ]
        for a, b in casos:
            r = self.J(a, b)
            self.assertGreaterEqual(r, 0.0, msg=f"J({a},{b}) = {r} < 0")
            self.assertLessEqual(r, 1.0,    msg=f"J({a},{b}) = {r} > 1")

    def test_pesos_iguais_equivale_ao_jaccard_classico(self):
        a = {1: 1, 2: 1, 3: 1}
        b = {2: 1, 3: 1, 4: 1}
        # |interseção| = 2, |união| = 4 → J = 0.5
        self.assertAlmostEqual(self.J(a, b), 0.5)

    def test_peso_maior_eleva_similaridade(self):
        base_a  = {1: 1, 2: 1}
        base_b  = {1: 1}
        forte_a = {1: 10, 2: 1}
        forte_b = {1: 10}
        j_base  = self.J(base_a, base_b)
        j_forte = self.J(forte_a, forte_b)
        # min/max com peso 10 → 10/11; com peso 1 → 1/2
        self.assertGreater(j_forte, j_base)

    def test_tipo_retorno_e_float(self):
        resultado = self.J({1: 4}, {1: 4})
        self.assertIsInstance(resultado, float)


class TestGrafoBipartido(unittest.TestCase):

    def _bipartido_simples(self):
        from core.grafo_bipartido import GrafoBipartido
        usuarios   = [{"id": 1}, {"id": 2}]
        noticias   = [{"id": 10}, {"id": 20}, {"id": 30}]
        interacoes = [
            {"usuario_id": 1, "noticia_id": 10, "peso": 4},
            {"usuario_id": 2, "noticia_id": 10, "peso": 1},
            {"usuario_id": 1, "noticia_id": 20, "peso": 5},
            {"usuario_id": 2, "noticia_id": 30, "peso": -3},  # dislike
        ]
        return GrafoBipartido.construir(usuarios, noticias, interacoes)

    def test_contagem_de_vertices(self):
        g = self._bipartido_simples()
        self.assertEqual(g.num_usuarios(), 2)
        self.assertEqual(g.num_noticias(), 3)

    def test_leitores_de_noticia_com_interacoes(self):
        """Notícia 10 foi lida por usuários 1 (peso 4) e 2 (peso 1)."""
        g = self._bipartido_simples()
        leitores = g.leitores_de(10)
        self.assertEqual(leitores, {1: 4.0, 2: 1.0})

    def test_leitores_de_noticia_sem_interacoes(self):
        """Notícia que ninguém leu retorna dict vazio."""
        from core.grafo_bipartido import GrafoBipartido
        g = GrafoBipartido.construir(
            [{"id": 1}], [{"id": 99}], []
        )
        self.assertEqual(g.leitores_de(99), {})

    def test_dislike_nao_entra_em_leitores(self):
        g = self._bipartido_simples()
        leitores_30 = g.leitores_de(30)
        self.assertNotIn(2, leitores_30)
        self.assertEqual(leitores_30, {})

    def test_dislike_registrado_em_dislikes(self):
        g = self._bipartido_simples()
        self.assertIn(30, g.dislikes_de(2))

    def test_leituras_de_usuario(self):
        g = self._bipartido_simples()
        leituras = g.leituras_de(1)
        self.assertEqual(leituras, {10: 4.0, 20: 5.0})

    def test_usuario_sem_leituras(self):
        from core.grafo_bipartido import GrafoBipartido
        g = GrafoBipartido.construir([{"id": 99}], [], [])
        self.assertEqual(g.leituras_de(99), {})

    def test_num_interacoes_positivas_exclui_dislikes(self):
        g = self._bipartido_simples()
        # interações positivas: (1→10), (2→10), (1→20) = 3
        self.assertEqual(g.num_interacoes_positivas(), 3)

    def test_leitores_retorna_copia(self):
        g = self._bipartido_simples()
        leitores = g.leitores_de(10)
        leitores[999] = 999.0  # muta a cópia
        self.assertNotIn(999, g.leitores_de(10))

class TestProjecao(unittest.TestCase):

    def _bipartido_e_projecao(self, interacoes, limiar=0.0):
        from core.grafo_bipartido import GrafoBipartido
        from core.projecao import projetar
        usuarios = [{"id": uid} for uid in {i["usuario_id"] for i in interacoes}]
        nids     = {i["noticia_id"] for i in interacoes}
        noticias = [{"id": nid} for nid in nids]
        bp = GrafoBipartido.construir(usuarios, noticias, interacoes)
        return projetar(bp, limiar_jaccard=limiar), bp

    def test_sem_leitores_compartilhados_sem_arestas(self):
        interacoes = [
            {"usuario_id": 1, "noticia_id": 10, "peso": 4},
            {"usuario_id": 2, "noticia_id": 20, "peso": 4},
        ]
        g, _ = self._bipartido_e_projecao(interacoes)
        self.assertEqual(g.num_arestas(), 0)

    def test_leitores_compartilhados_geram_aresta(self):
        interacoes = [
            {"usuario_id": 1, "noticia_id": 10, "peso": 4},
            {"usuario_id": 1, "noticia_id": 20, "peso": 4},
        ]
        g, _ = self._bipartido_e_projecao(interacoes)
        self.assertEqual(g.num_arestas(), 1)
        self.assertTrue(g.tem_aresta(10, 20))

    def test_pesos_iguais_geram_jaccard_1(self):
        interacoes = [
            {"usuario_id": 1, "noticia_id": 10, "peso": 5},
            {"usuario_id": 1, "noticia_id": 20, "peso": 5},
        ]
        g, _ = self._bipartido_e_projecao(interacoes)
        self.assertAlmostEqual(g.peso(10, 20), 1.0)

    def test_dislike_nao_contribui_para_jaccard(self):
        interacoes = [
            {"usuario_id": 1, "noticia_id": 10, "peso": 4},
            {"usuario_id": 1, "noticia_id": 20, "peso": -3},  # dislike em 20
        ]
        g, _ = self._bipartido_e_projecao(interacoes)
        self.assertEqual(g.num_arestas(), 0)

    def test_todas_noticias_sao_vertices(self):
        from core.grafo_bipartido import GrafoBipartido
        from core.projecao import projetar
        bp = GrafoBipartido.construir(
            [{"id": 1}],
            [{"id": 10}, {"id": 20}, {"id": 30}],
            [{"usuario_id": 1, "noticia_id": 10, "peso": 4}],
        )
        g = projetar(bp)
        for nid in [10, 20, 30]:
            self.assertIn(nid, g.vertices())

    def test_limiar_filtra_arestas_fracas(self):
        # Usuário 1 leu 10 (peso 4) e 20 (peso 1); usuário 2 só leu 10
        # J(10,20): só usuário 1 em comum; min(4,1)/max(4,1) = 1/4 = 0.25
        interacoes = [
            {"usuario_id": 1, "noticia_id": 10, "peso": 4},
            {"usuario_id": 2, "noticia_id": 10, "peso": 1},
            {"usuario_id": 1, "noticia_id": 20, "peso": 1},
        ]
        g_sem_limiar, _ = self._bipartido_e_projecao(interacoes, limiar=0.0)
        g_com_limiar, _ = self._bipartido_e_projecao(interacoes, limiar=0.5)

        self.assertGreater(g_sem_limiar.num_arestas(), 0)
        self.assertEqual(g_com_limiar.num_arestas(), 0)

    def test_grafo_resultante_e_nao_direcionado(self):
        interacoes = [
            {"usuario_id": 1, "noticia_id": 10, "peso": 4},
            {"usuario_id": 1, "noticia_id": 20, "peso": 4},
        ]
        g, _ = self._bipartido_e_projecao(interacoes)
        self.assertTrue(g.tem_aresta(10, 20))
        self.assertTrue(g.tem_aresta(20, 10))

    def test_integracao_com_jaccard_calculo_correto(self):
        interacoes = [
            {"usuario_id": 1, "noticia_id": 10, "peso": 4},
            {"usuario_id": 2, "noticia_id": 10, "peso": 1},
            {"usuario_id": 1, "noticia_id": 20, "peso": 2},
        ]
        g, _ = self._bipartido_e_projecao(interacoes)
        self.assertAlmostEqual(g.peso(10, 20), 0.4, places=6)


if __name__ == "__main__":
    unittest.main(verbosity=2)