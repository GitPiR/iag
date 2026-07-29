# -*- coding: utf-8 -*-
"""Schémas de sortie structurée native (§ 5.3).

Décrits en dictionnaires Python (et non en modèles Pydantic) : aucune
dépendance supplémentaire, et cela évite un bug connu du SDK sur les modèles
Pydantic imbriqués (`$defs`).

Le champ `infos_manquantes` matérialise le garde-fou principal (§ 6.3) : au
lieu d'inventer un fait absent, le modèle le déclare ici. Un garde-fou qui
n'est pas mesurable n'est qu'une intention ; ce champ le rend comptable par le
harnais, affichable dans l'UI et corrigible par l'utilisateur.

Le type est donné en MAJUSCULES (STRING, ARRAY, OBJECT...) conformément à
l'énumération OpenAPI attendue par l'API Gemini. `propertyOrdering` fixe
l'ordre des champs pour une sortie stable d'un tirage à l'autre.
"""

from __future__ import annotations

# Champ commun : liste des informations que le modèle aurait dû inventer et
# qu'il signale au lieu de fabriquer.
_INFOS_MANQUANTES = {
    "type": "ARRAY",
    "items": {"type": "STRING"},
    "description": (
        "Informations nécessaires mais absentes de la saisie, à réclamer à "
        "l'utilisateur au lieu de les inventer. Liste vide si tout est fourni."
    ),
}

# email / relance : objet + corps.
SCHEMA_EMAIL = {
    "type": "OBJECT",
    "properties": {
        "objet": {"type": "STRING", "description": "Ligne d'objet de l'email."},
        "corps": {"type": "STRING", "description": "Corps complet de l'email."},
        "infos_manquantes": _INFOS_MANQUANTES,
    },
    "required": ["objet", "corps", "infos_manquantes"],
    "propertyOrdering": ["objet", "corps", "infos_manquantes"],
}

SCHEMA_RELANCE = SCHEMA_EMAIL  # même structure (objet + corps)

# reponse_avis : pas d'objet (c'est une réponse publique/directe), un corps.
SCHEMA_REPONSE_AVIS = {
    "type": "OBJECT",
    "properties": {
        "corps": {"type": "STRING", "description": "Réponse adressée au client."},
        "infos_manquantes": _INFOS_MANQUANTES,
    },
    "required": ["corps", "infos_manquantes"],
    "propertyOrdering": ["corps", "infos_manquantes"],
}

# post (bonus) : texte + hashtags.
SCHEMA_POST = {
    "type": "OBJECT",
    "properties": {
        "corps": {"type": "STRING", "description": "Texte du post."},
        "hashtags": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Hashtags pertinents, sans le caractère #.",
        },
        "infos_manquantes": _INFOS_MANQUANTES,
    },
    "required": ["corps", "infos_manquantes"],
    "propertyOrdering": ["corps", "hashtags", "infos_manquantes"],
}

# reformuler (bonus) : texte reformulé.
SCHEMA_REFORMULER = {
    "type": "OBJECT",
    "properties": {
        "corps": {"type": "STRING", "description": "Texte reformulé."},
        "infos_manquantes": _INFOS_MANQUANTES,
    },
    "required": ["corps", "infos_manquantes"],
    "propertyOrdering": ["corps", "infos_manquantes"],
}

SCHEMAS = {
    "email": SCHEMA_EMAIL,
    "relance": SCHEMA_RELANCE,
    "reponse_avis": SCHEMA_REPONSE_AVIS,
    "post": SCHEMA_POST,
    "reformuler": SCHEMA_REFORMULER,
}


def schema_for(mode: str) -> dict:
    """Retourne le schéma de sortie natif pour un mode, ou celui d'email."""
    return SCHEMAS.get(mode, SCHEMA_EMAIL)
