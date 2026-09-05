# Sauvegarde et restauration
Objectifs pilote: RPO 4 a 24 heures, RTO 4 heures.
Backup: definir BACKUP_DIR hors volumes applicatifs, les variables PostgreSQL et MinIO, puis executer scripts/backup.sh. Le script cree un manifeste UTC, une archive pg_dump, un miroir MinIO et des sommes SHA-256.
Restauration: uniquement environnement isole. Definir BACKUP_PATH, TARGET_DATABASE_URL, MINIO_ALIAS, MINIO_BUCKET, CONFIRM_RESTORE=YES puis executer scripts/restore.sh. Ne jamais restaurer sur les services actuels.
Controle: executer python -m scripts.reconcile et verifier alembic current. Planifier un backup toutes les 4 heures a 24 heures selon le risque; retention indicative: 7 journaliers, 4 hebdomadaires, 3 mensuels.
