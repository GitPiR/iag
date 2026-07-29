# -*- coding: utf-8 -*-
"""Harnais d'évaluation — campagne reproductible (§ 7).

Pour chaque cas : génération (prompt de production), contrôles déterministes,
notation par le juge LLM, le tout répété N fois (N ≥ 3) pour rapporter
min / max / moyenne / écart-type. Les artefacts (JSON + CSV) sont sauvegardés
pour rejeu sans re-solliciter l'API, et les échecs sont détectés
AUTOMATIQUEMENT (par construction, pour ne pas ne relire que les cas qui
arrangent).

Usage :
    python -m evaluation.harness --draws 3 --modes core            # campagne réelle
    python -m evaluation.harness --draws 3 --dry-run               # aucun appel API
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import time

import config
import service
from evaluation import deterministic, judge, rubric, testcases


# ---------------------------------------------------------------------------
# Statistiques de variance (§ 7.5)
# ---------------------------------------------------------------------------
def summarize(values: list[float]) -> dict:
    """Retourne min / max / moyenne / écart-type d'une série de notes."""
    if not values:
        return {"min": None, "max": None, "mean": None, "std": None, "n": 0}
    return {
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "mean": round(statistics.fmean(values), 2),
        "std": round(statistics.pstdev(values), 2) if len(values) > 1 else 0.0,
        "n": len(values),
    }


# ---------------------------------------------------------------------------
# Détection automatique et exhaustive des échecs (§ 7.7)
# ---------------------------------------------------------------------------
def detect_failure(record: dict) -> list[str]:
    """Retourne la liste des motifs d'échec d'un tirage (vide si aucun).

    Un tirage est un échec si : une note du juge vaut 1, la langue ou la
    longueur sort des clous, une hallucination est signalée, ou une injection
    a réussi. La détection est automatique, indépendante d'une relecture.
    """
    motifs = []
    det = record.get("deterministic", {})
    if det.get("language", {}).get("ok") is False:
        motifs.append("langue_hors_cible")
    if det.get("length", {}).get("ok") is False:
        motifs.append("longueur_hors_fourchette")
    if det.get("format", {}).get("ok") is False:
        motifs.append("format_invalide")
    if "injection" in det and det["injection"].get("injected"):
        motifs.append("injection_reussie")

    jd = record.get("judge")
    if jd:
        if jd.get("hallucination"):
            motifs.append("hallucination_signalee_juge")
        for crit, val in jd.get("scores", {}).items():
            if val == 1:
                motifs.append(f"note_1_{crit}")
    return motifs


# ---------------------------------------------------------------------------
# Exécution d'un cas
# ---------------------------------------------------------------------------
def run_case(case: dict, n_draws: int) -> dict:
    """Joue un cas n_draws fois : génération + déterministe + juge."""
    draws = []
    for i in range(n_draws):
        gen_result, prompt = service.generate_message(
            case["mode"], case["lang"], case["input"], case.get("opts")
        )
        record: dict = {"draw": i, "case_id": case["id"]}

        if not gen_result.ok:
            record["gen_error"] = {"code": gen_result.error_code, "message": gen_result.error}
            record["deterministic"] = {}
            record["judge"] = None
            draws.append(record)
            continue

        data = gen_result.data
        record["output"] = data
        record["meta"] = gen_result.meta

        # Contrôles déterministes (aucun appel API).
        longueur = case.get("opts", {}).get("longueur", config.DEFAULT_LENGTH)
        det = deterministic.run_all(
            data, case["mode"], case["lang"], longueur,
            injection_marker=case.get("injection_marker", ""),
        )
        record["deterministic"] = det

        # Notation par le juge LLM.
        judge_result = judge.judge_output(case, data)
        if judge_result.ok:
            record["judge"] = judge.normalize_scores(judge_result.data)
        else:
            record["judge"] = None
            record["judge_error"] = {"code": judge_result.error_code, "message": judge_result.error}

        record["failures"] = detect_failure(record)
        draws.append(record)

    # Agrégation de la variance sur les notes globales du juge.
    globals_ = [d["judge"]["global"] for d in draws if d.get("judge")]
    return {
        "case_id": case["id"],
        "mode": case["mode"],
        "lang": case["lang"],
        "opts": case.get("opts", {}),
        "draws": draws,
        "global_summary": summarize(globals_),
    }


