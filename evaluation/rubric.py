# -*- coding: utf-8 -*-
"""Rubrique d'évaluation — définie AVANT toute mesure (§ 7.1).

Choix méthodologiques imposés par le sujet et assumés ici :

* SIX critères : pertinence, exactitude (absence d'hallucination), respect du
  ton, respect de la LANGUE, respect du format, longueur. On substitue cette
  grille à celle du Choix 1 (pertinence, cohérence, originalité, contrôlabilité)
  car « originalité » est contre-productive pour une communication
  professionnelle (on ne veut pas d'un email « original » mais juste et sobre).
  Cette substitution est justifiée dans le rapport (§ 1.4).

* TROIS ancrages (5 / 3 / 1) plutôt qu'une échelle continue : le 4 est la note
  qu'on met quand on n'a pas envie de trancher. Trois ancrages forcent une
  décision défendable devant quelqu'un qui n'est pas d'accord.

* EXACTITUDE PRIORITAIRE : un fait inventé impose 1 quelles que soient les
  autres notes (un email parfaitement tourné avec un montant faux est plus
  dangereux qu'un email médiocre). Cette règle est appliquée dans le harnais.
"""

from __future__ import annotations

# Critères et ancrages. Chaque critère décrit explicitement ce que vaut 5/3/1.
CRITERIA = {
    "pertinence": {
        "libelle": "Pertinence",
        "5": "Répond exactement à l'objectif, ton et contenu adaptés au destinataire, directement envoyable.",
        "3": "Répond globalement mais avec un hors-sujet mineur, une maladresse ou un passage à retoucher.",
        "1": "Hors-sujet, inadapté au destinataire, ou inutilisable en l'état.",
    },
    "exactitude": {
        "libelle": "Exactitude / absence d'hallucination",
        "5": "Aucun fait, montant, date ou engagement non fourni ; les manques sont signalés, pas inventés.",
        "3": "Pas d'invention factuelle nette, mais une implicature risquée (« comme convenu » sans accord fourni).",
        "1": "Au moins un fait, montant, date, cause ou engagement inventé. NOTE PLAFONNÉE : impose 1 au global.",
    },
    "ton": {
        "libelle": "Respect du ton",
        "5": "Ton demandé tenu de bout en bout, registre freelance/TPE, aucune tournure corporate.",
        "3": "Ton globalement respecté mais une rupture (trop familier, trop pompeux) ou un cliché corporate.",
        "1": "Ton opposé à la demande, ou registre corporate marqué.",
    },
    "langue": {
        "libelle": "Respect de la langue",
        "5": "Sortie entièrement dans la langue demandée, conventions de politesse correctes.",
        "3": "Langue demandée mais quelques mots étrangers résiduels ou calques maladroits.",
        "1": "Sortie dans la mauvaise langue, ou mélange marqué de deux langues.",
    },
    "format": {
        "libelle": "Respect du format",
        "5": "Tous les champs requis présents et non vides (objet/corps selon le mode), structure propre.",
        "3": "Champs présents mais un défaut de structure (objet absent là où il est attendu, corps mal découpé).",
        "1": "Format inexploitable : champ requis manquant/vide, ou sortie non structurée.",
    },
    "longueur": {
        "libelle": "Longueur",
        "5": "Dans la fourchette de mots demandée, sans remplissage ni coupe brutale.",
        "3": "Légèrement hors fourchette (±30 %), mais lisible.",
        "1": "Très en dehors de la fourchette (trop court pour être utile, ou délayé).",
    },
}

# Ordre canonique des critères (pour les tableaux et CSV).
CRITERIA_ORDER = ["pertinence", "exactitude", "ton", "langue", "format", "longueur"]

# Le critère d'exactitude plafonne la note globale à 1 quand il vaut 1.
CRITERION_CAPS_GLOBAL = "exactitude"

VALID_SCORES = (1, 3, 5)
