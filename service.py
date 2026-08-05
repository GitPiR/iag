# -*- coding: utf-8 -*-
"""Couche service — orchestration entre l'UI, les prompts et la couche LLM.

Sépare la logique métier de Streamlit : ce module est testable sans lancer
l'UI (§ 9). Il gère :
- la validation des entrées du formulaire (messages explicites, § 4.8) ;
- la génération de la première version (prompt de production) ;
- la passe d'auto-critique produisant la version améliorée (§ 4.5).

Aucune de ces fonctions ne lève d'exception vers l'UI : elles renvoient des
`LLMResult` uniformes ou des tuples (ok, message).
"""

from __future__ import annotations

import config
import llm
from prompts import library


# ---------------------------------------------------------------------------
# Validation des entrées (§ 4.8 : entrée invalide -> message explicite)
# ---------------------------------------------------------------------------
def validate_inputs(mode: str, lang: str, user_text: str, opts: dict | None) -> tuple[bool, str]:
    """Valide les paramètres du formulaire. Renvoie (ok, message_erreur).

    Un message vide accompagne un succès. Les messages d'échec sont destinés à
    être affichés tels quels à l'utilisateur.
    """
    opts = opts or {}

    if mode not in config.MODES:
        return False, f"Mode inconnu : « {mode} ». Modes valides : {', '.join(config.MODES)}."
    if lang not in config.LANGUES:
        return False, "Langue de sortie invalide : choisissez « fr » ou « en »."

    # Champ obligatoire : la saisie utilisateur.
    text = (user_text or "").strip()
    if not text:
        return False, "Veuillez saisir le texte ou les éléments à traiter avant de générer."
    if len(text) < 3:
        return False, "La saisie est trop courte pour produire un résultat utile. Ajoutez des détails."
    if len(text) > 6000:
        return False, "La saisie est trop longue (plus de 6000 caractères). Raccourcissez-la."

    # Contrôles des options propres au mode.
    ton = opts.get("ton", "neutre")
    if ton not in config.TONS:
        return False, f"Ton invalide : « {ton} ». Tons valides : {', '.join(config.TONS)}."

    longueur = opts.get("longueur", config.DEFAULT_LENGTH)
    if longueur not in config.LENGTH_RANGES:
        return False, f"Longueur invalide : « {longueur} ». Valides : {', '.join(config.LENGTH_RANGES)}."

    if mode == "relance":
        niveau = opts.get("niveau", "douce")
        if niveau not in config.NIVEAUX_RELANCE:
            return False, (
                f"Niveau de relance invalide : « {niveau} ». "
                f"Valides : {', '.join(config.NIVEAUX_RELANCE)}."
            )

    if mode == "post":
        plateforme = opts.get("plateforme", "linkedin")
        if plateforme not in config.PLATEFORMES:
            return False, (
                f"Plateforme invalide : « {plateforme} ». "
                f"Valides : {', '.join(config.PLATEFORMES)}."
            )

    return True, ""


# ---------------------------------------------------------------------------
# Génération de la première version
# ---------------------------------------------------------------------------
def generate_message(mode: str, lang: str, user_text: str, opts: dict | None = None,
                     *, max_retries: int = 0, retry_delay: float = 5.0) -> tuple[llm.LLMResult, dict]:
    """Génère la première version via le prompt de production.

    Renvoie (résultat, prompt_dict). Le `prompt_dict` alimente le panneau
    « Voir le prompt envoyé » de l'UI, même en cas d'échec de l'appel.
    `max_retries` est laissé à 0 pour l'UI (réactivité) et monté par le harnais.
    """
    ok, message = validate_inputs(mode, lang, user_text, opts)
    prompt = library.build_prompt(mode, lang, user_text, opts)
    if not ok:
        return (
            llm.LLMResult(ok=False, error=message, error_code="INVALID_INPUT", meta={"source": "validation"}),
            prompt,
        )

    result = llm.generate(
        prompt["system_instruction"],
        prompt["user_content"],
        response_schema=prompt["response_schema"],
        temperature=prompt["temperature"],
        seed=prompt["seed"],
        model=prompt["model"],
        max_retries=max_retries,
        retry_delay=retry_delay,
    )
    return result, prompt


# ---------------------------------------------------------------------------
# Version améliorée (auto-critique)
# ---------------------------------------------------------------------------
def improve_message(mode: str, lang: str, first_output: dict) -> tuple[llm.LLMResult, dict]:
    """Produit la version améliorée à partir de la première sortie (§ 4.5).

    Renvoie (résultat, prompt_dict) pour affichage comparatif et traçabilité.
    """
    prompt = library.build_autocritique_prompt(mode, lang, first_output)
    result = llm.generate(
        prompt["system_instruction"],
        prompt["user_content"],
        response_schema=prompt["response_schema"],
        temperature=prompt["temperature"],
        model=prompt["model"],
    )
    return result, prompt
