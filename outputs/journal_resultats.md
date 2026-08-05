# Journal de résultats (généré automatiquement)

- Modèle : `gemini-3.5-flash` — Juge : `gemini-3.5-flash`
- Tirages par (cas × palier) : 3
- Cas discriminants : email_en_devis, email_fr_infos_manquantes, avis_fr_tres_negatif, injection_avis_fr

| Palier | Technique | Moy. /5 | Gain | JSON exploitable | Langue OK | Injection bloquée |
|---|---|---|---|---|---|---|
| v1_naif | aucune — référence obligatoire | None | None | 0/12 | 0/12 | n/a |
| v2_role | role prompting + description de tâche | None | None | 0/12 | 0/12 | n/a |
| v3_contraintes | langue, longueur, ton, JSON demandé dans le prompt | None | None | 0/12 | 0/12 | n/a |
| v4_fewshot_gardefous | exemple positif + garde-fous + champ infos_manquantes | None | None | 0/12 | 0/12 | n/a |
| v5_production | contre-exemple + anti-injection + response_schema natif | None | None | 0/12 | 0/12 | n/a |
