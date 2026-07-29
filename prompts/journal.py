# -*- coding: utf-8 -*-
"""Journal des itérations de prompt — cinq paliers reconstruits par briques.

Le livrable le plus rentable du projet (§ 6.5). Chaque palier n'est PAS une
réécriture : il est construit à partir des mêmes briques que le prompt de
production (library.py), en n'activant qu'un sous-ensemble de features. Ainsi :

* `v5_production` est LITTÉRALEMENT le prompt qui tourne dans l'application
  (vérifié par tests/test_journal.py) ;
* les briques sont introduites UNE PAR UNE : on peut mesurer l'apport propre de
  chacune (l'exemple positif en v4, le contre-exemple en v5) au lieu de les
  créditer en bloc ;
* aucun palier avant v5 ne pose de délimiteurs : sans ce groupe témoin, la
  mesure anti-injection ne mesurerait rien ;
* v3 demande VOLONTAIREMENT le JSON dans le prompt (la mauvaise méthode) pour
  chiffrer combien de tirages produisent un JSON exploitable — ce chiffre
  justifie le passage au schéma natif en v5.

Tous les autres paramètres (modèle, température, tirages, juge) sont tenus
constants entre paliers : une seule variable change à la fois.
"""

from __future__ import annotations

from prompts import library as L
from prompts import schemas

# Température TENUE CONSTANTE sur tout le journal (§ 6.5, pt 4). Le réglage
# par mode de la production n'intervient pas ici : on isole l'effet du prompt.
JOURNAL_TEMPERATURE = 0.5

# Instruction naïve par mode : ce que taperait un utilisateur dans un chat.
_NAIVE_BY_MODE = {
    "email": "Écris un email professionnel pour ça :",
    "relance": "Écris une relance pour ça :",
    "reponse_avis": "Réponds à cet avis :",
    "post": "Écris un post pour ça :",
    "reformuler": "Reformule ça correctement :",
}

# Ordre des paliers. Chaque jeu de features est inclus dans le suivant, à
# l'exception documentée du passage json_in_prompt -> schéma natif en v5.
VERSIONS = ("v1_naif", "v2_role", "v3_contraintes", "v4_fewshot_gardefous", "v5_production")

_FEATURES_V2 = frozenset({L.F_ROLE, L.F_TASK})
_FEATURES_V3 = _FEATURES_V2 | {L.F_LANGUE, L.F_TON, L.F_LONGUEUR, L.F_JSON_IN_PROMPT}
_FEATURES_V4 = _FEATURES_V3 | {L.F_FEWSHOT_POS, L.F_GARDEFOUS, L.F_INFOS_MANQ}
# v5 : on RETIRE json_in_prompt (schéma natif) et on AJOUTE sécurité + contre-exemple.
_FEATURES_V5 = (_FEATURES_V4 - {L.F_JSON_IN_PROMPT}) | {L.F_SECURITE, L.F_CONTRE_EXEMPLE}

VERSION_FEATURES = {
    "v2_role": _FEATURES_V2,
    "v3_contraintes": _FEATURES_V3,
    "v4_fewshot_gardefous": _FEATURES_V4,
    "v5_production": _FEATURES_V5,
}

# Métadonnées documentaires (technique ajoutée / défaut visé).
VERSION_META = {
    "v1_naif": ("aucune — référence obligatoire", "—"),
    "v2_role": ("role prompting + description de tâche", "registre corporate, absence de structure"),
    "v3_contraintes": ("langue, longueur, ton, JSON demandé dans le prompt", "langue non respectée, longueur incontrôlée, sortie inexploitable"),
    "v4_fewshot_gardefous": ("exemple positif + garde-fous + champ infos_manquantes", "faits inventés, engagements non autorisés"),
    "v5_production": ("contre-exemple + anti-injection + response_schema natif", "défensivité, injection de prompt, JSON cassé"),
}


def build_version(version: str, mode: str, lang: str, user_text: str, opts: dict | None = None) -> dict:
    """Construit un palier complet (consigne, contenu, schéma, paramètres).

    Renvoie un dict homogène directement exploitable par le script de rejeu.
    Le `response_schema` n'est renseigné qu'en v5 (schéma natif) ; les paliers
    v3/v4 comptent sur le parsing défensif du JSON demandé dans le prompt ; v1/v2
    produisent du texte libre.
    """
    opts = opts or {}
    if version not in VERSIONS:
        raise ValueError(f"Version inconnue : {version!r}. Attendu : {VERSIONS}")

    if version == "v1_naif":
        naive = _NAIVE_BY_MODE.get(mode, _NAIVE_BY_MODE["email"])
        system_instruction = ""  # aucune consigne : c'est tout l'intérêt du témoin
        user_content = f"{naive}\n{user_text}"
        response_schema = None
    else:
        features = VERSION_FEATURES[version]
        system_instruction = L.build_system_instruction(mode, lang, opts, features)
        user_content = L.build_user_content(user_text, lang, features)
        response_schema = schemas.schema_for(mode) if version == "v5_production" else None

    technique, defaut = VERSION_META[version]
    return {
        "version": version,
        "technique": technique,
        "defaut_vise": defaut,
        "mode": mode,
        "lang": lang,
        "system_instruction": system_instruction,
        "user_content": user_content,
        "response_schema": response_schema,
        "temperature": JOURNAL_TEMPERATURE,
        "seed": None,
    }
