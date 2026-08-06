# ✍️ Atelier d'écriture générative

Assistant de rédaction de **communications professionnelles** pour **freelances
et TPE/PME** : email, relance, réponse à un avis client. Prototype réalisé dans
le cadre du module **T3 — Intelligence Artificielle** (ESGI-REIMS, S3).

> ⚠️ **Usage responsable.** Le contenu est **généré par IA** : il doit être
> **relu et assumé** avant tout envoi ou publication — surtout une réponse à un
> avis, qui est **publique**. Ne saisissez **aucune donnée personnelle
> sensible**. Le modèle peut inventer des faits : **vérifiez montants, dates et
> engagements**.

---

## 1. À quoi ça sert — et pourquoi une application plutôt qu'un chat ?

Un dirigeant de petite structure écrit lui-même, vite, et assume publiquement ce
qu'il envoie. Ce prototype encapsule le **prompt engineering** pour qu'il n'ait
qu'à remplir deux champs. Réponse frontale au « pourquoi ne pas taper directement
dans ChatGPT / Gemini ? », démontrée **par le produit** (§ 2.1 du cahier des
charges) :

1. **Prompts pré-engineerés et reproductibles** : l'utilisateur ne rédige pas de
   prompt ; le résultat ne dépend plus de la formulation.
2. **Garde-fous imposés, pas espérés** : interdiction d'inventer un montant, une
   date, une cause, un engagement — adossée à un champ mesurable `infos_manquantes`.
3. **Format de sortie garanti** par l'API (`response_schema` natif), donc
   affichable et comparable d'un tirage à l'autre.
