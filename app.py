# -*- coding: utf-8 -*-
"""Interface Streamlit — Atelier d'écriture générative (§ 4).

Assistant de rédaction de communications professionnelles pour freelances et
TPE/PME. L'UI reste minimale mais utilisable : elle délègue toute la logique à
la couche `service`, elle-même adossée à la couche LLM isolée (`llm`).

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
# Libellés des options (UI en français, valeurs internes stables)
# ---------------------------------------------------------------------------
MODE_LABELS = {
    "email": "✉️ Email professionnel",
    "relance": "🔔 Relance",
    "reponse_avis": "💬 Réponse à un avis",
    "post": "📣 Post réseau social (bonus)",
    "reformuler": "✏️ Reformuler (bonus)",
}
LANG_LABELS = {"fr": "Français", "en": "English"}
TON_LABELS = {"neutre": "Neutre", "chaleureux": "Chaleureux", "formel": "Formel", "direct": "Direct"}
LONGUEUR_LABELS = {"court": "Court", "moyen": "Moyen", "long": "Long"}
NIVEAU_LABELS = {"douce": "Douce", "ferme": "Ferme", "derniere_chance": "Dernière chance"}
PLATEFORME_LABELS = {"linkedin": "LinkedIn", "instagram": "Instagram", "twitter": "X/Twitter", "facebook": "Facebook"}


def _selectbox(label, options, fmt, key):
    return st.selectbox(label, options, format_func=lambda v: fmt[v], key=key)


def _render_output(data: dict, origin: str | None = None):
    """Affiche une sortie structurée (objet/corps/infos_manquantes)."""
    if origin:
        libelle = "produite par l'API" if origin == "api" else "rédigée à la main (amorce de démo)"
        st.caption(f"Origine de cette sortie : {libelle}.")
    if data.get("objet"):
        st.text_input("Objet", value=data["objet"], key=f"obj_{id(data)}")
    corps = data.get("corps", "")
    st.text_area("Message", value=corps, height=260, key=f"corps_{id(data)}")
    # Bouton copier : st.code offre une copie native, pratique et sans JS custom.
    with st.expander("📋 Copier le texte"):
        st.code(corps, language=None)
    infos = data.get("infos_manquantes") or []
    if infos:
        st.warning("⚠️ Informations à compléter avant envoi (signalées, non inventées) :")
        for i in infos:
            st.markdown(f"- {i}")


def _render_prompt_panel(prompt: dict):
    """Panneau « Voir le prompt envoyé » (§ 4.3) — décisif pour le correcteur."""
    with st.expander("🔍 Voir le prompt envoyé (traçabilité)"):
        st.markdown("**Modèle**")
        st.code(prompt.get("model", config.MODEL_ID))
        temp = prompt.get("temperature")
        st.markdown(f"**Température** : {'(non transmise — défaut du modèle)' if temp is None else temp}")
        st.markdown("**system_instruction**")
        st.code(prompt.get("system_instruction", ""), language=None)
        st.markdown("**Contenu utilisateur (données délimitées)**")
        st.code(prompt.get("user_content", ""), language=None)
        st.markdown("**response_schema (sortie structurée native)**")
        st.json(prompt.get("response_schema", {}))


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Atelier d'écriture générative", page_icon="✍️")
    st.title("✍️ Atelier d'écriture générative")
    st.caption("Assistant de communication pour freelances et TPE/PME — email, relance, réponse à un avis.")

    # Rappel d'usage responsable, en tête (§ 10.7).
    st.info(
        "🧭 **À relire et à assumer avant envoi.** Le texte est généré par IA : "
        "vérifiez les faits, montants et engagements. Une réponse à un avis est "
        "**publique**. Ne saisissez pas de données personnelles sensibles.",
        icon="🧭",
    )

    with st.sidebar:
        st.header("Paramètres")
        demo_mode = st.toggle("Mode démo (hors-ligne, sans clé API)", value=not config.get_api_key(),
                              help="Rejoue des sorties pré-enregistrées, sans aucun appel API.")
        improve = st.toggle("Produire aussi une version améliorée (auto-critique)", value=False,
                            help="Second appel qui critique puis corrige la première version.")
        if not demo_mode and not config.get_api_key():
            st.warning("Aucune clé API détectée. Activez le mode démo ou renseignez GEMINI_API_KEY.")

        st.divider()
        # --- Les 5+ contraintes paramétrables (§ 4.2) ---
        mode = _selectbox("1. Mode", list(MODE_LABELS), MODE_LABELS, "mode")            # contrainte 1
        lang = _selectbox("2. Langue de sortie", list(LANG_LABELS), LANG_LABELS, "lang")  # contrainte 2
        ton = _selectbox("3. Ton", list(TON_LABELS), TON_LABELS, "ton")                 # contrainte 3
        longueur = _selectbox("4. Longueur", list(LONGUEUR_LABELS), LONGUEUR_LABELS, "longueur")  # contrainte 4

        opts = {"ton": ton, "longueur": longueur}
        if mode == "relance":  # contrainte 5 (propre au mode)
            opts["niveau"] = _selectbox("5. Niveau d'insistance", list(NIVEAU_LABELS), NIVEAU_LABELS, "niveau")
        elif mode == "post":
            opts["plateforme"] = _selectbox("5. Plateforme", list(PLATEFORME_LABELS), PLATEFORME_LABELS, "plateforme")

    placeholder = {
        "email": "Objectif de l'email + éléments factuels (montant, date, référence...).",
        "relance": "Facture/prospect concerné, montant, échéance, contexte.",
        "reponse_avis": "Collez l'avis ou le message du client (note, contenu).",
        "post": "Message à faire passer, événement à annoncer.",
        "reformuler": "Collez le texte à corriger ou clarifier.",
    }.get(mode, "")
    user_text = st.text_area("Votre saisie", height=160, placeholder=placeholder)

    generate = st.button("Générer", type="primary")

    if not generate:
        return

    # ------------------------------------------------------------------ DÉMO
    if demo_mode:
        packed = demo.get_demo_output(mode, lang, opts)
        if packed is None:
            st.error("Aucune sortie de démo disponible pour cette combinaison. "
                     "Choisissez un mode cœur (email, relance, réponse à un avis).")
            return
        st.success("Version générée (mode démo)")
        if packed.get("input"):
            st.caption(f"Saisie rejouée : « {packed['input']} »")
        _render_output(packed["data"], origin=packed.get("origin"))
        # En démo, on montre tout de même le prompt qui SERAIT envoyé (traçabilité).
        _render_prompt_panel(library.build_prompt(mode, lang, user_text or packed.get("input", ""), opts))
        return

    # --------------------------------------------------------------- API réelle
    with st.spinner("Génération en cours..."):
        result, prompt = service.generate_message(mode, lang, user_text, opts)

    if not result.ok:
        # Message clair, jamais de trace Python (§ 4.8).
        st.error(f"❌ {result.error}")
        _render_prompt_panel(prompt)
        return

    st.success("Première version")
    _render_output(result.data)
    _render_prompt_panel(prompt)

    # ----------------------------------------------------- Version améliorée
    if improve:
        with st.spinner("Auto-critique et amélioration..."):
            improved, imp_prompt = service.improve_message(mode, lang, result.data)
        st.divider()
        if not improved.ok:
            st.warning(f"Version améliorée indisponible : {improved.error}")
        else:
            st.success("Version améliorée (après auto-critique)")
            _render_output(improved.data)
            with st.expander("🔍 Voir le prompt d'auto-critique"):
                st.code(imp_prompt["system_instruction"], language=None)
                st.code(imp_prompt["user_content"], language=None)


if __name__ == "__main__":
    main()
