#!/usr/bin/env bash
set -euo pipefail
: "${BACKUP_PATH:?BACKUP_PATH is required}"
: "${TARGET_DATABASE_URL:?TARGET_DATABASE_URL is required}"
: "${MINIO_ALIAS:?MINIO_ALIAS is required}"
: "${MINIO_BUCKET:?MINIO_BUCKET is required}"
: "${CONFIRM_RESTORE:?Set CONFIRM_RESTORE=YES explicitly}"
[ "$CONFIRM_RESTORE" = YES ] || { echo "Refusing restore without CONFIRM_RESTORE=YES" >&2; exit 2; }
[ -f "$BACKUP_PATH/postgres.dump" ] || { echo "Missing postgres archive" >&2; exit 3; }
[ -d "$BACKUP_PATH/minio" ] || { echo "Missing MinIO backup directory" >&2; exit 3; }
pg_restore --no-owner --clean --if-exists --dbname="$TARGET_DATABASE_URL" "$BACKUP_PATH/postgres.dump"
mc mirror --overwrite "$BACKUP_PATH/minio" "$MINIO_ALIAS/$MINIO_BUCKET"
mc ls --recursive "$MINIO_ALIAS/$MINIO_BUCKET" >/dev/null
printf "Restore completed; run alembic current and the reconciliation check.\n"
