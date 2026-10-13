# G8.2 — Décision finale

## `BLOCKED`

L’intégration Git et les tests du correctif sont validés. Le gel des écritures est attesté par contrôles indépendants avec `active_writes=0`. La sauvegarde de production ne peut toutefois pas être créée tant que le client MinIO approuvé et son SHA-256 ne sont pas disponibles.

Le statut ne peut donc pas être `AWAITING_KUBUNTU_BACKUP`, qui exige une archive locale complète et vérifiée. Aucun transfert, aucune migration, aucun redémarrage, aucun push distant, aucune suppression de volume et aucune ouverture publique n’ont été effectués.
