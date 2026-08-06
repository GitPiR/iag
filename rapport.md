# Atelier d'écriture générative — Rapport de projet

**Module T3 — Intelligence Artificielle · ESGI-REIMS · S3** — Choix 1 (atelier
d'écriture générative). Prototype : assistant de rédaction de communications
professionnelles (email, relance, réponse à un avis) pour freelances et TPE/PME.

> **Usage responsable.** Contenu **généré par IA, à relire et à assumer** avant
> envoi/publication (une réponse à un avis est **publique**). Ne pas saisir de
> données personnelles sensibles.

## Résumé (≤ 10 lignes)

Nous avons conçu un assistant de rédaction de communications professionnelles
(email, relance, réponse à un avis) pour freelances et TPE, sous forme d'une
**application** — et non d'un chat — afin d'encapsuler le prompt engineering :
prompts pré-engineerés, garde-fous imposés, format garanti, résistance à
l'injection. Le cœur (bilingue FR/EN) repose sur cinq versions de prompt figées
(`v1_naif` → `v5_production`, où **v5 est littéralement le prompt de l'app**,
vérifié par test). Une campagne d'évaluation réelle (juge LLM séparé + contrôles
déterministes, 3 tirages/cas) **mesure** l'apport du prompt engineering :
qualité **3.95 → 4.97/5** du naïf à la production, respect de la langue **9/12 →
12/12**. Deux résultats négatifs sont assumés (anti-injection et schéma sans gain
mesuré sur cet échantillon) et deux hallucinations analysées. Limites, RGPD et
alternative Mistral sont documentés.

## 0. État d'avancement — ce qui est vérifié

| Élément | État | Vérification |
|---|---|---|
| Prototype Streamlit (3 modes cœur, bilingue, démo, auto-critique) | **Exécuté** | captures réelles + app lancée |
| Couche LLM isolée, gestion d'erreurs, parsing défensif | **Codé + testé** | `tests/` (47 tests OK) |
| 5 paliers de prompt, v5 == production | **Codé + testé** | `tests/test_journal.py` |
| Vérification hors-ligne | **Exécuté** | `python verifier.py` → « TOUT EST COHÉRENT » |
| Campagne d'évaluation chiffrée | **Exécutée (2026-08-06)** | `outputs/campagne_20260806_094742.csv`, `journal_resultats.md` — chiffres réels, non inventés |

**Hypothèses** : (1) modèle `gemini-3.5-flash` (constante unique, à reconfirmer
au catalogue) ; (2) corpus fictif ; (3) évaluation par juge LLM, avec son biais
de complaisance assumé (même famille de modèle).

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

**Résultats (campagne réelle du 2026-08-06, `gemini-3.5-flash`)** :
- **Progression du prompt** (rejeu des 5 paliers, même juge) : moyenne
  **3.95 → 4.42 → 4.67 → 4.97 → 4.97/5**. Gain le plus fort : le **rôle** (+0.47).
- **Respect de la langue** : **9/12** au naïf → **12/12** dès l'ajout de la
  consigne de langue (v3). C'est la brique la plus nettement démontrée.
- **Comparaison naïf/engineeré** : +1.02 point (3.95 → 4.97), langue 9/12 → 12/12,
  format garanti seulement en engineeré.
- **Deux résultats négatifs assumés** : anti-injection (6/6 bloquées **mais** le
  naïf bloquait déjà — pas de gain mesuré) et JSON exploitable (12/12 partout, le
  parseur défensif suffit) ; le schéma natif apporte une **garantie**, pas un gain
  chiffré ici.
- **Honnêteté** : 35/36 tirages réussis, **2 hallucinations analysées** (une
  franche notée 1/5 sur `email_en_devis`, une implicature « comme convenu » notée
  3/5), variance forte sur ce cas (σ=1.81) illustrant l'utilité des ≥3 tirages.

Détail chiffré et fiches d'échec : `docs/protocole_evaluation.md` §8-10.
Rejouable : `python -m evaluation.harness --draws 3 --modes core`. **Aucun chiffre
n'est inventé** ; tous proviennent de `outputs/`.

## 6. Limites, risques, responsabilité (résumé — détail `docs/analyse_critique.md`)

- **Hallucinations** : franches contraintes/mesurées ; **résiduelles subtiles**
  (implicatures « comme convenu ») non éliminées → relecture humaine.
- **Biais** : corporate, culturel anglophone, apaisement (remises spontanées) —
  **contraints, non corrigés**.
- **Sécurité** : anti-injection implémentée ; efficacité **mesurée** = 6/6
  injections bloquées, mais gain non prouvé (le naïf bloquait déjà) → cas
  d'injection plus agressif à ajouter.
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
cœur).

**Contributions par membre** :
- **Pierre Postal** : couche LLM (`llm.py`, isolation fournisseur, gestion
  d'erreurs) + bibliothèque de prompts (`prompts/`) + journal des 5 itérations.
- **Fabien Tavernier** : harnais d'évaluation (`evaluation/`, rubrique, campagne,
  variance, artefacts) + juge LLM séparé + tests unitaires.
- **Fabien Lubin** : interface Streamlit (`app.py`) + mode démo hors-ligne +
  rédaction du rapport et des documents (`docs/`).
