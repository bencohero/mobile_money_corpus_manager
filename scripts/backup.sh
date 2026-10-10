#!/usr/bin/env bash
set -euo pipefail
: "${BACKUP_DIR:?BACKUP_DIR is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${PGHOST:?PGHOST is required}"
: "${MINIO_ALIAS:?MINIO_ALIAS is required}"
mkdir -p -- "$BACKUP_DIR"
stamp=$(date -u +%Y%m%dT%H%M%SZ); dest="$BACKUP_DIR/$stamp"; mkdir -m 700 "$dest"
pg_dump --format=custom --file="$dest/postgres.dump" --dbname="postgresql://${POSTGRES_USER}@${PGHOST}:5432/${POSTGRES_DB}"
mc alias set "$MINIO_ALIAS" "${MINIO_ENDPOINT:?MINIO_ENDPOINT is required}" "${MINIO_ACCESS_KEY:?MINIO_ACCESS_KEY is required}" "${MINIO_SECRET_KEY:?MINIO_SECRET_KEY is required}" >/dev/null
mc mirror --overwrite "$MINIO_ALIAS/${MINIO_BUCKET:?MINIO_BUCKET is required}" "$dest/minio"
sha256sum "$dest/postgres.dump" > "$dest/SHA256SUMS"
find "$dest/minio" -type f -print0 | sort -z | xargs -0 sha256sum >> "$dest/SHA256SUMS" || true
printf "Backup created at %s\n" "$dest"
