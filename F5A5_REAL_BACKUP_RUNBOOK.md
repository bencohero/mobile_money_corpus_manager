# F.5A.5 — Runbook de sauvegarde réelle préparée

Ce runbook est préparatoire. Il ne crée pas `/var/backups/mobile-money-corpus/`
et ne lance aucune sauvegarde réelle.

## Autorisations préalables

Obtenir séparément l’autorisation de sauvegarder la production et l’attestation
`OFFLINE_WRITERS_ATTESTED=YES`. Ne pas définir `WRITE_FREEZE_ATTESTED` pour ce
mode. Confirmer que l’application est déjà arrêtée ; ne pas la redémarrer.

## Variables à renseigner sans les journaliser

```bash
BACKUP_ROOT=/var/backups/mobile-money-corpus
BACKUP_MODE=offline_app
BACKUP_TARGET_ID=mobile_money_corpus_manager_v0_1
BACKUP_ID="$(date -u +%Y%m%dT%H%M%SZ)"
PG_CONTAINER=mobile_money_corpus_manager_v0_1-db-1
MINIO_CONTAINER=mobile_money_corpus_manager_v0_1-minio-1
APP_CONTAINER=mobile_money_corpus_manager_v0_1-app-1
MINIO_BUCKET=mobile-money-corpus
MINIO_MC_IMAGE=quay.io/minio/aistor/mc@sha256:23511e340cbabf07e6a8b53f9c434975708f22f3c047d6beeddc17bf1a5aed88
EXPECTED_PG_IMAGE_ID=sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685
EXPECTED_MINIO_IMAGE_ID=sha256:a1ea29fa28355559ef137d71fc570e508a214ec84ff8083e39bc5428980b015e
BACKUP_CONFIRM=PRODUCTION_BACKUP_AUTHORIZED
OFFLINE_WRITERS_ATTESTED=YES
```

## Capture

Après un prévol PASS et approbation explicite :

```bash
export BACKUP_ROOT BACKUP_MODE BACKUP_TARGET_ID BACKUP_ID
export PG_CONTAINER MINIO_CONTAINER APP_CONTAINER MINIO_BUCKET MINIO_MC_IMAGE
export EXPECTED_PG_IMAGE_ID EXPECTED_MINIO_IMAGE_ID BACKUP_CONFIRM OFFLINE_WRITERS_ATTESTED
./scripts/backup_local.sh
```

Le script réalise un dump PostgreSQL custom, un miroir complet du bucket,
comptage source/copie, catalogue `pg_restore`, manifeste, SHA-256 et publication
atomique du run. Toute collision de nom est refusée. Une erreur laisse un run
`.incomplete` à examiner ; elle ne déclenche aucune reprise automatique.

## Contrôles après capture

Vérifier `COMPLETE`, `COMPLETION.SHA256`, `manifests/SHA256SUMS`, le nombre
d’objets source/copie et la révision `0005` dans la base capturée. Ne faire
aucune migration, restauration de production, modification Traefik ou écriture
sur les volumes de production dans ce ticket.
