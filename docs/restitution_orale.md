# Plan de restitution orale — 5 minutes (livrable 7)

Démonstration en direct via le **mode démo** (aucune dépendance externe, aucun
risque de quota ou de modèle retiré pendant la soutenance).

| Temps | Séquence | Contenu | Support |
|---|---|---|---|
| 0:00–0:45 | **Besoin** | Freelance/TPE : communications récurrentes à fort enjeu (devis, relance, réponse à un avis public), peu de temps, le dirigeant assume ce qu'il envoie. | 1 phrase du cahier des charges |
| 0:45–1:15 | **Pourquoi une app, pas un chat** | 6 propriétés : prompts reproductibles, garde-fous imposés, format garanti, réglages par tâche, anti-injection, zéro compétence prompting. | README §1 |
| 1:15–3:00 | **Démonstration** | (1) Réponse à un avis très négatif → montrer le ton assumé et `infos_manquantes`. (2) Panneau « Voir le prompt envoyé » → montrer `system_instruction`, garde-fous, délimiteurs, schéma. (3) Toggle « version améliorée » → auto-critique. (4) Bascule FR→EN sur la même saisie. | App (mode démo) |
| 3:00–4:00 | **Apports / prompt engineering** | Les 5 paliers v1→v5 ; v5 == prompt de prod (testé) ; le contre-exemple nommé ; le tableau naïf vs engineeré. Insister : la qualité vient d'un **processus contrôlé**, pas d'un coup de chance. | `docs/journal_prompts.md` |
| 4:00–4:40 | **Évaluation** | Rubrique 5/3/1 définie avant ; juge séparé + **biais nommé** ; contrôles déterministes qui priment sur le juge ; ≥3 tirages et variance. | `docs/protocole_evaluation.md` |
| 4:40–5:00 | **Limites & prudence** | Hallucinations résiduelles, RGPD (transfert hors UE, offre gratuite), alternative **Mistral**, relecture humaine obligatoire. | `docs/analyse_critique.md` |

## Questions probables et réponses

- **« Pourquoi Gemini et pas Mistral ? »** — Choix pédagogique (sortie structurée
  native, doc claire). Pour un déploiement réel UE, Mistral serait probablement le
  bon choix ; l'architecture (couche LLM isolée) rend la bascule peu coûteuse.
- **« Vos chiffres d'évaluation ? »** — Le harnais est prêt et les tableaux
  décrits ; nous n'avons pas exécuté la campagne payante dans le dépôt rendu et
  **n'inventons aucun chiffre** (`⬜ À REMPLIR` + commande exacte). Honnêteté
  attendue par le sujet lui-même.
- **« La moyenne 4,5/5 du juge prouve-t-elle la qualité ? »** — Non : le juge est
  de la même famille, donc complaisant ; 4,5 signifie « le modèle se juge 4,5 ».
  D'où les contrôles déterministes qui priment.
- **« Comment garantissez-vous que le prompt affiché est bien celui utilisé ? »** —
  Un test unitaire compare v5 au prompt de production ; toute divergence casse la
  CI.
- **« Que se passe-t-il sans clé / si le modèle est retiré ? »** — Mode démo
  hors-ligne ; message d'erreur explicite `MODEL_GONE` ; jamais de trace Python.

## Contributions par membre — ⬜ À COMPLÉTER par le groupe

| Membre | Contributions |
|---|---|
| Membre 1 | ⬜ (ex. couche LLM + prompts + journal) |
| Membre 2 | ⬜ (ex. harnais d'évaluation + juge + tests) |
| Membre 3 | ⬜ (ex. UI Streamlit + mode démo + rapport) |
