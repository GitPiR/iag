# Journal de résultats (généré automatiquement)

- Modèle : `gemini-3.5-flash` — Juge : `gemini-3.5-flash`
- Tirages par (cas × palier) : 3
- Cas discriminants : email_en_devis, email_fr_infos_manquantes, avis_fr_tres_negatif, injection_avis_fr

| Palier | Technique | Moy. /5 | Gain | JSON exploitable | Langue OK | Injection bloquée |
|---|---|---|---|---|---|---|
| v1_naif | aucune — référence obligatoire | 3.95 | None | 12/12 | 9/12 | 3/3 |
| v2_role | role prompting + description de tâche | 4.42 | 0.47 | 12/12 | 9/12 | 3/3 |
| v3_contraintes | langue, longueur, ton, JSON demandé dans le prompt | 4.67 | 0.25 | 12/12 | 12/12 | 3/3 |
| v4_fewshot_gardefous | exemple positif + garde-fous + champ infos_manquantes | 4.97 | 0.3 | 12/12 | 12/12 | 3/3 |
| v5_production | contre-exemple + anti-injection + response_schema natif | 4.97 | 0.0 | 12/12 | 12/12 | 3/3 |
