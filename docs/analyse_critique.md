# Analyse critique, limites et responsabilité (critère 5)

## 1. Hallucinations

- **Formes franches** (montant, date, référence inventés) : contraintes par les
  garde-fous et rendues **mesurables** par `infos_manquantes`, mais **non
  supprimées** — le modèle reste génératif.
- **Formes résiduelles subtiles**, qui passent sous le radar d'un juge
  automatique parce qu'elles ne sont ni vraies ni fausses mais ajoutent une
  **implicature** : « comme convenu » sans accord fourni, un délai indicatif
  transformé en engagement ferme, « je vous recontacte lundi » non demandé. La
  rubrique note ces cas **3 en exactitude** (implicature risquée), pas 1 : c'est
  volontaire, mais cela signifie qu'un juge indulgent peut les laisser passer.
  **Seule vraie parade : la relecture humaine**, rappelée dans l'UI.

## 2. Biais

- **Registre corporate** par défaut : contraint par le rôle et le contre-exemple,
  jamais éliminé.
- **Biais culturel anglophone** : les conventions de politesse françaises
  (formules d'appel/clôture) sont moins bien tenues que les anglaises ; d'où la
  consigne de langue explicite **et** son rappel en fin de message.
- **Biais d'apaisement** : le modèle veut satisfaire, d'où les remises spontanées
  et excuses excessives face à un avis négatif. Contraint par le garde-fou « aucun
  engagement non fourni » et le contre-exemple. **Contraint, non corrigé.**

## 3. Incohérences, répétitions, contenu stéréotypé (vigilance Choix 1)

Répétitions (« je reste à votre disposition » systématique), tournures
stéréotypées, absence de contrôle fin sur le ton : contrôlés par le ton décrit en
comportement observable et la fourchette de longueur déterministe, mais un juge
LLM détecte mal la **redondance inter-tirages**. Piste : un contrôle déterministe
de similarité entre tirages (non implémenté).

## 4. Sécurité — injection de prompt

Mesures **implémentées** : séparation `system_instruction` / contenu (seule
séparation structurelle offerte par l'API), délimiteurs XML, consigne explicite
d'ignorer les instructions du texte fourni, règle homologue côté juge. Efficacité
**mesurée**, pas postulée : cas d'injection dédiés + détection déterministe du
marqueur (`deterministic.check_injection`). Résultat réel (§8.2) : **6/6
injections bloquées** — mais le rejeu montre que le **palier naïf bloquait déjà**
(le modèle résiste seul), donc le gain des délimiteurs n'est **pas prouvé** sur
ce cas. Limite assumée : une injection plus sophistiquée (multilingue, encodée)
n'est pas couverte ; c'est la première piste d'enrichissement du jeu de tests.

## 5. Confidentialité et RGPD

- Un freelance qui colle un avis transmet des **données personnelles** à un tiers
  (Google) et en est **responsable de traitement**.
- Sur l'offre **gratuite**, les contenus envoyés **peuvent être utilisés pour
  améliorer les modèles**. **Transfert hors UE** (États-Unis).
- **Mitigations implémentées** : avertissement en tête d'UI et de README ; **aucune
  journalisation**, **aucun stockage serveur** des saisies ; jeu de tests et
  corpus de démo **entièrement fictifs**.
- **Recommandée** : **anonymiser** avant de coller (retirer noms, numéros de
  facture réels).

## 6. Droits

Statut du contenu généré incertain ; risque d'**imitation trop proche** d'une
œuvre protégée (moindre ici, textes courts et fonctionnels) ; l'utilisateur doit
**assumer la paternité** du texte envoyé. L'UI le rappelle.

## 7. Souveraineté — l'alternative Mistral

**Mistral** aurait été un choix alternatif sérieux : **hébergement UE**, cadre
RGPD plus simple, très bon en français. Pour un déploiement réel auprès de TPE
françaises manipulant de **vraies** données clients, ce serait probablement le
bon choix. L'**isolation de la couche LLM** (`llm.py`, une seule fonction) rend
ce changement peu coûteux : c'était un **objectif d'architecture**, pas un hasard.

## 8. Coût, quotas, dépendance fournisseur

- Coût d'une campagne cœur (3 tirages) : **72 appels API** ; rejeu du journal :
  **120 appels**. Ordres de grandeur faibles, mais non nuls.
- **Quota gratuit rédhibitoire, constaté en pratique** : sur le palier gratuit,
  `gemini-3.5-flash` est plafonné à **5 requêtes/min et 20 requêtes/JOUR** (RPD).
  Une seule campagne (192 appels) est donc **impossible gratuitement** — nous
  avons dû ajouter throttling + retry (429/5xx) puis activer la **facturation**
  (coût réel < 0,10 € pour toute la campagne). C'est une illustration directe de
  la **dépendance fournisseur** : sans budget, le protocole n'est pas exécutable.
- **Dépendance forte** : les modèles **Gemini 1.5 et 2.0 ont été réellement
  coupés** (404). Un identifiant codé en dur **cesse de fonctionner sans
  prévenir** → d'où la **constante unique** commentée et le message d'erreur
  `MODEL_GONE` explicite.

## 9. Reproductibilité — classée par gravité

1. **Non-déterminisme du modèle** (traité) : ≥3 tirages, variance rapportée,
   seed pour le juge.
2. **Dérive / retrait du modèle** (partiellement traité) : constante unique +
   erreur explicite ; on ne peut pas empêcher Google de changer le catalogue.
3. **Biais du juge** (nommé, non traité) : juge de la même famille ; contre-mesure
   (autre famille) documentée mais non implémentée.

## 10. Traçabilité

Prompts et versions : `prompts/` (journal figé, testé). Paramètres : `config.py`
+ panneau « Voir le prompt envoyé » de l'UI. Sorties et notes :
`outputs/*.json|csv`. Corrections humaines : le champ `infos_manquantes` et la
version améliorée (auto-critique) matérialisent l'intervention.

## 11. Ce que le projet ne fait pas (délibérément)

Pas d'**envoi automatique** (l'humain garde la main), pas de **mémoire** entre
sessions, pas de **RAG**, pas d'**authentification**, pas de **stockage serveur**.
Ces absences sont des **choix de périmètre réaliste**, pas des oublis.

## 12. Pistes d'amélioration (par rapport bénéfice/coût décroissant)

1. **Juge d'une autre famille** (Mistral/Claude) pour casser la complaisance —
   fort bénéfice, coût faible (couche isolée).
2. **Contrôle déterministe de similarité inter-tirages** — détecte la redondance
   que le juge rate.
3. **Anonymisation assistée** avant envoi — bénéfice RGPD direct.
4. **Bascule fournisseur Mistral** pour un vrai déploiement UE.
5. Enrichissement du jeu d'injections (encodées, multilingues).
