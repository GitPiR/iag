# -*- coding: utf-8 -*-
"""Tests du journal des itérations (§ 6.5).

Le test central : v5 doit être LITTÉRALEMENT le prompt de production. Si
quelqu'un modifie le prompt sans mettre le journal à jour, ce test casse — ce
qui distingue un journal vérifiable d'un journal reconstitué après coup.
"""

import unittest

import config
from prompts import journal, library


class TestJournal(unittest.TestCase):
    def test_v5_egale_prompt_de_production(self):
        for mode in config.CORE_MODES:
            for lang in config.LANGUES:
                opts = {"ton": "neutre", "longueur": "moyen"}
                if mode == "relance":
                    opts["niveau"] = "ferme"
                prod = library.build_prompt(mode, lang, "Contenu de test.", opts)
                v5 = journal.build_version("v5_production", mode, lang, "Contenu de test.", opts)
                self.assertEqual(v5["system_instruction"], prod["system_instruction"], f"{mode}/{lang} system")
                self.assertEqual(v5["user_content"], prod["user_content"], f"{mode}/{lang} contenu")
                self.assertEqual(v5["response_schema"], prod["response_schema"], f"{mode}/{lang} schéma")

    def test_inclusion_stricte_des_paliers(self):
        # v2 ⊂ v3 ⊂ v4 (avant la bascule json->schéma en v5).
        self.assertTrue(journal._FEATURES_V2 <= journal._FEATURES_V3)
        self.assertTrue(journal._FEATURES_V3 <= journal._FEATURES_V4)

    def test_seul_v5_pose_des_delimiteurs(self):
        # Sans groupe témoin (paliers sans délimiteurs), la mesure anti-injection
        # ne mesurerait rien (§ 6.5, pt 2).
        for version in ("v1_naif", "v2_role", "v3_contraintes", "v4_fewshot_gardefous"):
            spec = journal.build_version(version, "reponse_avis", "fr", "Avis.", {"ton": "neutre"})
            self.assertNotIn("donnees_utilisateur", spec["user_content"], version)
        v5 = journal.build_version("v5_production", "reponse_avis", "fr", "Avis.", {"ton": "neutre"})
        self.assertIn("donnees_utilisateur", v5["user_content"])

    def test_seul_v5_utilise_le_schema_natif(self):
        for version in ("v1_naif", "v2_role", "v3_contraintes", "v4_fewshot_gardefous"):
            spec = journal.build_version(version, "email", "fr", "X", {"ton": "neutre"})
            self.assertIsNone(spec["response_schema"], version)
        v5 = journal.build_version("v5_production", "email", "fr", "X", {"ton": "neutre"})
        self.assertIsNotNone(v5["response_schema"])

    def test_v3_demande_le_json_dans_le_prompt(self):
        # Palier volontairement « mauvaise méthode » (§ 6.5, pt 3).
        spec = journal.build_version("v3_contraintes", "email", "fr", "X", {"ton": "neutre"})
        self.assertIn("JSON", spec["system_instruction"])
        # ... et v5 ne doit PLUS demander de JSON dans le prompt.
        v5 = journal.build_version("v5_production", "email", "fr", "X", {"ton": "neutre"})
        self.assertNotIn('"corps": "..."', v5["system_instruction"])

    def test_v1_est_un_prompt_naif_sans_consigne(self):
        spec = journal.build_version("v1_naif", "email", "fr", "Devis 100€", {"ton": "neutre"})
        self.assertEqual(spec["system_instruction"], "")

    def test_version_inconnue_leve(self):
        with self.assertRaises(ValueError):
            journal.build_version("v9", "email", "fr", "X", {})


if __name__ == "__main__":
    unittest.main()
