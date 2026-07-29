# -*- coding: utf-8 -*-
"""Configuration centrale de l'application.

Ce module ne dépend d'aucune bibliothèque externe : il doit pouvoir être
importé par les tests et le mode démo sans que le SDK Gemini ou la clé API
soient installés (cf. exigence § 5.5 du sujet).
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# MODÈLE
# ---------------------------------------------------------------------------
# Identifiant de modèle centralisé dans UNE seule constante (exigence § 5.2).
#
# ⚠️ À CONFIRMER dans Google AI Studio avant chaque campagne : les catalogues
# Gemini changent vite et des modèles sont réellement coupés (les familles 1.5
# et 2.0 renvoient désormais des 404). On n'utilise PAS l'alias
# `gemini-flash-latest`, hot-swappé par Google, donc non reproductible pour un
# protocole d'évaluation.
MODEL_ID = "gemini-3.5-flash"

# Modèle utilisé pour le juge d'évaluation. On le garde identique par défaut,
# tout en documentant que le juger avec un modèle de la MÊME famille est un
# biais de complaisance (cf. protocole d'évaluation § 7.3). Le rendre distinct
# ici est le seul point à changer pour utiliser un juge d'une autre famille.
JUDGE_MODEL_ID = "gemini-3.5-flash"

# ---------------------------------------------------------------------------
# CLÉ API
# ---------------------------------------------------------------------------
# Jamais de secret en dur (§ 5.5). La clé vient de l'environnement ou d'un
# fichier .env non commité, chargé paresseusement (voir llm.py).
API_KEY_ENV_VAR = "GEMINI_API_KEY"


def get_api_key() -> str | None:
    """Retourne la clé API depuis l'environnement, ou None si absente."""
    key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    return key or None


# ---------------------------------------------------------------------------
# TEMPÉRATURE — compromis assumé et rendu mesurable (§ 5.4)
# ---------------------------------------------------------------------------
# Doctrine classique attendue par le sujet : température basse pour la
# précision, plus haute pour la créativité. MAIS la documentation Gemini 3
# recommande de laisser temperature = 1.0 sur ces modèles à raisonnement
# interne (une valeur basse peut provoquer des boucles / dégrader la qualité).
#
# Position implémentée : on garde un réglage PAR MODE (pertinent, mesurable,
# attendu pédagogiquement) mais on le rend désactivable par un unique drapeau.
# Quand USE_PER_MODE_TEMPERATURE est False, la température n'est tout
# simplement PAS transmise à l'API (le modèle applique son défaut). On
# transforme ainsi un désaccord de doctrine en expérience mesurable.
USE_PER_MODE_TEMPERATURE = True

# Températures par mode. Précision -> bas ; créativité -> haut.
MODE_TEMPERATURE = {
    "email": 0.5,
    "relance": 0.3,          # précision : ne pas broder sur une créance
    "reponse_avis": 0.5,
    "post": 0.8,             # créativité (mode bonus)
    "reformuler": 0.3,       # précision (mode bonus)
}
DEFAULT_TEMPERATURE = 0.5


def temperature_for(mode: str) -> float | None:
    """Retourne la température à transmettre à l'API pour un mode donné.

    Renvoie None quand le réglage par mode est désactivé : l'appelant doit
    alors NE PAS transmettre le paramètre à l'API (et non transmettre 1.0),
    pour laisser le modèle appliquer son propre défaut.
    """
    if not USE_PER_MODE_TEMPERATURE:
        return None
    return MODE_TEMPERATURE.get(mode, DEFAULT_TEMPERATURE)


# ---------------------------------------------------------------------------
# SEED — réduit sans supprimer le non-déterminisme (§ 5.4)
# ---------------------------------------------------------------------------
# On fixe une seed pour le JUGE (où la stabilité prime) et on laisse la
# génération libre (le non-déterminisme y est un objet d'étude, cf. § 7.5).
JUDGE_SEED = 7

# ---------------------------------------------------------------------------
# LONGUEURS CIBLES PAR MODE (en mots) — utilisées par les contrôles
# déterministes de longueur (§ 7.4) et injectées dans les prompts.
# ---------------------------------------------------------------------------
LENGTH_RANGES = {
    "court": (40, 90),
    "moyen": (90, 180),
    "long": (180, 320),
}
DEFAULT_LENGTH = "moyen"

# ---------------------------------------------------------------------------
# ÉNUMÉRATIONS DE VALIDATION — servent à valider les entrées du formulaire
# (§ 4.8, § 8) et à générer des messages d'erreur explicites.
# ---------------------------------------------------------------------------
MODES = ("email", "relance", "reponse_avis", "post", "reformuler")
CORE_MODES = ("email", "relance", "reponse_avis")   # périmètre évalué
LANGUES = ("fr", "en")
TONS = ("neutre", "chaleureux", "formel", "direct")
NIVEAUX_RELANCE = ("douce", "ferme", "derniere_chance")
PLATEFORMES = ("linkedin", "instagram", "twitter", "facebook")

# ---------------------------------------------------------------------------
# CHEMINS
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
DEMO_FILE = os.path.join(BASE_DIR, "demo", "demo_outputs.json")
