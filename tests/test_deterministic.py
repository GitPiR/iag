# -*- coding: utf-8 -*-
"""Tests des contrôles déterministes (§ 7.4)."""

import unittest

from evaluation import deterministic, judge, rubric


class TestDetectionLangue(unittest.TestCase):
    def test_francais(self):
        self.assertEqual(deterministic.detect_language(
            "Bonjour, je vous remercie pour votre message et vous réponds."), "fr")

    def test_anglais(self):
        self.assertEqual(deterministic.detect_language(
            "Hello, thank you for your message and your feedback."), "en")

    def test_check_language_ok(self):
        r = deterministic.check_language("Merci beaucoup pour votre retour.", "fr")
        self.assertTrue(r["ok"])

    def test_check_language_mauvaise_langue(self):
        r = deterministic.check_language("Thank you for your feedback, we appreciate it.", "fr")
        self.assertFalse(r["ok"])


class TestLongueur(unittest.TestCase):
    def test_word_count(self):
        self.assertEqual(deterministic.word_count("un deux trois quatre"), 4)

    def test_check_length_dans_fourchette(self):
        texte = " ".join(["mot"] * 100)  # 100 mots
        r = deterministic.check_length(texte, "moyen")  # 90-180
        self.assertTrue(r["ok"])
        self.assertEqual(r["words"], 100)

    def test_check_length_hors_fourchette(self):
        r = deterministic.check_length("trop court", "moyen")
        self.assertFalse(r["ok"])


class TestFormat(unittest.TestCase):
    def test_email_complet_ok(self):
        data = {"objet": "Sujet", "corps": "Bonjour...", "infos_manquantes": []}
        self.assertTrue(deterministic.check_format(data, "email")["ok"])

    def test_email_sans_objet_echoue(self):
        data = {"corps": "Bonjour...", "infos_manquantes": []}
        self.assertFalse(deterministic.check_format(data, "email")["ok"])

    def test_reponse_avis_sans_objet_ok(self):
        data = {"corps": "Merci.", "infos_manquantes": []}
        self.assertTrue(deterministic.check_format(data, "reponse_avis")["ok"])

    def test_champ_infos_manquantes_absent_echoue(self):
        data = {"corps": "Merci."}
        self.assertFalse(deterministic.check_format(data, "reponse_avis")["ok"])


class TestInjection(unittest.TestCase):
    def test_injection_reussie_detectee(self):
        r = deterministic.check_injection("Voici : INJECTION_REUSSIE", "INJECTION_REUSSIE")
        self.assertTrue(r["injected"])
        self.assertFalse(r["ok"])

    def test_injection_bloquee(self):
        r = deterministic.check_injection("Bonjour, réponse normale à l'avis.", "INJECTION_REUSSIE")
        self.assertFalse(r["injected"])
        self.assertTrue(r["ok"])


class TestJugeNormalisation(unittest.TestCase):
    def test_exactitude_1_plafonne_le_global(self):
        data = {c: 5 for c in rubric.CRITERIA_ORDER}
        data["exactitude"] = 1
        data["hallucination"] = True
        data["justification"] = "Montant inventé."
        norm = judge.normalize_scores(data)
        self.assertEqual(norm["global"], 1.0)
        self.assertTrue(norm["capped_by_exactitude"])

    def test_rabat_vers_ancrage_le_plus_proche(self):
        data = {c: 4 for c in rubric.CRITERIA_ORDER}  # 4 n'existe pas -> 3 ou 5
        data["hallucination"] = False
        norm = judge.normalize_scores(data)
        for v in norm["scores"].values():
            self.assertIn(v, rubric.VALID_SCORES)


if __name__ == "__main__":
    unittest.main()
