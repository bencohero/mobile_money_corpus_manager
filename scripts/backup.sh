#!/usr/bin/env bash
set -euo pipefail
: "${BACKUP_DIR:?BACKUP_DIR is required}"
: "${BACKUP_MODE:?BACKUP_MODE must be synthetic or production}"
: "${BACKUP_TARGET_ID:?BACKUP_TARGET_ID is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${PGHOST:?PGHOST is required}"
: "${MINIO_ALIAS:?MINIO_ALIAS is required}"

case "$BACKUP_MODE" in
  synthetic)
    [ "$BACKUP_TARGET_ID" = "synthetic" ] || { echo "Refusing non-synthetic target in synthetic mode" >&2; exit 2; }
    ;;
  production)
    [ "$BACKUP_TARGET_ID" = "mobile_money_corpus_manager_v0_1" ] || { echo "Refusing unknown production target" >&2; exit 2; }
    [ "${BACKUP_CONFIRM:-}" = "PRODUCTION_BACKUP_AUTHORIZED" ] || {
      echo "Refusing production backup without BACKUP_CONFIRM=PRODUCTION_BACKUP_AUTHORIZED" >&2; exit 2;
    }
    ;;
  *) echo "Unsupported BACKUP_MODE: $BACKUP_MODE" >&2; exit 2 ;;
esac

case "$BACKUP_DIR" in
  /*) ;;
  *) echo "BACKUP_DIR must be an absolute path" >&2; exit 2 ;;
esac
script_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
case "$BACKUP_DIR" in
  "$script_root"|"$script_root"/*) echo "BACKUP_DIR must not be the repository or a child of it" >&2; exit 2 ;;
esac
mkdir -p -- "$BACKUP_DIR"
stamp=$(date -u +%Y%m%dT%H%M%SZ); dest="$BACKUP_DIR/$stamp"; mkdir -m 700 "$dest"
pg_dump --format=custom --file="$dest/postgres.dump" --dbname="postgresql://${POSTGRES_USER}@${PGHOST}:5432/${POSTGRES_DB}"
mc alias set "$MINIO_ALIAS" "${MINIO_ENDPOINT:?MINIO_ENDPOINT is required}" "${MINIO_ACCESS_KEY:?MINIO_ACCESS_KEY is required}" "${MINIO_SECRET_KEY:?MINIO_SECRET_KEY is required}" >/dev/null
mc mirror --overwrite "$MINIO_ALIAS/${MINIO_BUCKET:?MINIO_BUCKET is required}" "$dest/minio"
mc ls --json --recursive "$MINIO_ALIAS/${MINIO_BUCKET}" > "$dest/minio_inventory.jsonl"
python3 - "$dest" "$BACKUP_MODE" "$BACKUP_TARGET_ID" "$PGHOST" "$POSTGRES_DB" "$MINIO_BUCKET" <<'PY'
import json, pathlib, sys
dest, mode, target, pghost, database, bucket = sys.argv[1:]
root = pathlib.Path(dest)
files = [p for p in root.joinpath("minio").rglob("*") if p.is_file()]
manifest = {
    "schema": 1,
    "mode": mode,
    "target_id": target,
    "created_at_utc": root.name,
    "postgres_host": pghost,
    "postgres_database": database,
    "minio_bucket": bucket,
    "postgres_dump": "postgres.dump",
    "minio_file_count": len(files),
    "coherence_window": "controlled_write_freeze_required",
}
root.joinpath("MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY
sha256sum "$dest/postgres.dump" > "$dest/SHA256SUMS"
find "$dest/minio" -type f -print0 | sort -z | xargs -0 sha256sum >> "$dest/SHA256SUMS"
sha256sum "$dest/MANIFEST.json" > "$dest/MANIFEST.SHA256"
sha256sum -c "$dest/SHA256SUMS" >/dev/null
sha256sum -c "$dest/MANIFEST.SHA256" >/dev/null
printf "Backup created at %s\n" "$dest"
