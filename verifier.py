# -*- coding: utf-8 -*-
"""Mode de vérification hors-ligne (§ 9).

Contrôle la COHÉRENCE du jeu de tests, des prompts et du corpus de démo SANS
aucun appel API. C'est ce qui permet de valider le harnais avant de dépenser du
quota, et de prouver que quelque chose fonctionne même sans clé.

Usage :
    python verifier.py
    python app.py --verifier   (raccourci équivalent)
"""

from __future__ import annotations

import sys

import config
import demo
from evaluation import testcases
from prompts import journal, library


def _check(label: str, condition: bool, detail: str = "") -> bool:
    mark = "✅" if condition else "❌"
    line = f"  {mark} {label}"
    if detail and not condition:
        line += f" — {detail}"
    print(line)
    return condition


def verify() -> bool:
    """Lance tous les contrôles hors-ligne. Renvoie True si tout passe."""
    ok = True
    print("Vérification hors-ligne du prototype (aucun appel API)\n")

    # 1) Prompts de production : propriétés structurelles sur les 3 modes cœur.
    print("Prompts de production (modes cœur) :")
    for mode in config.CORE_MODES:
        for lang in config.LANGUES:
            p = library.build_prompt(mode, lang, "Texte de test.", {"ton": "neutre", "longueur": "moyen"})
            si = p["system_instruction"]
            ok &= _check(f"{mode}/{lang} : délimiteurs anti-injection présents",
                         "donnees_utilisateur" in p["user_content"])
            ok &= _check(f"{mode}/{lang} : consigne de langue présente",
                         "LANGUE" in si)
            ok &= _check(f"{mode}/{lang} : garde-fous présents",
                         "GARDE-FOUS" in si)
            ok &= _check(f"{mode}/{lang} : schéma de sortie natif fourni",
                         p["response_schema"] is not None)
    # Le contre-exemple n'est requis que pour reponse_avis.
    for lang in config.LANGUES:
        p = library.build_prompt("reponse_avis", lang, "Avis test.", {"ton": "neutre"})
        ok &= _check(f"reponse_avis/{lang} : contre-exemple présent",
                     "CONTRE-EXEMPLE" in p["system_instruction"] or "COUNTER-EXAMPLE" in p["system_instruction"])

    # 2) Journal : v5 == prompt de production.
    print("\nJournal des itérations :")
    for mode in config.CORE_MODES:
        prod = library.build_prompt(mode, "fr", "X", {"ton": "neutre", "longueur": "moyen"})
        v5 = journal.build_version("v5_production", mode, "fr", "X", {"ton": "neutre", "longueur": "moyen"})
        ok &= _check(f"{mode} : v5.system == production",
                     v5["system_instruction"] == prod["system_instruction"])
        ok &= _check(f"{mode} : v5.contenu == production",
                     v5["user_content"] == prod["user_content"])
    # Inclusion des paliers : chaque jeu de features contient le précédent (hors json->schéma).
    ok &= _check("v2 ⊂ v3 ⊂ v4 (inclusion stricte des features)",
                 journal._FEATURES_V2 <= journal._FEATURES_V3 <= journal._FEATURES_V4)

    # 3) Jeu de tests : validité et couverture.
    print("\nJeu de tests :")
    ok &= _check("au moins 6 cas au total", len(testcases.CASES) >= 6,
                 f"{len(testcases.CASES)} cas")
    ok &= _check("au moins 2 cas d'injection", len(testcases.injection_cases()) >= 2,
                 f"{len(testcases.injection_cases())} cas")
    ok &= _check("couverture FR et EN",
                 {c["lang"] for c in testcases.CASES} == {"fr", "en"})
    for c in testcases.CASES:
        valid = bool(c["mode"] in config.MODES and c["lang"] in config.LANGUES and c.get("input"))
        ok &= _check(f"cas {c['id']} : structure valide", valid)

    # 4) Corpus de démo : entrées valides et origines honnêtes.
    print("\nCorpus de démo :")
    entries = demo.entries()
    ok &= _check("corpus non vide", len(entries) >= 1, f"{len(entries)} entrées")
    for e in entries:
        good = bool(
            e.get("mode") in config.MODES
            and e.get("lang") in config.LANGUES
            and e.get("origin") in ("manuelle", "api")
            and str(e.get("output", {}).get("corps", "")).strip()
        )
        ok &= _check(f"entrée démo {e.get('mode')}/{e.get('lang')} valide", good)

    print("\n" + ("✅ TOUT EST COHÉRENT." if ok else "❌ DES INCOHÉRENCES ONT ÉTÉ DÉTECTÉES."))
    return ok


if __name__ == "__main__":
    sys.exit(0 if verify() else 1)
