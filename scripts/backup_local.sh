#!/usr/bin/env bash
# F5A6: secure, read-only capture of PostgreSQL + MinIO.
# This script never stops, starts, removes, or recreates a Docker service.
set -Eeuo pipefail
umask 077

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/mobile-money-corpus}"
BACKUP_ID="${BACKUP_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
FINAL_DIR="${BACKUP_ROOT}/${BACKUP_ID}"
BACKUP_DIR="${FINAL_DIR}.incomplete"
LOCK_FILE="${BACKUP_ROOT}/.f5a6-backup.lock"
MODE="${BACKUP_MODE:-offline_app}"
PG_CONTAINER="${PG_CONTAINER:-mobile_money_corpus_manager_v0_1-db-1}"
MINIO_CONTAINER="${MINIO_CONTAINER:-mobile_money_corpus_manager_v0_1-minio-1}"
APP_CONTAINER="${APP_CONTAINER:-mobile_money_corpus_manager_v0_1-app-1}"
EXPECTED_PROJECT="${EXPECTED_PROJECT:-mobile_money_corpus_manager_v0_1}"
PG_DATABASE="${PG_DATABASE:-corpus}"
MINIO_BUCKET="${MINIO_BUCKET:-mobile-money-corpus}"
MC_BIN="${MC_BIN:-mc}"
MC_SHA256="${MC_SHA256:-}"
MINIO_ALIAS="${MINIO_ALIAS:-f5a6-source}"

