"""Smoke test do motor de recomendação (offline, sem banco).

Monta um conjunto sintético de usuários/notícias/interações e verifica que o
pipeline completo — bipartido → projeção (Jaccard) → Kruskal → DFS → Heap —
produz um Top-N coerente: exclui as lidas, respeita o dislike e ordena pelo
score de gargalo.
"""

import unittest

from recomendacao.motor import recomendar_de_dados


class TestMotorIntegracao(unittest.TestCase):
    def _dados(self):
        # 3 usuários, 5 notícias. U1 e U2 têm perfil parecido (leem 10 e 20);
        # isso cria coocorrência → projeção liga 10-20-30. U3 é de outro nicho.
        usuarios = [{"id": 1}, {"id": 2}, {"id": 3}]
        noticias = [{"id": n} for n in (10, 20, 30, 40, 50)]
        interacoes = [
            # U1 leu 10 (forte) e 20 (forte) → sementes do U1
            {"usuario_id": 1, "noticia_id": 10, "peso": 5},
            {"usuario_id": 1, "noticia_id": 20, "peso": 5},
            # U2 leu 10, 20 e 30 → cria a ponte 20-30 via coocorrência com U1/U2
            {"usuario_id": 2, "noticia_id": 10, "peso": 4},
            {"usuario_id": 2, "noticia_id": 20, "peso": 4},
            {"usuario_id": 2, "noticia_id": 30, "peso": 4},
            # U3 leu 40 e 50 (nicho separado) e deu dislike na 30
            {"usuario_id": 3, "noticia_id": 40, "peso": 5},
            {"usuario_id": 3, "noticia_id": 50, "peso": 5},
            {"usuario_id": 3, "noticia_id": 30, "peso": -3},
        ]
        return {"usuarios": usuarios, "noticias": noticias, "interacoes": interacoes}

    def test_recomenda_nao_lida_alcancavel(self):
        recs = recomendar_de_dados(self._dados(), usuario_id=1, top_n=10)
        ids = [r["noticia_id"] for r in recs]
        # U1 leu 10 e 20; a 30 é alcançável pela projeção (coocorrência via U2).
        self.assertIn(30, ids)

    def test_exclui_lidas_do_usuario(self):
        recs = recomendar_de_dados(self._dados(), usuario_id=1, top_n=10)
        ids = [r["noticia_id"] for r in recs]
        self.assertNotIn(10, ids)
        self.assertNotIn(20, ids)

    def test_nao_recomenda_nicho_desconexo(self):
        # 40 e 50 estão noutra componente; o U1 não deve alcançá-las.
        recs = recomendar_de_dados(self._dados(), usuario_id=1, top_n=10)
        ids = [r["noticia_id"] for r in recs]
        self.assertNotIn(40, ids)
        self.assertNotIn(50, ids)

    def test_cold_start_retorna_vazio(self):
        # Usuário sem nenhuma interação positiva → sem sementes → lista vazia
        # (o fallback de recência vive na camada que toca o banco).
        dados = self._dados()
        dados["interacoes"] = []
        recs = recomendar_de_dados(dados, usuario_id=1, top_n=10)
        self.assertEqual(recs, [])

    def test_ordenado_por_score_desc(self):
        recs = recomendar_de_dados(self._dados(), usuario_id=2, top_n=10)
        scores = [r["score"] for r in recs]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_dislike_nao_vira_semente(self):
        # U3 deu dislike na 30; a 30 não pode aparecer no feed dele.
        recs = recomendar_de_dados(self._dados(), usuario_id=3, top_n=10)
        ids = [r["noticia_id"] for r in recs]
        self.assertNotIn(30, ids)


if __name__ == "__main__":
    unittest.main(verbosity=2)
