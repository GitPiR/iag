# -*- coding: utf-8 -*-
"""Tests de validation des entrées du formulaire (§ 4.8)."""

import unittest

import service


class TestValidation(unittest.TestCase):
    def test_entree_valide(self):
        ok, msg = service.validate_inputs("email", "fr", "Envoyer le devis.", {"ton": "neutre", "longueur": "moyen"})
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_saisie_vide_refusee(self):
        ok, msg = service.validate_inputs("email", "fr", "   ", {})
        self.assertFalse(ok)
        self.assertIn("saisir", msg.lower())

    def test_saisie_trop_courte(self):
        ok, msg = service.validate_inputs("email", "fr", "ok", {})
        self.assertFalse(ok)

    def test_mode_invalide(self):
        ok, msg = service.validate_inputs("inconnu", "fr", "texte suffisant", {})
        self.assertFalse(ok)
        self.assertIn("Mode", msg)

    def test_langue_invalide(self):
        ok, msg = service.validate_inputs("email", "de", "texte suffisant", {})
        self.assertFalse(ok)

    def test_niveau_relance_invalide(self):
        ok, msg = service.validate_inputs(
            "relance", "fr", "Facture impayée", {"ton": "neutre", "longueur": "court", "niveau": "brutale"}
        )
        self.assertFalse(ok)
        self.assertIn("Niveau", msg)

    def test_plateforme_invalide(self):
        ok, msg = service.validate_inputs(
            "post", "fr", "Annonce", {"ton": "neutre", "longueur": "court", "plateforme": "myspace"}
        )
        self.assertFalse(ok)
        self.assertIn("Plateforme", msg)

    def test_ton_invalide(self):
        ok, msg = service.validate_inputs("email", "fr", "texte suffisant", {"ton": "sarcastique"})
        self.assertFalse(ok)

    def test_generate_message_sur_entree_invalide_ne_leve_pas(self):
        # Même invalide, generate_message renvoie un LLMResult + un prompt.
        result, prompt = service.generate_message("email", "fr", "", {})
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "INVALID_INPUT")
        self.assertIn("system_instruction", prompt)


if __name__ == "__main__":
    unittest.main()
