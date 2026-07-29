# -*- coding: utf-8 -*-
"""Exemples few-shot (§ 6.2, § 6.4).

Deux principes du sujet sont appliqués ici :

1. Les exemples montrent le **texte attendu** (« Objet : … / Corps : … ») et
   NON un objet JSON. En effet, avec `response_schema` natif, dupliquer la
   structure JSON dans le prompt dégrade la qualité (piège documenté § 5.3).

2. Les exemples sont donnés **dans la langue demandée** : un exemple français
   devant une sortie anglaise provoque des fuites de langue, sanctionnées par
   le critère « respect de la langue ».

L'exemple POSITIF et le CONTRE-EXEMPLE sont stockés SÉPARÉMENT : c'est la
condition pour les introduire à deux paliers différents du journal (v4 puis
v5) et mesurer l'apport propre de chacun (§ 6.4).

Le persona est un freelance / TPE-PME : ton professionnel mais accessible, pas
de vocabulaire de grand groupe.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Exemples POSITIFS par mode et par langue.
# ---------------------------------------------------------------------------
POSITIVE_EXAMPLES: dict[str, dict[str, str]] = {
    "email": {
        "fr": (
            "EXEMPLE\n"
            "Demande : envoyer le devis pour la refonte du logo, montant 850 € HT, "
            "validité 30 jours.\n"
            "Sortie attendue :\n"
            "Objet : Votre devis pour la refonte du logo\n"
            "Corps : Bonjour,\n"
            "Merci pour votre confiance. Vous trouverez ci-joint le devis pour la "
            "refonte de votre logo, d'un montant de 850 € HT, valable 30 jours.\n"
            "Je reste disponible si vous souhaitez ajuster le périmètre. Belle "
            "journée,\n"
            "[Votre nom]"
        ),
        "en": (
            "EXAMPLE\n"
            "Request: send the quote for the logo redesign, amount €850 excl. VAT, "
            "valid 30 days.\n"
            "Expected output:\n"
            "Subject: Your quote for the logo redesign\n"
            "Body: Hello,\n"
            "Thank you for reaching out. Please find attached the quote for your "
            "logo redesign, for €850 excl. VAT, valid for 30 days.\n"
            "I'm happy to adjust the scope if needed. Best regards,\n"
            "[Your name]"
        ),
    },
    "relance": {
        "fr": (
            "EXEMPLE\n"
            "Demande : relancer la facture n°2024-042 de 1 200 € échue depuis 15 "
            "jours. Niveau : ferme.\n"
            "Sortie attendue :\n"
            "Objet : Facture n°2024-042 en attente de règlement\n"
            "Corps : Bonjour,\n"
            "Sauf erreur de ma part, la facture n°2024-042 d'un montant de 1 200 €, "
            "échue depuis le 15, reste à ce jour impayée.\n"
            "Pourriez-vous m'indiquer une date de règlement ? Je vous en remercie "
            "par avance.\n"
            "Cordialement,\n"
            "[Votre nom]"
        ),
        "en": (
            "EXAMPLE\n"
            "Request: follow up on invoice #2024-042 for €1,200, overdue by 15 "
            "days. Level: firm.\n"
            "Expected output:\n"
            "Subject: Invoice #2024-042 awaiting payment\n"
            "Body: Hello,\n"
            "Unless I'm mistaken, invoice #2024-042 for €1,200, due on the 15th, "
            "remains unpaid to date.\n"
            "Could you let me know a payment date? Thank you in advance.\n"
            "Best regards,\n"
            "[Your name]"
        ),
    },
    "reponse_avis": {
        "fr": (
            "EXEMPLE\n"
            "Avis : « Très bon accueil et travail soigné, je recommande ! » (5/5)\n"
            "Sortie attendue :\n"
            "Corps : Merci beaucoup pour votre retour, il nous touche. Ce fut un "
            "plaisir de travailler avec vous, et au plaisir de vous revoir.\n"
            "[Votre nom]"
        ),
        "en": (
            "EXAMPLE\n"
            "Review: \"Great welcome and careful work, I recommend!\" (5/5)\n"
            "Expected output:\n"
            "Body: Thank you so much for your feedback, it means a lot. It was a "
            "pleasure working with you, and we hope to see you again.\n"
            "[Your name]"
        ),
    },
    # Modes bonus (hors périmètre d'évaluation) : un exemple minimal suffit.
    "post": {
        "fr": (
            "EXEMPLE\n"
            "Demande : annoncer l'ouverture de nouveaux créneaux le samedi.\n"
            "Sortie attendue :\n"
            "Corps : Bonne nouvelle : j'ouvre désormais des créneaux le samedi ! "
            "Réservez le vôtre, les places partent vite. 📅"
        ),
        "en": (
            "EXAMPLE\n"
            "Request: announce new Saturday openings.\n"
            "Expected output:\n"
            "Body: Good news: I'm now opening Saturday slots! Book yours, spots go "
            "fast. 📅"
        ),
    },
    "reformuler": {
        "fr": (
            "EXEMPLE\n"
            "Texte : « jpe pa venir demain dsl »\n"
            "Sortie attendue :\n"
            "Corps : Bonjour, je suis désolé mais je ne pourrai pas venir demain."
        ),
        "en": (
            "EXAMPLE\n"
            "Text: \"cant make it tmrw sry\"\n"
            "Expected output:\n"
            "Body: Hello, I'm sorry but I won't be able to make it tomorrow."
        ),
    },
}


# ---------------------------------------------------------------------------
# CONTRE-EXEMPLE — uniquement pour reponse_avis (§ 6.4).
# Une mauvaise réponse complète, suivie de ses fautes NOMMÉES, puis de la bonne.
# Nommer les fautes donne au modèle un vocabulaire pour se contrôler, ce que ne
# fait pas une interdiction abstraite.
# ---------------------------------------------------------------------------
CONTRE_EXEMPLE: dict[str, str] = {
    "fr": (
        "CONTRE-EXEMPLE (à NE PAS imiter)\n"
        "Avis négatif : « Commande arrivée cassée et en retard. Très déçu. »\n"
        "Mauvaise réponse :\n"
        "« Bonjour, nous sommes vraiment navrés mais le retard est entièrement de "
        "la faute du transporteur. Nous avons tenté de vous joindre plusieurs fois "
        "sans succès. À titre commercial, nous vous offrons -20 % sur votre "
        "prochaine commande. Contactez-nous en privé. »\n"
        "Fautes commises (nommées) :\n"
        "- REPORT DE FAUTE : accuse le transporteur au lieu d'assumer.\n"
        "- CONTACT INVENTÉ : prétend avoir tenté de joindre le client (fait non "
        "fourni).\n"
        "- REMISE NON AUTORISÉE : offre -20 % que le commerçant n'a jamais décidé.\n"
        "- FUITE VERS LE PRIVÉ SANS RECONNAISSANCE PUBLIQUE : botte en touche.\n"
        "Bonne réponse :\n"
        "« Bonjour, je suis sincèrement désolé que votre commande soit arrivée "
        "abîmée et en retard : ce n'est pas le niveau de service que je vise. Je "
        "veux comprendre ce qui s'est passé et trouver une solution avec vous — "
        "écrivez-moi à [email] et je m'en occupe personnellement. Encore toutes "
        "mes excuses. [Votre nom] »"
    ),
    "en": (
        "COUNTER-EXAMPLE (do NOT imitate)\n"
        "Negative review: \"Order arrived broken and late. Very disappointed.\"\n"
        "Bad response:\n"
        "\"Hello, we're truly sorry but the delay is entirely the carrier's fault. "
        "We tried to reach you several times without success. As a gesture, we're "
        "offering you 20% off your next order. Contact us privately.\"\n"
        "Faults committed (named):\n"
        "- BLAME-SHIFTING: blames the carrier instead of owning it.\n"
        "- INVENTED CONTACT: claims contact attempts (fact not provided).\n"
        "- UNAUTHORIZED DISCOUNT: offers 20% the merchant never decided.\n"
        "- DODGING TO PRIVATE WITHOUT PUBLIC OWNERSHIP.\n"
        "Good response:\n"
        "\"Hello, I'm truly sorry your order arrived damaged and late — that's not "
        "the level of service I aim for. I'd like to understand what happened and "
        "find a solution with you; please email me at [email] and I'll handle it "
        "personally. My sincere apologies. [Your name]\""
    ),
}


def positive_example(mode: str, lang: str) -> str:
    """Retourne l'exemple positif pour (mode, langue), chaîne vide si absent."""
    return POSITIVE_EXAMPLES.get(mode, {}).get(lang, "")


def contre_exemple(lang: str) -> str:
    """Retourne le contre-exemple pour la langue (reponse_avis uniquement)."""
    return CONTRE_EXEMPLE.get(lang, "")
