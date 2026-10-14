# G1 — Décision finale

## Décision : `BLOCKED`

Le plan de reprise est défini, mais l’intégration ne peut pas être déclarée prête immédiatement.

Motifs bloquants :

1. `main` est au schéma `0005`, tandis que la branche de remédiation attend `0006`–`0008`.
2. La compatibilité de ces migrations avec le clone restauré F5A7.2 n’a pas encore été démontrée dans ce ticket.
3. Les lots A–F sont fortement couplés ; un cherry-pick partiel pourrait produire un modèle, une API ou un schéma incohérent.
4. Le script de sauvegarde de `main` et celui de la branche courante doivent être comparés et validés séparément avant de retenir une version.

Aucune donnée PostgreSQL ou MinIO, archive, branche, worktree ou service de production n’a été modifié. Les changements locaux préexistants restent conservés.

## Passage à `READY_FOR_INTEGRATION`

La décision pourra être réévaluée après :

- validation des migrations `0006` à `0008` sur un clone de F5A7.2 ;
- réussite des tests des lots 1 à 5 et des scans de sécurité ;
- revue du diff exact contre `main` ;
- validation d’un lot d’intégration et de son retour arrière ;
- approbation explicite avant tout merge ou cherry-pick.

