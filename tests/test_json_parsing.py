# -*- coding: utf-8 -*-
"""Tests du parsing JSON défensif (§ 5.3)."""

import unittest

import llm


class TestJsonParsing(unittest.TestCase):
    def test_json_propre(self):
        self.assertEqual(llm.parse_json_defensive('{"a": 1}'), {"a": 1})

    def test_json_avec_cloture_markdown(self):
        text = '```json\n{"corps": "salut"}\n```'
        self.assertEqual(llm.parse_json_defensive(text), {"corps": "salut"})

    def test_json_entoure_de_prose(self):
        text = 'Voici la réponse : {"corps": "ok"} — merci.'
        self.assertEqual(llm.parse_json_defensive(text), {"corps": "ok"})

    def test_accolades_dans_chaines_ignorees(self):
        text = '{"corps": "prix {remise} à confirmer", "n": 2}'
        self.assertEqual(
            llm.parse_json_defensive(text),
            {"corps": "prix {remise} à confirmer", "n": 2},
        )

    def test_troncature_renvoie_none(self):
        # Objet non refermé (réponse tronquée) : échec propre, pas d'exception.
        self.assertIsNone(llm.parse_json_defensive('{"corps": "incomp'))

    def test_texte_non_json_renvoie_none(self):
        self.assertIsNone(llm.parse_json_defensive("Bonjour, ceci est du texte."))

    def test_chaine_vide_renvoie_none(self):
        self.assertIsNone(llm.parse_json_defensive(""))

    def test_tableau_json_rejete(self):
        # On attend un objet, pas un tableau.
        self.assertIsNone(llm.parse_json_defensive("[1, 2, 3]"))


class TestGenerateSansCle(unittest.TestCase):
    """generate ne doit jamais lever, même sans clé (renvoie un LLMResult)."""

    def test_pas_de_cle_renvoie_erreur_propre(self):
        import os
        old = os.environ.pop("GEMINI_API_KEY", None)
        try:
            res = llm.generate("sys", "contenu")
            self.assertFalse(res.ok)
            self.assertEqual(res.error_code, "NO_KEY")
            self.assertIsInstance(res.error, str)
        finally:
            if old is not None:
                os.environ["GEMINI_API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
