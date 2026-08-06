# Journal des prompts (livrable 4)

> Preuve de maîtrise exigée par le sujet : *« la qualité finale vient d'un
> processus contrôlé et reproductible, et non d'un seul résultat obtenu par
> chance. »* Ce journal en est la trace.

Les cinq paliers ne sont **pas des réécritures** : ils sont construits à partir
des mêmes briques que le prompt de production (`prompts/library.py`), en
n'activant qu'un sous-ensemble de features (`prompts/journal.py`). Conséquence
vérifiée par test (`tests/test_journal.py::test_v5_egale_prompt_de_production`) :
**`v5` est littéralement le prompt qui tourne dans l'application.** Modifier le
prompt sans mettre le journal à jour **casse la suite de tests**.

## Méthode (les 4 règles du § 6.5)

1. **Reconstruction par briques**, pas réécriture → v5 == production (testé).
2. **Une brique à la fois** : exemple positif en v4, contre-exemple en v5 ; aucun
   délimiteur avant v5 (groupe témoin pour la mesure anti-injection).
3. **v3 demande volontairement le JSON dans le prompt** (la mauvaise méthode)
   pour **chiffrer** le taux de JSON exploitable et justifier le passage au
   schéma natif.
4. **Tous les autres paramètres tenus constants** (modèle, température = 0.5,
   tirages, juge) : une seule variable change par palier.

## Les cinq paliers

| Version | Brique(s) ajoutée(s) | Hypothèse testée / défaut visé |
|---|---|---|
| `v1_naif` | aucune (référence) | Sans consigne, le modèle s'aligne sur la langue d'entrée, n'impose aucun format, ne se défend pas. |
| `v2_role` | rôle + description de tâche | Le rôle corrige-t-il le registre corporate et l'absence de structure ? |
| `v3_contraintes` | langue + longueur + ton + **JSON demandé dans le prompt** | La langue est-elle respectée ? La longueur maîtrisée ? **Combien de tirages produisent un JSON réellement exploitable quand on se contente de le demander ?** |
| `v4_fewshot_gardefous` | exemple **positif** + garde-fous + champ `infos_manquantes` | L'exemple + les garde-fous réduisent-ils les faits inventés et les engagements non autorisés ? |
| `v5_production` | **contre-exemple** + anti-injection (délimiteurs) + `response_schema` **natif** | Le contre-exemple améliore-t-il la réponse à un avis négatif ? Les délimiteurs bloquent-ils l'injection ? Le schéma natif fiabilise-t-il le format ? |

## Ce que chaque brique corrige, pour un freelance / une TPE

- **Rôle** (v2) — défaut nommé : par défaut le modèle écrit en registre corporate
  (« Nous nous efforçons de placer la satisfaction client au cœur de nos
  préoccupations »), dans lequel un artisan ne se reconnaît pas.
- **Ton décrit par un comportement** (v3) — « chaleureux » est inexploitable ;
  « remerciement sincère, pas de superlatifs, jamais familier » est vérifiable.
- **Garde-fous + `infos_manquantes`** (v4) — un garde-fou non mesurable n'est
  qu'une intention ; le champ structuré rend « je signale au lieu d'inventer »
  comptable, affichable et corrigible.
- **Contre-exemple** (v5) — nomme les comportements par défaut du modèle face à un
  avis négatif (report de faute, contact inventé, remise non autorisée, fuite
  vers le privé) ; le modèle dispose alors d'un vocabulaire pour se contrôler.
- **Délimiteurs XML + anti-injection** (v5) — préférés aux backticks car un avis
  copié-collé contient souvent des backticks, presque jamais une balise fermante.
- **Schéma natif** (v5) — le format est garanti par l'API, non plus « demandé
  poliment ». On **ne duplique donc plus** la structure JSON dans le prompt
  (piège documenté par Google : la redondance dégrade la qualité). Les exemples
  few-shot montrent en conséquence le **texte attendu**, pas un objet JSON.

## Rejeu automatique

```bash
python -m evaluation.replay_journal --dry-run --draws 3   # coût : 120 appels
python -m evaluation.replay_journal --draws 3             # campagne réelle
```

