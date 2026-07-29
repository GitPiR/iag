# -*- coding: utf-8 -*-
"""Tests des propriétés structurelles des prompts (§ 6, § 9)."""

import unittest

import config
from prompts import library


class TestProprietesPrompts(unittest.TestCase):
    def test_tous_les_modes_coeur_ont_garde_fous(self):
        for mode in config.CORE_MODES:
            for lang in config.LANGUES:
                p = library.build_prompt(mode, lang, "Texte.", {"ton": "neutre", "longueur": "moyen"})
                self.assertIn("GARDE-FOUS", p["system_instruction"], f"{mode}/{lang}")

    def test_delimiteurs_anti_injection_presents(self):
        p = library.build_prompt("reponse_avis", "fr", "Avis.", {"ton": "neutre"})
        self.assertIn("<donnees_utilisateur>", p["user_content"])
        self.assertIn("</donnees_utilisateur>", p["user_content"])

    def test_consigne_de_langue_presente_et_correcte(self):
        pf = library.build_prompt("email", "fr", "X", {"ton": "neutre"})
        pe = library.build_prompt("email", "en", "X", {"ton": "neutre"})
        self.assertIn("français", pf["system_instruction"])
        self.assertIn("English", pe["system_instruction"])
        # Rappel de langue en fin de message utilisateur (redondance délibérée).
        self.assertIn("Rappel", pf["user_content"])
        self.assertIn("Reminder", pe["user_content"])

    def test_contre_exemple_uniquement_pour_reponse_avis(self):
        avis = library.build_prompt("reponse_avis", "fr", "Avis.", {"ton": "neutre"})
        email = library.build_prompt("email", "fr", "X", {"ton": "neutre"})
        self.assertIn("CONTRE-EXEMPLE", avis["system_instruction"])
        self.assertNotIn("CONTRE-EXEMPLE", email["system_instruction"])

    def test_champ_infos_manquantes_dans_le_schema(self):
        for mode in config.CORE_MODES:
            p = library.build_prompt(mode, "fr", "X", {"ton": "neutre"})
            self.assertIn("infos_manquantes", p["response_schema"]["properties"])

    def test_pas_de_json_exemple_duplique_en_production(self):
        # En v5/production on s'appuie sur le schéma natif : la consigne ne doit
        # pas re-décrire une structure JSON à produire (piège § 5.3).
        p = library.build_prompt("email", "fr", "X", {"ton": "neutre"})
        self.assertNotIn('"corps": "..."', p["system_instruction"])

    def test_niveau_relance_influe_sur_le_prompt(self):
        douce = library.build_prompt("relance", "fr", "Facture", {"ton": "neutre", "niveau": "douce"})
        derniere = library.build_prompt("relance", "fr", "Facture", {"ton": "neutre", "niveau": "derniere_chance"})
        self.assertNotEqual(douce["system_instruction"], derniere["system_instruction"])
        self.assertIn("DERNIÈRE", derniere["system_instruction"])


if __name__ == "__main__":
    unittest.main()
