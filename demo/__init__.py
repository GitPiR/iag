# -*- coding: utf-8 -*-
"""Mode démo hors-ligne (§ 4.4).

Rejoue des sorties pré-enregistrées SANS aucun appel API, pour que le
correcteur voie des résultats même sans clé, sans quota et sans dépendre d'un
modèle susceptible d'avoir été retiré du catalogue. Chaque sortie indique
honnêtement son origine (rédigée à la main, ou produite par l'API).
"""

from __future__ import annotations

import json
import os

import config

_CACHE: dict | None = None


def _load() -> dict:
    """Charge et met en cache le corpus de démo. Ne lève jamais vers l'UI."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    try:
        with open(config.DEMO_FILE, encoding="utf-8") as fh:
            _CACHE = json.load(fh)
    except (OSError, json.JSONDecodeError):
        _CACHE = {"entries": []}
    return _CACHE


def entries() -> list[dict]:
    """Retourne toutes les entrées de démo."""
    return _load().get("entries", [])


def get_demo_output(mode: str, lang: str, opts: dict | None = None) -> dict | None:
    """Retourne une sortie de démo correspondant au (mode, langue).

    Recherche du meilleur candidat : même mode + même langue d'abord, puis même
    mode toutes langues. Renvoie une copie enrichie de l'origine, ou None si
    aucune entrée ne correspond.
    """
    opts = opts or {}
    all_entries = entries()

    # 1) Correspondance mode + langue (+ éventuellement niveau/plateforme).
    best = None
    for e in all_entries:
        if e.get("mode") == mode and e.get("lang") == lang:
            # Priorité aux entrées dont le niveau de relance correspond.
            if mode == "relance":
                if e.get("opts", {}).get("niveau") == opts.get("niveau"):
                    return _pack(e)
                if best is None:
                    best = e
            else:
                return _pack(e)
    if best is not None:
        return _pack(best)

    # 2) Repli : même mode, n'importe quelle langue.
    for e in all_entries:
        if e.get("mode") == mode:
            return _pack(e)
    return None


def _pack(entry: dict) -> dict:
    """Emballe une entrée de démo dans un format homogène pour l'UI."""
    return {
        "data": entry.get("output", {}),
        "origin": entry.get("origin", "manuelle"),
        "input": entry.get("input", ""),
        "opts": entry.get("opts", {}),
    }
