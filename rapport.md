# Atelier d'écriture générative — Rapport de projet

**Module T3 — Intelligence Artificielle · ESGI-REIMS · S3** — Choix 1 (atelier
d'écriture générative). Prototype : assistant de rédaction de communications
professionnelles (email, relance, réponse à un avis) pour freelances et TPE/PME.

> **Usage responsable.** Contenu **généré par IA, à relire et à assumer** avant
> envoi/publication (une réponse à un avis est **publique**). Ne pas saisir de
> données personnelles sensibles.

## 0. État d'avancement — ce qui est vérifié vs ce qui ne l'est pas

| Élément | État | Vérification |
|---|---|---|
| Prototype Streamlit (3 modes cœur, bilingue, démo, auto-critique) | **Exécuté** | `assets/screenshot_demo.png`, `screenshot_prompt.png` (captures réelles) |
| Couche LLM isolée, gestion d'erreurs, parsing défensif | **Codé + testé** | `tests/` (47 tests OK) |
| 5 paliers de prompt, v5 == production | **Codé + testé** | `tests/test_journal.py` |
| Vérification hors-ligne | **Exécuté** | `python verifier.py` → « TOUT EST COHÉRENT » |
| Campagne d'évaluation chiffrée | **Non exécutée** (pas de clé) | Tableaux `⬜ À REMPLIR` + commande exacte ; **aucun chiffre inventé** |

**Hypothèses** : (1) faits techniques du § 5 du cahier des charges tenus pour à
jour (SDK `google-genai`, modèle `gemini-3.5-flash`, familles 1.5/2.0 coupées) ;
(2) corpus fictif ; (3) évaluation par juge LLM, avec son biais assumé.

## 1. Cahier des charges (6 points)

1. **Problème** : rédiger vite une communication professionnelle juste et sobre
   sans savoir prompter.
2. **Utilisateur** : freelance / dirigeant de TPE-PME, écrit lui-même, assume
   publiquement ses envois.
3. **Entrées** : mode, langue, ton, longueur, contrainte propre au mode ; texte
   ou éléments factuels.
4. **Sorties** : objet (si email/relance) + corps + `infos_manquantes`, au format
   JSON structuré natif, affiché dans l'UI.
5. **Contraintes** : bilingue FR/EN, ton contrôlé, sécurité (anti-injection),
   données non stockées, coût maîtrisé, **reproductibilité**.
6. **Critères** (définis **avant** mesure) : pertinence, exactitude, ton, langue,
   format, longueur — ancrés 5/3/1, exactitude prioritaire.

## 2. Architecture et choix techniques

**Modules séparés** (testables sans Streamlit) : `config` (constantes) ·
`llm` (**couche LLM isolée**, une seule fonction `generate` qui **ne lève
jamais** et renvoie un résultat uniforme) · `prompts/` (schémas, exemples,
`library` par briques, `journal`) · `service` (validation + orchestration) ·
`evaluation/` · `demo/` · `verifier`.

- **SDK** `google-genai` (unifié), **pas** `google-generativeai` (déprécié) ;
  **import paresseux** (tests/démo sans SDK ni clé).
- **Modèle** `gemini-3.5-flash` dans **une seule constante** commentée (les
  catalogues changent ; 1.5/2.0 renvoient des 404).
- **Sortie structurée native** (`response_schema` en dicts, pas Pydantic) +
  **parsing JSON défensif** de secours ; **pas d'exemple JSON dupliqué** dans le
  prompt (piège documenté) → les few-shot montrent le **texte** attendu.
- **Température par mode**, **désactivable** par un drapeau unique : compromis
  Gemini 3 (temp=1.0 recommandée sur modèles à raisonnement) transformé en
  **expérience mesurable** plutôt qu'en pari silencieux.
- **Secrets** hors code (`GEMINI_API_KEY` / `.env`), `.env.example` fourni.
- **Gestion d'erreurs** sur tous les chemins faillibles (clé/SDK absents, clé
  refusée, quota, modèle retiré, serveur, réseau, réponse vide, hors-format,
  champ manquant) → **message clair, jamais de trace Python**.

**Isolation fournisseur** assumée : basculer vers **Mistral** (hébergement UE) ne
toucherait que `llm.py`.

