# G6 — Registre des risques

| ID | Risque | Niveau | Mesure / condition de clôture |
|---|---|---:|---|
| R1 | `.pyc` versionnés dans la candidate | Critique | Retirer les artefacts par commit dédié, ajouter une règle d’ignore, puis refaire l’inventaire Git |
| R2 | Scanners sécurité non disponibles sur l’hôte G6 | Élevé | Rejouer Bandit, pip-audit et gitleaks dans un environnement outillé et archiver les résultats hors secret |
| R3 | Microphone uniquement simulé | Moyen | Acceptation explicite ou test complémentaire avec périphérique physique représentatif |
| R4 | Compose production dépend d’un `.env` externe | Moyen | Fournir les variables via secret manager et valider la résolution avant déploiement ; ne jamais committer `.env` |
| R5 | Warnings de dépréciation Python | Faible | Ticket technique séparé ; surveiller les upgrades de Python/FastAPI/Starlette |
| R6 | Sauvegarde pré-migration non encore prise | Critique hors production | Exiger la sauvegarde PostgreSQL/MinIO et sa vérification immédiatement avant toute migration réelle |
| R7 | Worktree courant déjà modifié | Moyen | Ne pas l’utiliser pour merger ; conserver les changements et travailler dans une worktree dédiée |

Les risques R1 et R2 empêchent une approbation de merge immédiate. R3 et R5 sont des warnings acceptables seulement avec approbation formelle.