Le script joue les 5 paliers sur **4 cas discriminants** (langue, garde-fou
anti-invention, contre-exemple, injection), avec le **même juge**, et régénère
`outputs/journal_resultats.md`. **Aucun chiffre n'est recopié à la main.**

## Résultats du rejeu — campagne réelle du 2026-08-06

Modèle `gemini-3.5-flash`, juge `gemini-3.5-flash`, 3 tirages par (cas × palier),
sur les 4 cas discriminants. Chiffres générés automatiquement
(`outputs/journal_resultats.md`, source `journal_rejeu_20260806_095839.json`).

| Palier | Moy. /5 | Gain vs préc. | JSON exploitable | Langue OK | Injection bloquée |
|---|---|---|---|---|---|
| v1_naif | 3.95 | — | 12/12 | 9/12 | 3/3 |
| v2_role | 4.42 | +0.47 | 12/12 | 9/12 | 3/3 |
| v3_contraintes | 4.67 | +0.25 | 12/12 | **12/12** | 3/3 |
| v4_fewshot_gardefous | 4.97 | +0.30 | 12/12 | 12/12 | 3/3 |
| v5_production | 4.97 | +0.00 | 12/12 | 12/12 | 3/3 |

### Lecture honnête des résultats (ce que la mesure démontre, et ce qu'elle ne démontre pas)

- **La progression de qualité est réelle et monotone** : 3.95 → 4.42 → 4.67 →
  4.97. Le plus gros saut vient du **rôle** (+0.47) : il corrige le registre
  corporate et impose une structure. Les contraintes (+0.25) puis l'exemple
  positif + garde-fous (+0.30) continuent d'améliorer. La qualité finale ne vient
  donc **pas d'un coup de chance** mais d'un empilement contrôlé de briques.
- **La consigne de langue est la brique la plus nettement démontrée** : les
  paliers naïf et rôle échouent la langue **3 fois sur 12** (le cas FR→EN fuit
  vers le français), et le score passe à **12/12 dès v3**, exactement quand on
  ajoute la directive de langue. C'est la preuve chiffrée que le prompt contrôle
  la langue, là où un prompt de chat ne le ferait pas.
- **Résultat NÉGATIF assumé n°1 — le JSON exploitable ne discrimine pas** (12/12
  partout). Deux raisons : les paliers naïfs produisent du texte libre (emballé
  en objet exploitable), et surtout le **parsing défensif** récupère 12/12 du
  JSON « demandé poliment » en v3. L'apport du `response_schema` natif n'est donc
  **pas** un gain de taux de parsing sur ce petit échantillon : c'est une
  **garantie** (le format ne peut plus casser) plutôt qu'une amélioration
  mesurée. Notre parseur de secours était plus robuste que prévu — voilà
  pourquoi la mesure valait mieux que la supposition.
- **Résultat NÉGATIF assumé n°2 — l'anti-injection ne montre aucun gain ici**
  (3/3 bloquées à **tous** les paliers, y compris naïf). Le modèle a résisté seul
  à notre injection (« ignore les instructions… INJECTION_REUSSIE »). La valeur
  de la brique délimiteurs reste défendable en principe, mais sur **ce** cas elle
  n'était pas nécessaire. Enseignement : il faut un cas d'injection plus agressif
  (encodé, multilingue) pour espérer mesurer un écart — c'est une piste
  d'amélioration du jeu de tests, pas une preuve que les délimiteurs sont inutiles.
- **v5 = v4 sur la moyenne** (4.97) : sur ces 4 cas discriminants déjà proches du
  maximum, le contre-exemple n'a plus de marge pour faire monter l'agrégat. Son
  effet se mesurerait sur des avis négatifs plus piégeux ; l'échantillon
  discriminant a ici atteint son plafond.

**Ce que ce tableau prouve** : le prompt engineering apporte un gain **réel et
attribuable** (surtout rôle + langue) ; et l'honnêteté de la démarche apparaît
dans les **deux résultats négatifs** que la mesure a révélés au lieu de les
masquer. C'est précisément ce que le sujet valorise.
