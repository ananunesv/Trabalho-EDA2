"""Testes unitários para pipeline.filtro_escopo (Issue #3).

Estratégia: mockar o spaCy para que os testes rodem rápido (sem carregar
o modelo de 50 MB) e sem dependência de rede. Cada teste cria um doc falso
que simula a saída relevante do spaCy (lemas e entidades).

Rodar:  PYTHONPATH=. python -m tests.test_filtro_escopo
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers para criar docs spaCy falsos
# ---------------------------------------------------------------------------

def _make_token(lemma: str, is_stop=False, is_punct=False, is_space=False):
    tok = MagicMock()
    tok.lemma_ = lemma
    tok.is_stop  = is_stop
    tok.is_punct = is_punct
    tok.is_space = is_space
    return tok


def _make_ent(text: str, label: str):
    ent = MagicMock()
    ent.text   = text
    ent.label_ = label
    return ent


def _make_doc(tokens=None, ents=None):
    """Cria um documento spaCy falso com tokens e entidades predefinidos."""
    doc = MagicMock()
    doc.__iter__ = MagicMock(return_value=iter(tokens or []))
    doc.ents     = ents or []
    return doc


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

class TestScoreEconomico(unittest.TestCase):

    def _run_com_doc(self, doc_mock, texto=""):
        """Aplica score_economico injetando o doc mockado no spaCy."""
        # Importa aqui dentro para que o patch já esteja ativo
        from pipeline.filtro_escopo import score_economico as _score

        nlp_mock = MagicMock(return_value=doc_mock)
        with patch("pipeline.filtro_escopo._get_nlp", return_value=nlp_mock):
            return _score(texto, "")

    def test_sem_termos_economicos_retorna_zero(self):
        """Texto de esportes sem termos financeiros → score 0."""
        doc = _make_doc(
            tokens=[
                _make_token("brasil"),
                _make_token("vencer"),
                _make_token("copa"),
            ],
            ents=[],
        )
        score = self._run_com_doc(doc, "Brasil vence Copa América")
        self.assertEqual(score, 0)

    def test_lema_do_lexico_e_contado(self):
        """Lema 'selic' presente no léxico deve contar +1."""
        doc = _make_doc(
            tokens=[
                _make_token("selic"),   # presente no léxico
                _make_token("manter"),
            ],
            ents=[],
        )
        score = self._run_com_doc(doc, "Copom mantém Selic")
        self.assertGreaterEqual(score, 1)

    def test_entidade_financeira_conta(self):
        """Entidade do tipo MONEY contabilizada mesmo sem lema no léxico."""
        doc = _make_doc(
            tokens=[_make_token("anunciar")],
            ents=[_make_ent("R$ 3,50", "MONEY")],
        )
        score = self._run_com_doc(doc, "Empresa anuncia R$ 3,50 por ação")
        self.assertGreaterEqual(score, 1)

    def test_stopwords_ignoradas(self):
        """Stopwords não devem entrar na contagem mesmo se presente no léxico."""
        doc = _make_doc(
            tokens=[
                _make_token("de", is_stop=True),
                _make_token(".", is_punct=True),
                _make_token("selic"),   # termo econômico, não stopword
            ],
            ents=[],
        )
        score = self._run_com_doc(doc, "meta de selic")
        self.assertGreaterEqual(score, 1)  # "selic" é do léxico

    def test_lemas_duplicados_contam_uma_vez(self):
        """Mesmo lema repetido no texto conta apenas 1 (usa set)."""
        doc = _make_doc(
            tokens=[
                _make_token("selic"),
                _make_token("selic"),  # duplicado
                _make_token("selic"),
            ],
            ents=[],
        )
        score = self._run_com_doc(doc, "Selic Selic Selic")
        self.assertEqual(score, 1)  # set → apenas 1 único lema

    def test_multiplos_sinais_acumulam(self):
        """Notícia com múltiplos termos deve ter score alto."""
        doc = _make_doc(
            tokens=[
                _make_token("selic"),
                _make_token("juro"),
                _make_token("inflação"),
                _make_token("bolsa"),
            ],
            ents=[_make_ent("Petrobras", "ORG"), _make_ent("R$ 1 bi", "MONEY")],
        )
        score = self._run_com_doc(doc, "Selic, juros, inflação e bolsa")
        self.assertGreaterEqual(score, 4)


class TestEmEscopo(unittest.TestCase):

    def _patch_score(self, valor: int):
        """Retorna um context manager que fixa score_economico em `valor`."""
        return patch("pipeline.filtro_escopo.score_economico", return_value=valor)

    def test_score_zero_fora_de_escopo(self):
        from pipeline.filtro_escopo import em_escopo
        with self._patch_score(0):
            self.assertFalse(em_escopo("", "", limiar=2))

    def test_score_um_fora_de_escopo(self):
        from pipeline.filtro_escopo import em_escopo
        with self._patch_score(1):
            self.assertFalse(em_escopo("", "", limiar=2))

    def test_score_igual_ao_limiar_dentro_de_escopo(self):
        from pipeline.filtro_escopo import em_escopo
        with self._patch_score(2):
            self.assertTrue(em_escopo("", "", limiar=2))

    def test_score_acima_do_limiar_dentro_de_escopo(self):
        from pipeline.filtro_escopo import em_escopo
        with self._patch_score(10):
            self.assertTrue(em_escopo("", "", limiar=2))

    def test_limiar_customizado_e_respeitado(self):
        from pipeline.filtro_escopo import em_escopo
        with self._patch_score(3):
            self.assertFalse(em_escopo("", "", limiar=5))
            self.assertTrue(em_escopo("", "", limiar=3))


class TestProcessarItemIntegrado(unittest.TestCase):
    """Testa que processar_item do processador_nlp.py inclui os campos novos."""

    def test_campos_score_e_em_escopo_presentes(self):
        """processar_item deve sempre adicionar score_economico e em_escopo."""
        doc_vazio = _make_doc(tokens=[], ents=[])
        nlp_mock  = MagicMock(return_value=doc_vazio)

        with patch("pipeline.filtro_escopo._get_nlp", return_value=nlp_mock), \
             patch("pipeline.processador_nlp._carregar_nlp", return_value=nlp_mock):
            from pipeline.processador_nlp import processar_item
            item = {"titulo": "Notícia qualquer", "resumo": "Texto qualquer."}
            resultado = processar_item(item)

        self.assertIn("score_economico", resultado)
        self.assertIn("em_escopo", resultado)
        self.assertIsInstance(resultado["score_economico"], int)
        self.assertIsInstance(resultado["em_escopo"], bool)

    def test_noticia_fora_de_escopo_marcada_corretamente(self):
        """Notícia sem termos financeiros deve ter em_escopo=False."""
        doc_esporte = _make_doc(
            tokens=[_make_token("gol"), _make_token("futebol")],
            ents=[],
        )
        nlp_mock = MagicMock(return_value=doc_esporte)

        with patch("pipeline.filtro_escopo._get_nlp", return_value=nlp_mock), \
             patch("pipeline.processador_nlp._carregar_nlp", return_value=nlp_mock):
            from pipeline.processador_nlp import processar_item
            item = {
                "titulo": "Brasil vence Argentina na Copa",
                "resumo": "Gol de Vinicius garante classificação.",
            }
            resultado = processar_item(item)

        self.assertEqual(resultado["score_economico"], 0)
        self.assertFalse(resultado["em_escopo"])


if __name__ == "__main__":
    unittest.main(verbosity=2)