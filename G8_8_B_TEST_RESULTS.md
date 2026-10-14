# G8.8-B — Résultats de validation

## Résultats

| Contrôle | Résultat |
|---|---|
| Huit tests du contrat restore | PASS (8 cas) |
| Régression `tests/test_backup_local.sh` | PASS |
| Build `Dockerfile.tools` hors production | PASS |
| Restore synthétique schema 1 | PASS |
| Restore synthétique schema 2 | PASS |
| Restore archive historique schema 2 (`/tmp/f5a3-backups/20261011T114424Z`) | PASS |
| Refus cible PostgreSQL de production | PASS |
| Refus endpoint MinIO public/production | PASS (`rc=2`) |

Les restaurations ont utilisé uniquement `g88-a-isolated`, avec PostgreSQL et
MinIO dédiés et volumes dédiés. Aucun volume ou réseau de production n’a été
utilisé par les commandes de test. Les conteneurs de production observés n’ont
pas été arrêtés, redémarrés ou modifiés.

Limite : la vérification `alembic current` et la réconciliation applicative
post-restore restent une étape opérateur à exécuter dans une cible isolée
disposant de l’application correspondante; le script imprime explicitement ce
contrôle à effectuer.
