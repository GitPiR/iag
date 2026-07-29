# -*- coding: utf-8 -*-
"""Harnais d'évaluation, testable sans lancer Streamlit (§ 9).

Sous-modules :
- rubric        : rubrique 5/3/1 définie avant les mesures.
- deterministic : contrôles objectifs sans appel API (langue, longueur, format, injection).
- testcases     : jeu de tests FR/EN avec cas difficiles et injections.
- judge         : juge LLM séparé, biais nommé.
- harness       : campagne d'évaluation (variance, artefacts, détection d'échecs).
- replay_journal: rejeu automatique des cinq paliers de prompt.
"""
