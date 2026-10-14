# G7 — Préparation des sauvegardes

## Archive F5A7.2

Emplacement vérifié en lecture seule : `/home/sangouman/mobile-money-corpus-backups/20261011T133947Z`.

- État : `COMPLETE`.
- Révision : `0005_workshop_attribution`.
- PostgreSQL : dump custom de 60 629 octets, lisible par `pg_restore` PostgreSQL 16.
- Comptages : users 21, participants 17, utterances 13, recordings 15, transcriptions 1, audit_logs 115.
- MinIO : 30 objets, 5 289 708 octets.
- `manifests/SHA256SUMS` : toutes les entrées `OK`.
- `COMPLETION.SHA256` : le hash correspond à `sha256sum COMPLETE`.
- Rapport de cohérence : 30 objets référencés, 30 capturés, aucun manquant/orphelin.
- Archive incomplète de la première tentative conservée séparément.

## Rétention et indépendance

Le runbook prévoit indicativement 7 sauvegardes journalières, 4 hebdomadaires et 3 mensuelles, avec un RPO pilote de 4 à 24 heures et un RTO de 4 heures. L’emplacement local ci-dessus ne constitue pas une copie indépendante du VPS ; l’opérateur doit vérifier cette copie et sa rétention avant GO.

## Commande préparée, non exécutée

Après gel des écritures et arrêt contrôlé autorisés, la commande prévue est :

```text
BACKUP_APPROVED=YES BACKUP_MODE=offline_app \
BACKUP_ROOT=/var/backups/mobile-money-corpus \
PG_CONTAINER=<production-db-container> \
MINIO_CONTAINER=<production-minio-container> \
MINIO_BUCKET=mobile-money-corpus \
scripts/backup_local.sh
```

La commande n’a pas été exécutée sur la production dans G7. Elle doit être suivie de `SHA256SUMS`, `pg_restore --list`, inventaire MinIO et vérification d’une copie indépendante.