die() { printf '[F5A6] ERROR: %s\n' "$*" >&2; exit 1; }
log() { printf '[F5A6] %s\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing command: $1"; }
json_escape() { python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'; }

[[ "$MODE" == offline_app ]] || die "BACKUP_MODE must be offline_app"
[[ "${CONFIRM_TARGET:-}" == YES ]] || die "CONFIRM_TARGET=YES required"
[[ "${OFFLINE_WRITERS_ATTESTED:-}" == YES ]] || die "OFFLINE_WRITERS_ATTESTED=YES required"
[[ "${BACKUP_APPROVED:-}" == YES ]] || die "BACKUP_APPROVED=YES required; this is a real-backup gate"
[[ -d "$PROJECT_DIR" ]] || die "project directory not found: $PROJECT_DIR"
[[ "$BACKUP_DIR" != "$PROJECT_DIR"/* ]] || die "backup destination must not be inside project"

for c in docker flock sha256sum find sort awk sed python3 mktemp; do need "$c"; done
need "$MC_BIN"
[[ -n "$MC_SHA256" ]] || die "MC_SHA256 must pin the approved MinIO client"
printf '%s  %s\n' "$MC_SHA256" "$MC_BIN" | sha256sum -c - >/dev/null 2>&1 || die "MinIO client digest mismatch"

mkdir -p "$BACKUP_ROOT"
exec 9>"$LOCK_FILE"
flock -n 9 || die "another F5A6 backup is running"
[[ ! -e "$BACKUP_DIR" && ! -e "$FINAL_DIR" ]] || die "refusing to overwrite existing archive: $FINAL_DIR"

inspect() { docker inspect --format '{{json .}}' "$1"; }
container_json() { inspect "$1" 2>/dev/null || die "required container is missing: $1"; }
json_field() { python3 -c 'import json,sys; x=json.load(sys.stdin); print(x.get(sys.argv[1],""))' "$1"; }
json_nested() { python3 -c 'import json,sys; x=json.load(sys.stdin); [x:=x[k] for k in sys.argv[1].split(".")]; print(str(x).lower() if isinstance(x,bool) else x)' "$1"; }

PG_JSON="$(container_json "$PG_CONTAINER")"
MINIO_JSON="$(container_json "$MINIO_CONTAINER")"
APP_JSON="$(inspect "$APP_CONTAINER" 2>/dev/null || true)"
pg_name="$(printf '%s' "$PG_JSON" | json_field Name)"
minio_name="$(printf '%s' "$MINIO_JSON" | json_field Name)"
[[ "$pg_name" == "/$PG_CONTAINER" ]] || die "unexpected PostgreSQL container identity"
[[ "$minio_name" == "/$MINIO_CONTAINER" ]] || die "unexpected MinIO container identity"

pg_image="$(printf '%s' "$PG_JSON" | json_nested Config.Image)"
minio_image="$(printf '%s' "$MINIO_JSON" | json_nested Config.Image)"
[[ "$pg_image" == postgres:16* ]] || die "unexpected PostgreSQL image: $pg_image"
[[ "$minio_image" == minio/minio:RELEASE.2025-04-22T22-12-26Z ]] || die "unexpected MinIO image: $minio_image"

pg_running="$(printf '%s' "$PG_JSON" | json_nested State.Running)"
minio_running="$(printf '%s' "$MINIO_JSON" | json_nested State.Running)"
[[ "$pg_running" == true ]] || die "PostgreSQL is not running"
[[ "$minio_running" == true ]] || die "MinIO is not running"

if [[ -n "$APP_JSON" ]]; then
  app_running="$(printf '%s' "$APP_JSON" | json_nested State.Running)"
  [[ "$app_running" == false ]] || die "application container is active"
  APP_STATE=APP_STOPPED
else
  APP_STATE=APP_ABSENT
fi

docker exec "$PG_CONTAINER" pg_isready -d "$PG_DATABASE" >/dev/null 2>&1 || die "PostgreSQL health check failed"
docker exec "$MINIO_CONTAINER" curl -fsS http://localhost:9000/minio/health/live >/dev/null 2>&1 || die "MinIO health check failed"
active_sessions="$(docker exec "$PG_CONTAINER" sh -ceu 'psql -U "$POSTGRES_USER" -d "$1" -AtX -c "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid()"' sh "$PG_DATABASE")"
[[ "$active_sessions" == 0 ]] || die "other PostgreSQL sessions detected: $active_sessions"

mkdir -p "$BACKUP_DIR/postgres" "$BACKUP_DIR/minio" "$BACKUP_DIR/manifests" "$BACKUP_DIR/reports"
incomplete=1
MC_CONFIG_DIR="$(mktemp -d)"
cleanup() {
  rm -rf -- "$MC_CONFIG_DIR"
  if [[ "$incomplete" == 1 ]]; then log "archive retained incomplete: $BACKUP_DIR" >&2; fi
}
trap cleanup EXIT

log "capturing PostgreSQL custom dump"
docker exec "$PG_CONTAINER" sh -ceu 'pg_dump -U "$POSTGRES_USER" -d "$1" -Fc' sh "$PG_DATABASE" >"$BACKUP_DIR/postgres/corpus.dump"
[[ -s "$BACKUP_DIR/postgres/corpus.dump" ]] || die "empty PostgreSQL dump"
docker exec -i "$PG_CONTAINER" pg_restore --list <"$BACKUP_DIR/postgres/corpus.dump" >"$BACKUP_DIR/manifests/postgres.list"
cp "$BACKUP_DIR/manifests/postgres.list" "$BACKUP_DIR/postgres.list"

log "capturing MinIO bucket"
MC_CONFIG_DIR="$MC_CONFIG_DIR" "$MC_BIN" alias set "$MINIO_ALIAS" "${MINIO_ENDPOINT:?MINIO_ENDPOINT required}" "${MINIO_ACCESS_KEY:?MINIO_ACCESS_KEY required}" "${MINIO_SECRET_KEY:?MINIO_SECRET_KEY required}" >/dev/null
MC_CONFIG_DIR="$MC_CONFIG_DIR" "$MC_BIN" stat "$MINIO_ALIAS/$MINIO_BUCKET" >/dev/null
MC_CONFIG_DIR="$MC_CONFIG_DIR" "$MC_BIN" mirror "$MINIO_ALIAS/$MINIO_BUCKET" "$BACKUP_DIR/minio/$MINIO_BUCKET" >"$BACKUP_DIR/manifests/minio.log" 2>&1

source_objects="$(MC_CONFIG_DIR="$MC_CONFIG_DIR" "$MC_BIN" find "$MINIO_ALIAS/$MINIO_BUCKET" | awk 'NF{n++} END{print n+0}')"
dest_objects="$(find "$BACKUP_DIR/minio/$MINIO_BUCKET" -type f -print | awk 'NF{n++} END{print n+0}')"
[[ "$source_objects" == "$dest_objects" ]] || die "MinIO object count mismatch: source=$source_objects destination=$dest_objects"
export BACKUP_ID APP_STATE PG_CONTAINER MINIO_CONTAINER PG_DATABASE MINIO_BUCKET
export SOURCE_OBJECTS="$source_objects" DEST_OBJECTS="$dest_objects"
export MC_SHA256

docker exec "$PG_CONTAINER" sh -ceu 'psql -U "$POSTGRES_USER" -d "$1" -AtX -c "SELECT version()"' sh "$PG_DATABASE" >"$BACKUP_DIR/manifests/postgres_version.txt"
docker exec "$PG_CONTAINER" sh -ceu 'psql -U "$POSTGRES_USER" -d "$1" -AtX -c "SELECT version_num FROM alembic_version ORDER BY version_num"' sh "$PG_DATABASE" >"$BACKUP_DIR/manifests/alembic_revision.txt"
grep -Fxq 0005_workshop_attribution "$BACKUP_DIR/manifests/alembic_revision.txt" || die "unexpected Alembic revision"

docker exec "$PG_CONTAINER" sh -ceu 'for table_name in users participants utterances recordings transcriptions audit_logs; do printf "%s|" "$table_name"; psql -U "$POSTGRES_USER" -d "$1" -AtX -c "SELECT count(*) FROM $table_name"; done' sh "$PG_DATABASE" >"$BACKUP_DIR/manifests/table_counts.txt"

docker exec "$PG_CONTAINER" sh -ceu 'psql -U "$POSTGRES_USER" -d "$1" -AtX -c "SELECT raw_object FROM recordings WHERE raw_object IS NOT NULL UNION SELECT wav_object FROM recordings WHERE wav_object IS NOT NULL"' sh "$PG_DATABASE" | sort -u >"$BACKUP_DIR/manifests/referenced_objects.txt"
find "$BACKUP_DIR/minio/$MINIO_BUCKET" -type f -printf '%P\n' | sort -u >"$BACKUP_DIR/manifests/captured_objects.txt"
python3 - "$BACKUP_DIR/manifests/referenced_objects.txt" "$BACKUP_DIR/manifests/captured_objects.txt" "$BACKUP_DIR/reports/backup_report.json" <<'PY'
import json, sys
refs = {x.strip() for x in open(sys.argv[1], encoding="utf-8") if x.strip()}
objects = {x.strip() for x in open(sys.argv[2], encoding="utf-8") if x.strip()}
missing = sorted(refs - objects)
orphans = sorted(objects - refs)
report = {
    "format": "f5a6-report-v1",
    "referenced_objects": len(refs),
    "captured_objects": len(objects),
    "missing_referenced_objects": missing,
    "orphan_objects": orphans,
    "coherent": not missing and not orphans,
}
with open(sys.argv[3], "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, sort_keys=True)
    f.write("\n")
if missing or orphans:
    raise SystemExit("PostgreSQL/MinIO coherence check failed")
PY

python3 - "$BACKUP_DIR/manifests/MANIFEST.json" <<'PY'
import json, os, sys
payload = {
    "format": "f5a6-v1",
    "backup_id": os.environ["BACKUP_ID"],
    "app_state": os.environ["APP_STATE"],
    "postgres_container": os.environ["PG_CONTAINER"],
    "minio_container": os.environ["MINIO_CONTAINER"],
    "postgres_database": os.environ["PG_DATABASE"],
    "minio_bucket": os.environ["MINIO_BUCKET"],
    "source_objects": int(os.environ["SOURCE_OBJECTS"]),
    "destination_objects": int(os.environ["DEST_OBJECTS"]),
    "minio_client_sha256": os.environ["MC_SHA256"],
}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(payload, f, sort_keys=True, indent=2)
    f.write("\n")
PY
(cd "$BACKUP_DIR" && { find postgres minio manifests reports -type f ! -name SHA256SUMS -print0; printf '%s\\0' postgres.list; } | sort -z | xargs -0 sha256sum > manifests/SHA256SUMS)
(cd "$BACKUP_DIR" && sha256sum --check manifests/SHA256SUMS >/dev/null)
printf 'complete_at_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >"$BACKUP_DIR/COMPLETE"
sha256sum "$BACKUP_DIR/COMPLETE" | awk '{print $1}' >"$BACKUP_DIR/COMPLETION.SHA256"
mv -- "$BACKUP_DIR" "$FINAL_DIR"
incomplete=0
log "backup complete: $FINAL_DIR"
