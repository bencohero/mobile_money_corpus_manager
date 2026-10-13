# G7 — Décision finale

## Décision

**READY_WITH_WARNINGS**

## Justification

La préparation opérationnelle est suffisamment vérifiée sur clone : archive F5A7.2 cohérente, restauration PostgreSQL/MinIO réussie, migration explicite `0005 → 0008`, release `889fd5b` démarrée avec readiness 200, parcours critiques validés et restauration coordonnée mesurée à 24 secondes.

## Réserves obligatoires avant approbation de déploiement

- Les conteneurs PostgreSQL et MinIO du projet de production local sont actuellement actifs ; le conteneur applicatif correspondant est absent. L’état n’est donc pas celui d’une production entièrement arrêtée.
- Une copie indépendante du VPS n’a pas pu être vérifiée depuis cet environnement.
- Le rate limiting a été vérifié par migration, code et contrôles existants, mais aucun test de saturation HTTP à 429 n’a été chronométré dans le dry-run G7.
- Les durées de migration et de démarrage n’ont pas été mesurées séparément ; seule la restauration coordonnée du clone est mesurée à 24 secondes.

Aucune action de production n’a été effectuée. Une autorisation distincte reste requise pour toute exécution.
