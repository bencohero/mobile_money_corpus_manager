#!/usr/bin/env bash
set -euo pipefail
: "${BACKUP_PATH:?BACKUP_PATH is required}"
: "${TARGET_DATABASE_URL:?TARGET_DATABASE_URL is required}"
: "${RESTORE_MODE:?RESTORE_MODE must be synthetic or isolated}"
: "${RESTORE_TARGET_ID:?RESTORE_TARGET_ID is required}"
: "${MINIO_ALIAS:?MINIO_ALIAS is required}"
: "${MINIO_BUCKET:?MINIO_BUCKET is required}"
: "${CONFIRM_RESTORE:?Set CONFIRM_RESTORE=YES explicitly}"
[ "$CONFIRM_RESTORE" = YES ] || { echo "Refusing restore without CONFIRM_RESTORE=YES" >&2; exit 2; }
[ "$RESTORE_MODE" != production ] || { echo "Production restore is forbidden by this script" >&2; exit 2; }
[ "$RESTORE_TARGET_ID" != mobile_money_corpus_manager_v0_1 ] || { echo "Refusing production restore target" >&2; exit 2; }
case "$TARGET_DATABASE_URL" in
  *mobile_money_corpus_manager_v0_1-db-1*|*mobile-money-corpus-db*) echo "Refusing production database hostname" >&2; exit 2 ;;
esac
[ -f "$BACKUP_PATH/postgres.dump" ] || { echo "Missing postgres archive" >&2; exit 3; }
[ -d "$BACKUP_PATH/minio" ] || { echo "Missing MinIO backup directory" >&2; exit 3; }
[ -f "$BACKUP_PATH/SHA256SUMS" ] || { echo "Missing SHA256SUMS" >&2; exit 3; }
[ -f "$BACKUP_PATH/MANIFEST.SHA256" ] || { echo "Missing MANIFEST.SHA256" >&2; exit 3; }
sha256sum -c "$BACKUP_PATH/SHA256SUMS" >/dev/null
sha256sum -c "$BACKUP_PATH/MANIFEST.SHA256" >/dev/null
pg_restore --no-owner --clean --if-exists --dbname="$TARGET_DATABASE_URL" "$BACKUP_PATH/postgres.dump"
mc mirror --overwrite "$BACKUP_PATH/minio" "$MINIO_ALIAS/$MINIO_BUCKET"
mc ls --recursive "$MINIO_ALIAS/$MINIO_BUCKET" >/dev/null
printf "Restore completed; run alembic current and the reconciliation check.\n"
