# G8.8-A — Matrice de compatibilité

| Format | Producteur | Entrée PostgreSQL | Entrée MinIO | Empreintes | Résultat |
|---|---|---|---|---|---|
| Schema 1 | `scripts/backup.sh` | `postgres.dump` | `minio/` | `SHA256SUMS`, `MANIFEST.SHA256` | PASS |
| Schema 2 | `scripts/backup_local.sh` | `postgres/corpus.dump` | `minio/<bucket>/` | `manifests/SHA256SUMS`, `COMPLETION.SHA256` | PASS |
| Historique validé | archive synthétique 2026-10-11 | `postgres/corpus.dump` | `minio/mobile-money-corpus/` | schema 2 | PASS |
| Ancien restore ambigu | ancien `restore.sh` | racine seulement | racine seulement | manifest implicite | REFUSÉ / remplacé |

Le consommateur accepte explicitement les schemas 1 et 2, et aucun autre.

La restauration historique a retrouvé Alembic `0005_workshop_attribution`,
ce qui est attendu pour cette archive ancienne ; les fixtures actuelles ont
retrouvé `0008_rate_limit_buckets`.
