# -*- coding: utf-8 -*-
"""Interface Streamlit — Atelier d'écriture générative (§ 4).

Assistant de rédaction de communications professionnelles pour freelances et
TPE/PME. UX épurée « une tâche, un écran, une action » : l'utilisateur voit au
départ seulement le mode, sa saisie et un bouton ; tout le reste (réglages,
prompt) est en repli. Toute la logique est déléguée à la couche `service`,
elle-même adossée à la couche LLM isolée (`llm`).

Lancement :
    streamlit run app.py
Vérification hors-ligne (sans Streamlit ni clé) :
    python app.py --verifier
"""

from __future__ import annotations

import sys

# Raccourci --verifier : on délègue AVANT d'importer Streamlit, pour que la
# vérification hors-ligne tourne sans dépendance UI ni clé API.
if "--verifier" in sys.argv:
    import verifier
    sys.exit(0 if verifier.verify() else 1)

import streamlit as st

import config
import demo
import service
from prompts import library

# ---------------------------------------------------------------------------
# Libellés (UI en français, valeurs internes stables)
# ---------------------------------------------------------------------------
MODE_LABELS = {
    "email": "✉️ Email",
    "relance": "🔔 Relance",
    "reponse_avis": "💬 Réponse à un avis",
    "post": "📣 Post",
    "reformuler": "✏️ Reformuler",
}
LANG_LABELS = {"fr": "Français", "en": "English"}
TON_LABELS = {"neutre": "Neutre", "chaleureux": "Chaleureux", "formel": "Formel", "direct": "Direct"}
LONGUEUR_LABELS = {"court": "Court", "moyen": "Moyen", "long": "Long"}
NIVEAU_LABELS = {"douce": "Douce", "ferme": "Ferme", "derniere_chance": "Dernière chance"}
PLATEFORME_LABELS = {"linkedin": "LinkedIn", "instagram": "Instagram", "twitter": "X/Twitter", "facebook": "Facebook"}

PLACEHOLDERS = {
    "email": "Objectif de l'email + éléments factuels (montant, date, référence…).",
    "relance": "Facture/prospect concerné, montant, échéance, contexte.",
    "reponse_avis": "Collez l'avis ou le message du client (note, contenu).",
    "post": "Message à faire passer, événement à annoncer.",
    "reformuler": "Collez le texte à corriger ou clarifier.",
}


# ---------------------------------------------------------------------------
# Rendu d'une sortie (objet / message / infos manquantes)
# ---------------------------------------------------------------------------
def _render_output(data: dict, *, origin: str | None = None, key: str = ""):
    if data.get("objet"):
        st.markdown(f"**Objet —** {data['objet']}")
    corps = data.get("corps", "")
    st.text_area("Message", value=corps, height=240, key=f"corps_{key}",
                 label_visibility="collapsed")
    # Vrai bouton copier, sans encombrer l'écran : un popover révèle un bloc
    # avec l'icône de copie native de st.code.
    with st.popover("📋 Copier"):
        st.code(corps, language=None)
    infos = data.get("infos_manquantes") or []
    if infos:
        st.warning("⚠️ À compléter avant envoi (signalé, non inventé) :")
        for i in infos:
            st.markdown(f"- {i}")
    if origin:
        libelle = "produite par l'API" if origin == "api" else "rédigée à la main (amorce de démo)"
        st.caption(f"Origine : {libelle}.")