4. **Paramètres réglés par tâche** : température, longueur, registre.
5. **Résistance à l'injection** : le texte du client est une **donnée**, jamais
   une instruction (délimiteurs XML + consigne d'ignorer les instructions).
6. **Aucune compétence en prompting requise** côté utilisateur.

---

## 2. Installation

Prérequis : **Python 3.10+**.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

### Clé API (optionnelle : le mode démo fonctionne sans)

```bash
cp .env.example .env
# éditez .env et renseignez GEMINI_API_KEY (https://aistudio.google.com/apikey)
```

Le fichier `.env` est ignoré par git (`.gitignore`). **Aucun secret n'est en
dur** dans le code.

---

## 3. Lancement

```bash
streamlit run app.py
```

- **Mode démo** (activé par défaut sans clé) : rejoue des sorties
  pré-enregistrées, **sans aucun appel API**. Chaque sortie indique honnêtement
  son origine (rédigée à la main, ou produite par l'API).
- **Mode réel** : renseignez `GEMINI_API_KEY`, désactivez le toggle démo.

Captures de l'application en fonctionnement (mode démo, réelles) :
`assets/screenshot_demo.png` et `assets/screenshot_prompt.png`.

---

## 4. Vérification hors-ligne (sans clé, sans SDK)

Contrôle la cohérence des prompts, du jeu de tests et du corpus de démo **sans
aucun appel API** — utile pour valider le harnais avant de dépenser du quota :

```bash
python app.py --verifier      # ou : python verifier.py
```

## 5. Tests unitaires (sans dépendance externe)

```bash
python -m unittest discover -s tests -v
```

47 tests couvrent : parsing JSON défensif, validation des entrées, propriétés
structurelles des prompts (délimiteurs / langue / garde-fous), non-régression du
journal (**v5 == prompt de production**), contrôles déterministes, normalisation
du juge.

---

## 6. Évaluation

Rubrique **définie avant** toute mesure (`evaluation/rubric.py`), juge LLM séparé
(`evaluation/judge.py`), contrôles déterministes indépendants
(`evaluation/deterministic.py`).

```bash
# Estimer le coût sans rien envoyer :
python -m evaluation.harness --dry-run --draws 3          # 72 appels
python -m evaluation.replay_journal --dry-run --draws 3   # 120 appels

# Lancer réellement (nécessite GEMINI_API_KEY) :
python -m evaluation.harness --draws 3 --modes core
python -m evaluation.replay_journal --draws 3
```

Les artefacts (JSON + CSV + fichier d'échecs) sont écrits dans `outputs/`. Le
journal de résultats Markdown est régénéré automatiquement.

> **État des mesures** : une campagne réelle a été exécutée le **2026-08-06**
> (`gemini-3.5-flash`, 3 tirages/cas). Résultats chiffrés dans
> `outputs/journal_resultats.md` et `docs/protocole_evaluation.md` §8-10 —
> progression **3.95 → 4.97/5**, langue **9/12 → 12/12**, 2 hallucinations
> analysées. **Aucun chiffre n'est inventé** ; tout provient de `outputs/`.
> Ajoutez `--delay 5` (et `--retries` par défaut) pour tenir un palier gratuit.

---

## 7. Journal des prompts

Cinq paliers `v1 → v5` (`prompts/journal.py`), chacun reconstruit à partir des
mêmes briques que la production, de sorte que **v5 est littéralement le prompt de
l'app** (test de non-régression). Détail et méthode : `docs/journal_prompts.md`.

---

## 8. Structure du dépôt

```
iag/
├── README.md                  ← ce fichier
├── rapport.md / rapport.docx  ← rapport 3 pages (livrable 1)
├── app.py                     ← UI Streamlit (+ raccourci --verifier)
├── config.py                  ← constantes : modèle, température, énumérations
├── llm.py                     ← couche LLM ISOLÉE (une seule fonction generate)
├── service.py                 ← validation + orchestration (génération, auto-critique)
├── verifier.py                ← vérification hors-ligne
├── requirements.txt / .env.example / .gitignore
├── prompts/
│   ├── schemas.py             ← schémas de sortie native (dicts)
│   ├── examples.py            ← few-shot positif + contre-exemple (séparés)
│   ├── library.py             ← construction du prompt par briques + production
│   └── journal.py             ← les 5 paliers d'itération
├── evaluation/
│   ├── rubric.py              ← rubrique 5/3/1 (avant mesures)
│   ├── deterministic.py       ← contrôles objectifs sans API
│   ├── testcases.py           ← jeu de tests FR/EN + injections
│   ├── judge.py               ← juge LLM séparé (biais nommé)
│   ├── harness.py             ← campagne (variance, artefacts, échecs)
│   └── replay_journal.py      ← rejeu automatique des 5 paliers
├── demo/
│   ├── __init__.py            ← chargeur du corpus de démo
│   └── demo_outputs.json      ← sorties pré-enregistrées (origine étiquetée)
├── tests/                     ← tests unittest (stdlib)
├── outputs/                   ← artefacts d'évaluation (générés)
├── assets/                    ← captures d'écran réelles
└── docs/                      ← journal, protocole, analyse critique, oral
```

Ajouts par rapport à l'arborescence recommandée par le sujet (`config.py`,
`llm.py`, `service.py`, `verifier.py`, `evaluation/`, `demo/`, `docs/`) : ils
matérialisent l'**isolation de la couche LLM** (changer de fournisseur ne touche
que `llm.py`) et la **séparation UI / prompts / évaluation** exigée au § 9. Les
noms et emplacements attendus (`app.py`, `requirements.txt`, `prompts/`,
`tests/`, `outputs/`) sont conservés.

---

## 9. Choix techniques (résumé)

| Sujet | Choix | Où |
|---|---|---|
| SDK | `google-genai` (unifié, officiel) — **pas** `google-generativeai` | `llm.py` |
| Modèle | `gemini-3.5-flash`, **une seule constante** | `config.MODEL_ID` |
| Sortie | `response_schema` natif + parsing défensif de secours | `llm.py`, `prompts/schemas.py` |
| Température | par mode, **désactivable** par un drapeau (compromis Gemini 3) | `config.py` |
| Sécurité | `system_instruction` ≠ contenu ; délimiteurs XML ; anti-injection | `prompts/library.py` |
| Secrets | variable d'env / `.env`, jamais en dur | `config.py` |

Détails et justifications : `rapport.md` et `docs/`.

## 10. Ce que le projet ne fait PAS (délibérément)

Pas d'envoi automatique d'emails, pas de mémoire entre sessions, pas de RAG, pas
d'authentification, pas de stockage serveur des saisies. Voir l'analyse critique
(`docs/analyse_critique.md`).