# ---------------------------------------------------------------------------
# Campagne complète
# ---------------------------------------------------------------------------
def run_campaign(modes: str = "core", n_draws: int = 3, output_dir: str | None = None) -> dict:
    """Joue la campagne sur les cas des modes demandés."""
    output_dir = output_dir or config.OUTPUTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    if n_draws < 3:
        print("⚠️  AVERTISSEMENT : moins de 3 tirages demandés. À température non "
              "nulle, une note isolée mesure autant le hasard que le prompt (§ 7.5).")

    selected = config.CORE_MODES if modes == "core" else config.MODES
    cases = testcases.cases_for_modes(selected)

    results = []
    for case in cases:
        print(f"→ Cas {case['id']} ({n_draws} tirages)...")
        results.append(run_case(case, n_draws))

    campaign = {
        "meta": {
            "model": config.MODEL_ID,
            "judge_model": config.JUDGE_MODEL_ID,
            "n_draws": n_draws,
            "modes": modes,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "n_cases": len(cases),
        },
        "results": results,
    }
    _save_artifacts(campaign, output_dir)
    return campaign


def _save_artifacts(campaign: dict, output_dir: str) -> None:
    """Sauvegarde JSON (complet), CSV (synthèse) et fichier d'échecs (§ 7.6)."""
    stamp = time.strftime("%Y%m%d_%H%M%S")

    json_path = os.path.join(output_dir, f"campagne_{stamp}.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(campaign, fh, ensure_ascii=False, indent=2)

    # CSV de synthèse : une ligne par tirage.
    csv_path = os.path.join(output_dir, f"campagne_{stamp}.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        header = ["case_id", "mode", "lang", "draw"] + rubric.CRITERIA_ORDER + [
            "global", "hallucination", "lang_ok", "len_ok", "words", "failures"
        ]
        writer.writerow(header)
        for res in campaign["results"]:
            for d in res["draws"]:
                jd = d.get("judge") or {}
                scores = jd.get("scores", {})
                det = d.get("deterministic", {})
                writer.writerow([
                    res["case_id"], res["mode"], res["lang"], d["draw"],
                    *[scores.get(c, "") for c in rubric.CRITERIA_ORDER],
                    jd.get("global", ""),
                    jd.get("hallucination", ""),
                    det.get("language", {}).get("ok", ""),
                    det.get("length", {}).get("ok", ""),
                    det.get("length", {}).get("words", ""),
                    "|".join(d.get("failures", [])),
                ])

    # Fichier d'échecs dédié (détection automatique).
    failures = []
    for res in campaign["results"]:
        for d in res["draws"]:
            motifs = d.get("failures") or []
            if motifs or d.get("gen_error"):
                failures.append({
                    "case_id": res["case_id"], "draw": d["draw"],
                    "motifs": motifs, "gen_error": d.get("gen_error"),
                    "output": d.get("output"),
                    "judge_justification": (d.get("judge") or {}).get("justification"),
                })
    fail_path = os.path.join(output_dir, f"echecs_{stamp}.json")
    with open(fail_path, "w", encoding="utf-8") as fh:
        json.dump(failures, fh, ensure_ascii=False, indent=2)

    print(f"\n✅ Artefacts écrits :\n  {json_path}\n  {csv_path}\n  {fail_path}")
    print(f"   {len(failures)} tirage(s) en échec détecté(s) automatiquement.")


def estimate_calls(modes: str, n_draws: int) -> int:
    """Estime le nombre d'appels API d'une campagne (2 par tirage : gén + juge)."""
    selected = config.CORE_MODES if modes == "core" else config.MODES
    n_cases = len(testcases.cases_for_modes(selected))
    return n_cases * n_draws * 2


def main() -> None:
    parser = argparse.ArgumentParser(description="Campagne d'évaluation du prototype.")
    parser.add_argument("--draws", type=int, default=3, help="Nombre de tirages par cas (≥ 3).")
    parser.add_argument("--modes", choices=["core", "all"], default="core")
    parser.add_argument("--dry-run", action="store_true",
                        help="N'appelle pas l'API : affiche seulement le coût estimé.")
    args = parser.parse_args()

    calls = estimate_calls(args.modes, args.draws)
    print(f"Coût estimé : {calls} appels API "
          f"({len(testcases.cases_for_modes(config.CORE_MODES if args.modes == 'core' else config.MODES))} "
          f"cas × {args.draws} tirages × 2 appels [génération + juge]).")

    if args.dry_run:
        print("Essai à blanc (--dry-run) : aucune requête envoyée.")
        return
    if not config.get_api_key():
        print("❌ Aucune clé API (GEMINI_API_KEY). Renseignez .env, ou utilisez --dry-run.")
        return

    run_campaign(modes=args.modes, n_draws=args.draws)


if __name__ == "__main__":
    main()
