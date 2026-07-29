# -*- coding: utf-8 -*-
"""Rejeu du journal des itérations (§ 6.5).

Joue les CINQ paliers (v1 → v5) sur un sous-ensemble de CAS DISCRIMINANTS,
avec le MÊME juge, et génère automatiquement le journal de résultats (tableaux
de progression, gain par itération). Aucun chiffre n'est recopié à la main :
une itération « documentée » retranscrite manuellement n'a aucune valeur de
preuve.

Cas discriminants sélectionnés — chacun teste UNE hypothèse précise :
- email_en_devis          : la consigne de langue (saisie FR, sortie EN).
- email_fr_infos_manquantes : le garde-fou anti-invention (date non fournie).
- avis_fr_tres_negatif    : l'apport du contre-exemple (avis négatif).
- injection_avis_fr       : la résistance à l'injection de prompt.

Usage :
    python -m evaluation.replay_journal --draws 3            # campagne réelle
    python -m evaluation.replay_journal --draws 1 --dry-run  # essai à blanc réduit
"""

from __future__ import annotations

import argparse
import json
import os
import time

import config
import llm
from evaluation import deterministic, judge, rubric, testcases
from prompts import journal

# Cas discriminants (par id, résolus depuis le jeu de tests).
DISCRIMINANT_IDS = [
    "email_en_devis",
    "email_fr_infos_manquantes",
    "avis_fr_tres_negatif",
    "injection_avis_fr",
]


def _case_by_id(case_id: str) -> dict:
    for c in testcases.CASES:
        if c["id"] == case_id:
            return c
    raise KeyError(case_id)


def _generate_for_version(spec: dict) -> llm.LLMResult:
    """Appelle le modèle pour un palier donné.

    v1/v2 produisent du texte libre (expect_json=False) ; v3/v4 demandent le
    JSON dans le prompt sans schéma natif (on mesure le taux de JSON
    exploitable) ; v5 utilise le schéma natif.
    """
    version = spec["version"]
    expect_json = version not in ("v1_naif", "v2_role")
    return llm.generate(
        spec["system_instruction"],
        spec["user_content"],
        response_schema=spec["response_schema"],
        temperature=spec["temperature"],
        seed=spec["seed"],
        expect_json=expect_json,
    )


def run_replay(n_draws: int, output_dir: str | None = None) -> dict:
    """Joue les 5 paliers sur les cas discriminants, n_draws fois."""
    output_dir = output_dir or config.OUTPUTS_DIR
    os.makedirs(output_dir, exist_ok=True)
    cases = [_case_by_id(cid) for cid in DISCRIMINANT_IDS]

    per_version: dict[str, list] = {v: [] for v in journal.VERSIONS}

    for case in cases:
        for version in journal.VERSIONS:
            spec = journal.build_version(
                version, case["mode"], case["lang"], case["input"], case.get("opts")
            )
            for i in range(n_draws):
                gen = _generate_for_version(spec)
                rec = {"case_id": case["id"], "version": version, "draw": i}
                if not gen.ok:
                    rec["gen_error"] = {"code": gen.error_code, "message": gen.error}
                    # Un JSON demandé mais illisible EST le résultat qu'on mesure.
                    rec["json_exploitable"] = False
                    per_version[version].append(rec)
                    continue

                data = gen.data
                rec["json_exploitable"] = True
                rec["output"] = data
                longueur = case.get("opts", {}).get("longueur", config.DEFAULT_LENGTH)
                rec["deterministic"] = deterministic.run_all(
                    data, case["mode"], case["lang"], longueur,
                    injection_marker=case.get("injection_marker", ""),
                )
                jr = judge.judge_output(case, data)
                rec["judge"] = judge.normalize_scores(jr.data) if jr.ok else None
                per_version[version].append(rec)

    replay = {
        "meta": {
            "model": config.MODEL_ID,
            "judge_model": config.JUDGE_MODEL_ID,
            "n_draws": n_draws,
            "cases": DISCRIMINANT_IDS,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "per_version": per_version,
        "progression": _progression(per_version),
    }
    _save(replay, output_dir)
    return replay


def _progression(per_version: dict) -> list[dict]:
    """Calcule, par palier, la moyenne globale et des indicateurs clés."""
    rows = []
    prev_mean = None
    for version in journal.VERSIONS:
        recs = per_version[version]
        globals_ = [r["judge"]["global"] for r in recs if r.get("judge")]
        mean = round(sum(globals_) / len(globals_), 2) if globals_ else None
        json_ok = sum(1 for r in recs if r.get("json_exploitable"))
        lang_ok = sum(1 for r in recs if r.get("deterministic", {}).get("language", {}).get("ok"))
        inj = [r for r in recs if "injection" in r.get("deterministic", {})]
        inj_blocked = sum(1 for r in inj if r["deterministic"]["injection"]["ok"])
        gain = None if (mean is None or prev_mean is None) else round(mean - prev_mean, 2)
        rows.append({
            "version": version,
            "technique": journal.VERSION_META[version][0],
            "moyenne_globale": mean,
            "gain_vs_precedent": gain,
            "json_exploitable": f"{json_ok}/{len(recs)}",
            "langue_ok": f"{lang_ok}/{len(recs)}",
            "injection_bloquee": f"{inj_blocked}/{len(inj)}" if inj else "n/a",
        })
        if mean is not None:
            prev_mean = mean
    return rows


def _save(replay: dict, output_dir: str) -> None:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(output_dir, f"journal_rejeu_{stamp}.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(replay, fh, ensure_ascii=False, indent=2)

    # Journal de résultats lisible (Markdown), généré automatiquement.
    md_path = os.path.join(output_dir, "journal_resultats.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# Journal de résultats (généré automatiquement)\n\n")
        fh.write(f"- Modèle : `{replay['meta']['model']}` — Juge : "
                 f"`{replay['meta']['judge_model']}`\n")
        fh.write(f"- Tirages par (cas × palier) : {replay['meta']['n_draws']}\n")
        fh.write(f"- Cas discriminants : {', '.join(replay['meta']['cases'])}\n\n")
        fh.write("| Palier | Technique | Moy. /5 | Gain | JSON exploitable | "
                 "Langue OK | Injection bloquée |\n")
        fh.write("|---|---|---|---|---|---|---|\n")
        for r in replay["progression"]:
            fh.write(f"| {r['version']} | {r['technique']} | {r['moyenne_globale']} | "
                     f"{r['gain_vs_precedent']} | {r['json_exploitable']} | "
                     f"{r['langue_ok']} | {r['injection_bloquee']} |\n")
    print(f"\n✅ Journal écrit :\n  {json_path}\n  {md_path}")


def estimate_calls(n_draws: int) -> int:
    """5 paliers × cas discriminants × tirages × 2 (génération + juge)."""
    return 5 * len(DISCRIMINANT_IDS) * n_draws * 2


def main() -> None:
    parser = argparse.ArgumentParser(description="Rejeu du journal des 5 paliers.")
    parser.add_argument("--draws", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    calls = estimate_calls(args.draws)
    print(f"Coût estimé : {calls} appels API "
          f"(5 paliers × {len(DISCRIMINANT_IDS)} cas × {args.draws} tirages × 2).")
    if args.dry_run:
        print("Essai à blanc (--dry-run) : aucune requête envoyée.")
        return
    if not config.get_api_key():
        print("❌ Aucune clé API (GEMINI_API_KEY). Renseignez .env, ou utilisez --dry-run.")
        return
    run_replay(args.draws)


if __name__ == "__main__":
    main()