def _render_prompt_panel(prompt: dict):
    """Traçabilité du prompt — tout en bas, replié (preuve pour le correcteur)."""
    with st.expander("🔍 Voir le prompt envoyé (traçabilité)"):
        temp = prompt.get("temperature")
        st.caption(f"Modèle : `{prompt.get('model', config.MODEL_ID)}` · "
                   f"Température : {'défaut du modèle' if temp is None else temp}")
        st.markdown("**system_instruction**")
        st.code(prompt.get("system_instruction", ""), language=None)
        st.markdown("**Contenu utilisateur (données délimitées)**")
        st.code(prompt.get("user_content", ""), language=None)
        st.markdown("**response_schema**")
        st.json(prompt.get("response_schema", {}), expanded=False)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Atelier d'écriture générative", page_icon="✍️")

    has_key = bool(config.get_api_key())
    ss = st.session_state
    # Le mode démo est forcé sans clé ; avec clé, il est proposé dans les options.
    ss.setdefault("force_demo", False)
    demo_mode = (not has_key) or ss["force_demo"]

    # En-tête minimal : titre + badge d'état + rappel d'usage en une ligne.
    left, right = st.columns([4, 1])
    with left:
        st.title("✍️ Atelier d'écriture")
    with right:
        st.markdown(
            "<div style='text-align:right;padding-top:22px'>"
            + ("🟢 En ligne" if not demo_mode else "⚪ Démo")
            + "</div>",
            unsafe_allow_html=True,
        )
    st.caption("Email · relance · réponse à un avis, pour freelances et TPE. "
               "⚠️ Contenu IA — **à relire et à assumer avant envoi** (une réponse à un avis est publique).")

    # 1) Mode : sélecteur visuel (un clic, tout visible).
    mode = st.segmented_control(
        "Mode", list(MODE_LABELS), format_func=lambda v: MODE_LABELS[v],
        default="email", key="mode", label_visibility="collapsed",
    ) or "email"

    # 2) Saisie.
    user_text = st.text_area("Votre saisie", height=150, key="saisie",
                             placeholder=PLACEHOLDERS.get(mode, ""),
                             label_visibility="collapsed")

    # 3) Options avancées, repliées par défaut (défauts sensés pour 90 % des cas).
    with st.expander("⚙️ Options"):
        lang = st.segmented_control("Langue", list(LANG_LABELS),
                                    format_func=lambda v: LANG_LABELS[v],
                                    default="fr", key="lang") or "fr"
        ton = st.segmented_control("Ton", list(TON_LABELS),
                                   format_func=lambda v: TON_LABELS[v],
                                   default="neutre", key="ton") or "neutre"
        longueur = st.segmented_control("Longueur", list(LONGUEUR_LABELS),
                                        format_func=lambda v: LONGUEUR_LABELS[v],
                                        default="moyen", key="longueur") or "moyen"
        opts = {"ton": ton, "longueur": longueur}
        if mode == "relance":
            opts["niveau"] = st.selectbox("Niveau d'insistance", list(NIVEAU_LABELS),
                                          format_func=lambda v: NIVEAU_LABELS[v], key="niveau")
        elif mode == "post":
            opts["plateforme"] = st.selectbox("Plateforme", list(PLATEFORME_LABELS),
                                              format_func=lambda v: PLATEFORME_LABELS[v], key="plateforme")
        if has_key:
            ss["force_demo"] = st.checkbox("Forcer le mode démo (hors-ligne)", value=ss["force_demo"])

    # Options par défaut si l'expander n'a pas été ouvert.
    opts = locals().get("opts", {"ton": "neutre", "longueur": "moyen"})
    lang = locals().get("lang", "fr")

    # 4) Une seule action, pleine largeur.
    if st.button("Générer", type="primary", use_container_width=True):
        _do_generate(mode, lang, user_text, opts, demo_mode)

    # Affichage persistant du dernier résultat (survit aux reruns des boutons).
    _render_last_result(mode, lang, opts)


def _do_generate(mode, lang, user_text, opts, demo_mode):
    ss = st.session_state
    ss.pop("improved", None)  # on repart d'une v1 propre
    if demo_mode:
        packed = demo.get_demo_output(mode, lang, opts)
        if packed is None:
            ss["result"] = {"error": "Aucune sortie de démo pour cette combinaison. "
                                      "Choisissez email, relance ou réponse à un avis."}
            return
        ss["result"] = {
            "data": packed["data"], "origin": packed.get("origin"),
            "demo_input": packed.get("input", ""),
            "prompt": library.build_prompt(mode, lang, user_text or packed.get("input", ""), opts),
        }
        return
    with st.status("Rédaction en cours…", expanded=False):
        result, prompt = service.generate_message(mode, lang, user_text, opts)
    ss["result"] = ({"data": result.data, "prompt": prompt} if result.ok
                    else {"error": result.error, "prompt": prompt})


def _render_last_result(mode, lang, opts):
    ss = st.session_state
    res = ss.get("result")
    if not res:
        return
    st.divider()
    if "error" in res:
        st.error(f"❌ {res['error']}")
        if res.get("prompt"):
            _render_prompt_panel(res["prompt"])
        return

    if res.get("demo_input"):
        st.caption(f"Saisie rejouée : « {res['demo_input']} »")
    st.markdown("#### Résultat")
    _render_output(res["data"], origin=res.get("origin"), key="v1")

    # 6) La version améliorée devient un bouton secondaire APRÈS la v1 :
    # on décide d'améliorer en voyant le premier jet (seulement en ligne).
    if not (res.get("origin")):  # pas en démo
        if st.button("✨ Améliorer cette version (auto-critique)"):
            with st.status("Auto-critique et amélioration…", expanded=False):
                improved, _ = service.improve_message(mode, lang, res["data"])
            ss["improved"] = {"data": improved.data} if improved.ok else {"error": improved.error}
        imp = ss.get("improved")
        if imp:
            if "error" in imp:
                st.warning(f"Version améliorée indisponible : {imp['error']}")
            else:
                st.markdown("#### Version améliorée")
                _render_output(imp["data"], key="v2")

    if res.get("prompt"):
        _render_prompt_panel(res["prompt"])


if __name__ == "__main__":
    main()