## 3. Prompt engineering (le cœur)

Architecture : `system_instruction` = rôle + langue + tâche + ton/niveau +
longueur + garde-fous + `infos_manquantes` + sécurité + exemples ; `contenu` =
`<donnees_utilisateur>…</donnees_utilisateur>` + **rappel de langue en fin**.
Séparation justifiée par **sécurité** (le texte d'un tiers n'a pas le statut de
la consigne développeur), **réutilisation**, **évaluation**.

Techniques et défaut corrigé : **rôle** (registre corporate → registre artisan),
**ton décrit par comportement** (« pas de superlatifs, jamais familier »),
**délimiteurs XML** (un avis contient des backticks, pas de balise fermante),
**garde-fous adossés au champ mesurable `infos_manquantes`** (un garde-fou non
mesurable n'est qu'une intention), **contre-exemple nommé** pour l'avis négatif
(report de faute, contact inventé, remise non autorisée), **anti-injection**.

**Journal de 5 itérations** (`v1_naif` → `v5_production`), reconstruites par
briques de sorte que **`v5` est le prompt de production** (test de
non-régression). Une brique par palier ; v3 demande volontairement le JSON dans
le prompt (mauvaise méthode) pour **chiffrer** le taux de JSON exploitable et
justifier le schéma natif. Détail : `docs/journal_prompts.md`.

## 4. Prototype

UI Streamlit minimale : mode, langue, ton, longueur, contrainte propre au mode
(**≥ 5 contraintes**), saisie, génération, **panneau « Voir le prompt envoyé »**
(traçabilité complète : modèle, température, `system_instruction`, contenu,
schéma), **mode démo hors-ligne** (origine de chaque sortie étiquetée
honnêtement), **version améliorée** par auto-critique, bouton copier, gestion des
entrées invalides. Vérifié en fonctionnement (captures réelles jointes).

## 5. Évaluation

Rubrique **définie avant** (5/3/1, exactitude prioritaire) ; **jeu de 12 cas**
FR/EN avec avis très négatif/agressif, relance délicate, info manquante, fait
invérifiable, **2 injections** ; **juge LLM séparé** (biais de complaisance
**nommé**) ; **contrôles déterministes** (langue, longueur, format, injection)
qui **priment** sur le juge en cas de désaccord ; **≥ 3 tirages**, min/max/moyenne/
écart-type ; **artefacts JSON/CSV** rejouables ; **détection automatique des
échecs**. Protocole complet : `docs/protocole_evaluation.md`.

**Résultats** : ⬜ **À REMPLIR** — la campagne (72 appels, cœur, 3 tirages) n'a
pas été exécutée faute de clé. Commande : `python -m evaluation.harness --draws 3
--modes core`. **Aucun chiffre n'est inventé** (fraude que ce projet enseigne à
éviter). Deux fiches d'échec sont réservées et seront remplies depuis
`outputs/echecs_*.json`.

## 6. Limites, risques, responsabilité (résumé — détail `docs/analyse_critique.md`)

- **Hallucinations** : franches contraintes/mesurées ; **résiduelles subtiles**
  (implicatures « comme convenu ») non éliminées → relecture humaine.
- **Biais** : corporate, culturel anglophone, apaisement (remises spontanées) —
  **contraints, non corrigés**.
- **Sécurité** : anti-injection implémentée, efficacité **mesurée** (⬜).
- **RGPD** : données personnelles transmises hors UE ; offre gratuite = données
  possiblement réutilisées ; mitigations (aucun stockage, corpus fictif,
  avertissements) + anonymisation recommandée. **Mistral** = meilleure option UE.
- **Dépendance fournisseur** : modèles réellement retirés → constante unique +
  erreur explicite.
- **Reproductibilité** : non-déterminisme (traité), dérive modèle (partiel), biais
  juge (nommé, non traité).
- **Hors périmètre délibéré** : envoi auto, mémoire, RAG, auth, stockage serveur.

## 7. Périmètre et travail d'équipe

Modes **cœur évalués** : email, relance, réponse à un avis. Modes **bonus
explicitement exclus** de l'évaluation : post, reformuler (ne dégradent pas le
cœur). **Contributions par membre** : ⬜ à compléter (voir
`docs/restitution_orale.md`).
