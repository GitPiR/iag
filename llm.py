# -*- coding: utf-8 -*-
"""Couche d'accès au modèle — ISOLÉE et unique (§ 5.5).

Toute l'application passe par UNE seule fonction de génération : `generate`.
Objectifs de conception :

* **Isolation fournisseur** : changer de fournisseur (p. ex. Mistral pour un
  hébergement UE, cf. analyse critique) ne touche que ce fichier.
* **Ne lève jamais d'exception** : `generate` renvoie toujours un objet
  `LLMResult` uniforme (`ok`, `data`, `error`, `error_code`, `meta`). L'UI n'a
  ainsi jamais à afficher de trace Python brute (§ 4.8).
* **Import paresseux du SDK** : le SDK n'est importé qu'au moment de l'appel
  réseau, pour que les tests et le mode démo s'exécutent sans le SDK ni la clé.
* **Parsing JSON défensif en secours** : même avec `response_schema` natif, on
  conserve un parseur robuste pour les cas de troncature ou de repli.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import config


# ---------------------------------------------------------------------------
# Objet résultat uniforme
# ---------------------------------------------------------------------------
@dataclass
class LLMResult:
    """Résultat homogène renvoyé par `generate`, quel que soit le chemin.

    Attributs
    ---------
    ok        : True si une donnée exploitable a été obtenue.
    data      : dict parsé depuis la réponse (ou None en cas d'échec).
    raw_text  : texte brut renvoyé par le modèle (utile au débogage / affichage).
    error     : message d'erreur LISIBLE par un humain (jamais une trace).
    error_code: code technique court et stable ('NO_KEY', 'QUOTA', ...),
                utilisable par l'UI pour router l'affichage.
    meta      : métadonnées (modèle, température, source, tokens, ...).
    """

    ok: bool
    data: dict | None = None
    raw_text: str = ""
    error: str | None = None
    error_code: str | None = None
    meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Parsing JSON défensif (§ 5.3) — testable sans SDK
# ---------------------------------------------------------------------------
def _strip_markdown_fences(text: str) -> str:
    """Retire d'éventuelles clôtures Markdown ```json ... ``` autour du JSON."""
    t = text.strip()
    if t.startswith("```"):
        # Retire la première ligne d'ouverture (``` ou ```json)
        newline = t.find("\n")
        if newline != -1:
            t = t[newline + 1 :]
        # Retire la clôture finale
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def _extract_first_balanced_object(text: str) -> str | None:
    """Extrait le premier objet JSON équilibré `{...}`.

    Ignore les accolades situées à l'intérieur des chaînes et gère
    l'échappement, pour survivre à un texte tronqué ou entouré de prose.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None  # Objet non refermé (troncature) : échec propre


def parse_json_defensive(text: str) -> dict | None:
    """Tente de parser du JSON de façon robuste. Renvoie None si impossible.

    Stratégie : (1) parsing direct ; (2) retrait des clôtures Markdown ;
    (3) extraction du premier objet équilibré. Aucune exception ne remonte.
    """
    if not text:
        return None
    # 1) Chemin nominal
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except (json.JSONDecodeError, TypeError):
        pass
    # 2) Retrait des clôtures Markdown
    cleaned = _strip_markdown_fences(text)
    try:
        obj = json.loads(cleaned)
        return obj if isinstance(obj, dict) else None
    except (json.JSONDecodeError, TypeError):
        pass
    # 3) Extraction du premier objet équilibré
    candidate = _extract_first_balanced_object(cleaned)
    if candidate:
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else None
        except (json.JSONDecodeError, TypeError):
            return None
    return None


# ---------------------------------------------------------------------------
# Traduction des erreurs SDK en messages lisibles
# ---------------------------------------------------------------------------
def _classify_api_error(exc: Any) -> tuple[str, str]:
    """Traduit une exception d'API en (error_code, message_lisible).

    On lit `.code` et `.message` (attributs documentés d'`errors.APIError`) sans
    dépendre de classes non documentées.
    """
    code = getattr(exc, "code", None)
    message = getattr(exc, "message", None) or str(exc)

    if code in (401, 403):
        return "KEY_REFUSED", (
            "Clé API refusée ou droits insuffisants. Vérifiez GEMINI_API_KEY "
            "et son activation dans Google AI Studio."
        )
    if code == 404:
        return "MODEL_GONE", (
            f"Modèle « {config.MODEL_ID} » introuvable (peut-être retiré du "
            "catalogue). Confirmez l'identifiant dans Google AI Studio."
        )
    if code == 429:
        return "QUOTA", (
            "Quota dépassé ou trop de requêtes. Réessayez plus tard ou "
            "vérifiez votre plan de facturation."
        )
    if isinstance(code, int) and 500 <= code < 600:
        return "SERVER", (
            "Le service Gemini a renvoyé une erreur serveur. C'est temporaire : "
            "réessayez dans quelques instants."
        )
    if isinstance(code, int) and 400 <= code < 500:
        return "CLIENT", f"Requête invalide (code {code}) : {message}"
    return "API_ERROR", f"Erreur d'API : {message}"


# ---------------------------------------------------------------------------
# Fonction de génération unique
# ---------------------------------------------------------------------------
def generate(
    system_instruction: str,
    user_content: str,
    *,
    response_schema: dict | None = None,
    temperature: float | None = None,
    seed: int | None = None,
    model: str | None = None,
    expect_json: bool = True,
    max_retries: int = 0,
    retry_delay: float = 5.0,
) -> LLMResult:
    """Appelle le modèle et renvoie un `LLMResult`. NE LÈVE JAMAIS.

    Paramètres
    ----------
    system_instruction : consigne développeur (rôle, garde-fous, format...).
    user_content       : données utilisateur, déjà délimitées par l'appelant.
    response_schema    : schéma dict pour la sortie structurée native (ou None).
    temperature        : température, ou None pour ne pas transmettre le
                         paramètre (laisse le défaut du modèle, cf. § 5.4).
    seed               : graine optionnelle (stabilité du juge).
    model              : identifiant de modèle (défaut : config.MODEL_ID).
    expect_json        : True -> parse la réponse en JSON (défaut). False ->
                         renvoie le texte brut dans data["corps"] (utilisé par
                         les paliers naïfs du journal, qui produisent du texte
                         libre non structuré).
    max_retries        : nombre de nouvelles tentatives sur erreur TRANSITOIRE
                         (429 quota, 5xx serveur). 0 par défaut pour ne pas
                         ralentir l'UI ; le harnais d'évaluation le monte à ~5
                         afin de tenir sur le palier gratuit (limite par minute).
    retry_delay        : délai de base (s) du back-off exponentiel entre essais.
    """
    model = model or config.MODEL_ID
    meta: dict = {"model": model, "temperature": temperature, "source": "api"}

    # 1) Clé présente ?
    api_key = config.get_api_key()
    if not api_key:
        return LLMResult(
            ok=False,
            error=(
                "Aucune clé API détectée. Renseignez GEMINI_API_KEY dans un "
                "fichier .env, ou activez le mode démo pour des exemples "
                "hors-ligne."
            ),
            error_code="NO_KEY",
            meta=meta,
        )

    # 2) Import paresseux du SDK (absent en test / démo).
    try:
        from google import genai
        from google.genai import types, errors
    except ImportError:
        return LLMResult(
            ok=False,
            error=(
                "Le SDK 'google-genai' n'est pas installé. Lancez "
                "'pip install -r requirements.txt', ou utilisez le mode démo."
            ),
            error_code="NO_SDK",
            meta=meta,
        )

    # 3) Construction de la configuration d'appel.
    config_kwargs: dict = {"system_instruction": system_instruction}
    if response_schema is not None:
        config_kwargs["response_mime_type"] = "application/json"
        config_kwargs["response_schema"] = response_schema
    if temperature is not None:
        config_kwargs["temperature"] = temperature
    if seed is not None:
        config_kwargs["seed"] = seed

    # 4) Appel réseau protégé, avec retry sur erreurs TRANSITOIRES (429/5xx).
    # Le back-off exponentiel est plafonné à 60 s : la limite « par minute » du
    # palier gratuit se réinitialise en une minute, inutile d'attendre plus.
    attempt = 0
    while True:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=user_content,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            break
        except errors.APIError as exc:
            code = getattr(exc, "code", None)
            transient = code == 429 or (isinstance(code, int) and 500 <= code < 600)
            if transient and attempt < max_retries:
                time.sleep(min(retry_delay * (2 ** attempt), 60.0))
                attempt += 1
                continue
            # Erreur définitive (ou plus de tentatives) : message lisible.
            c, message = _classify_api_error(exc)
            return LLMResult(ok=False, error=message, error_code=c, meta=meta)
        except Exception as exc:  # noqa: BLE001
            # Dernier rempart JUSTIFIÉ (§ 5.5) : les pannes réseau remontent sous
            # des types trop variés (httpx, ssl, socket, timeout) pour être
            # toutes énumérées sans risque d'en oublier. On tente aussi un retry
            # (coupures passagères), sans rien AVALER : type et message restent
            # visibles dans le message d'erreur final.
            if attempt < max_retries:
                time.sleep(min(retry_delay * (2 ** attempt), 60.0))
                attempt += 1
                continue
            return LLMResult(
                ok=False,
                error=(
                    "Échec de l'appel réseau au service Gemini "
                    f"({type(exc).__name__} : {exc}). Vérifiez votre connexion "
                    "puis réessayez."
                ),
                error_code="NETWORK",
                meta=meta,
            )

    # 5) Extraction du texte.
    raw_text = getattr(response, "text", None) or ""
    if not raw_text.strip():
        return LLMResult(
            ok=False,
            raw_text=raw_text,
            error="Le modèle a renvoyé une réponse vide. Réessayez.",
            error_code="EMPTY",
            meta=meta,
        )

    # 6a) Texte libre attendu (paliers naïfs) : pas de parsing JSON.
    if not expect_json:
        return LLMResult(
            ok=True,
            data={"corps": raw_text.strip(), "infos_manquantes": []},
            raw_text=raw_text,
            meta=meta,
        )

    # 6) Parsing (défensif même avec schéma natif).
    data = parse_json_defensive(raw_text)
    if data is None:
        return LLMResult(
            ok=False,
            raw_text=raw_text,
            error=(
                "La réponse du modèle n'est pas au format attendu (JSON "
                "illisible ou tronqué). Réessayez."
            ),
            error_code="BAD_FORMAT",
            meta=meta,
        )

    # 7) Métadonnées de consommation (best-effort, jamais bloquantes).
    usage = getattr(response, "usage_metadata", None)
    if usage is not None:
        meta["tokens"] = {
            "prompt": getattr(usage, "prompt_token_count", None),
            "output": getattr(usage, "candidates_token_count", None),
            "total": getattr(usage, "total_token_count", None),
        }

    return LLMResult(ok=True, data=data, raw_text=raw_text, meta=meta)
