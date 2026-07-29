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

## Résultats du rejeu — ⬜ À REMPLIR

À produire par la commande ci-dessus. Colonnes attendues (lecture : la moyenne
doit monter de v1 à v5 ; le taux de JSON exploitable doit bondir entre v3 et v5 ;
l'injection ne doit être bloquée qu'à partir de v5) :

| Palier | Moy. /5 | Gain vs préc. | JSON exploitable | Langue OK | Injection bloquée |
|---|---|---|---|---|---|
| v1_naif | ⬜ | — | ⬜ | ⬜ | ⬜ |
| v2_role | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| v3_contraintes | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| v4_fewshot_gardefous | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| v5_production | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

**Comment lire** : un gain concentré sur un seul palier isole la brique
responsable. Si v3 affiche un faible taux de JSON exploitable et v5 un taux
élevé, le chiffre justifie à lui seul le passage au schéma natif — et donne au
parsing défensif une origine datée, non un statut de précaution théorique.
