#!/usr/bin/env bash
# Atomic PostgreSQL 16 + MinIO backup. Production uses a validated write freeze;
# offline_app uses an explicitly attested application stop and writer-path check.
set -Eeuo pipefail
umask 077

: "${BACKUP_ROOT:?BACKUP_ROOT is required}"
: "${BACKUP_MODE:?BACKUP_MODE must be synthetic or production}"
: "${BACKUP_TARGET_ID:?BACKUP_TARGET_ID is required}"
: "${PG_CONTAINER:?PG_CONTAINER is required}"
: "${MINIO_CONTAINER:?MINIO_CONTAINER is required}"
: "${MINIO_BUCKET:?MINIO_BUCKET is required}"
: "${MINIO_MC_IMAGE:?MINIO_MC_IMAGE must be pinned by digest}"

[[ "$BACKUP_ROOT" = /* ]] || { echo "BACKUP_ROOT must be absolute" >&2; exit 2; }
[[ "$MINIO_MC_IMAGE" == *@sha256:* ]] || { echo "MINIO_MC_IMAGE must include @sha256" >&2; exit 2; }
case "$BACKUP_MODE:$BACKUP_TARGET_ID" in
  synthetic:synthetic|offline_app:synthetic) ;;
  production:mobile_money_corpus_manager_v0_1|offline_app:mobile_money_corpus_manager_v0_1)
    [[ "${BACKUP_CONFIRM:-}" == PRODUCTION_BACKUP_AUTHORIZED ]] || { echo "Production authorization missing" >&2; exit 2; }
    [[ "$PG_CONTAINER" == mobile_money_corpus_manager_v0_1-db-1 ]] || { echo "Unexpected production PostgreSQL target" >&2; exit 2; }
    [[ "$MINIO_CONTAINER" == mobile_money_corpus_manager_v0_1-minio-1 ]] || { echo "Unexpected production MinIO target" >&2; exit 2; }
    ;;
  *) echo "Unsupported mode/target" >&2; exit 2 ;;
esac

script_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
case "$BACKUP_ROOT" in "$script_root"|"$script_root"/*) echo "Destination cannot be repository" >&2; exit 2;; esac
require_image() { local c="$1" e="$2" a; a="$(docker inspect -f '{{.Image}}' "$c")"; [[ -z "$e" || "$a" == "$e" ]] || { echo "Image digest mismatch" >&2; exit 2; }; }
require_label() { local c="$1" k="$2" e="$3" a; a="$(docker inspect -f "{{index .Config.Labels \"$k\"}}" "$c" 2>/dev/null || true)"; [[ -z "$e" || "$a" == "$e" ]] || { echo "Unexpected target label" >&2; exit 2; }; }
docker inspect "$PG_CONTAINER" "$MINIO_CONTAINER" >/dev/null
[[ "$(docker inspect -f '{{.State.Status}}' "$PG_CONTAINER")" == running ]] || { echo "PostgreSQL is not running" >&2; exit 2; }
[[ "$(docker inspect -f '{{.State.Status}}' "$MINIO_CONTAINER")" == running ]] || { echo "MinIO is not running" >&2; exit 2; }
require_image "$PG_CONTAINER" "${EXPECTED_PG_IMAGE_ID:-}"
require_image "$MINIO_CONTAINER" "${EXPECTED_MINIO_IMAGE_ID:-}"
require_label "$PG_CONTAINER" com.docker.compose.service "${EXPECTED_PG_SERVICE:-}"
require_label "$MINIO_CONTAINER" com.docker.compose.service "${EXPECTED_MINIO_SERVICE:-}"

if [[ "$BACKUP_MODE" == offline_app ]]; then
  : "${APP_CONTAINER:?APP_CONTAINER is required in offline_app mode}"
  : "${OFFLINE_WRITERS_ATTESTED:?OFFLINE_WRITERS_ATTESTED must be YES in offline_app mode}"
  [[ "$OFFLINE_WRITERS_ATTESTED" == YES ]] || { echo "Refusing offline backup without writer-path attestation" >&2; exit 2; }
  docker inspect "$APP_CONTAINER" >/dev/null || { echo "Offline app container is missing" >&2; exit 2; }
  [[ "$(docker inspect -f '{{.State.Status}}' "$APP_CONTAINER")" =~ ^(exited|dead)$ ]] || {
    echo "Offline app container is not stopped" >&2; exit 2;
  }
  app_project="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$APP_CONTAINER" 2>/dev/null || true)"
  [[ "$app_project" == "$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$PG_CONTAINER")" ]] || {
    echo "Offline app is not in the target Compose project" >&2; exit 2;
  }
  running_project_services="$(docker ps -q --filter "label=com.docker.compose.project=$app_project" --filter status=running | wc -l | tr -d ' ')"
  [[ "$running_project_services" == 2 ]] || {
    echo "Target Compose project has unexpected running services" >&2; exit 2;
  }
  target_volumes="$(docker inspect -f '{{range .Mounts}}{{if .Name}}{{.Name}}{{"\n"}}{{end}}{{end}}' "$PG_CONTAINER" "$MINIO_CONTAINER" | sort -u)"
  while IFS= read -r volume; do
    [[ -n "$volume" ]] || continue
    mounted_elsewhere="$(docker ps -q --filter status=running | while read -r c; do
      docker inspect -f '{{range .Mounts}}{{if eq .Name "'"$volume"'"}}{{.Name}}{{end}}{{end}}' "$c" 2>/dev/null | grep -qx "$volume" && docker inspect -f '{{.Name}}' "$c"
    done | grep -v -E "^/$PG_CONTAINER$|^/$MINIO_CONTAINER$" || true)"
    [[ -z "$mounted_elsewhere" ]] || { echo "Target data volume mounted by another running container: $mounted_elsewhere" >&2; exit 2; }
  done <<< "$target_volumes"
  published_ports="$(docker inspect -f '{{json .HostConfig.PortBindings}}' "$PG_CONTAINER" "$MINIO_CONTAINER" | grep -v -E '^(null|\{\})$' || true)"
  [[ -z "$published_ports" ]] || { echo "Target PostgreSQL/MinIO has a published host port" >&2; exit 2; }
  write_processes="$(ps -eo pid=,cmd= | grep -E '[u]pload|[t]ranscrib|[r]econcil|[p]g_dump|[p]g_restore|[m]c mirror|[r]clone|[r]estic|[b]org' || true)"
  [[ -z "$write_processes" ]] || { echo "Potential write/backup process detected: $write_processes" >&2; exit 2; }
  db_external_sessions="$(docker exec "$PG_CONTAINER" sh -ceu 'psql -Atq -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select count(*) from pg_stat_activity where pid <> pg_backend_pid() and datname = current_database()"')"
  [[ "$db_external_sessions" == 0 ]] || { echo "PostgreSQL has external sessions: $db_external_sessions" >&2; exit 2; }
fi

mkdir -m 700 -p "$BACKUP_ROOT"
exec 9>"$BACKUP_ROOT/.backup.lock"
flock -n 9 || { echo "Another backup is already running" >&2; exit 2; }
BACKUP_ID="${BACKUP_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
FINAL="$BACKUP_ROOT/$BACKUP_ID"
TMP="$BACKUP_ROOT/.run.$BACKUP_ID.incomplete"
[[ ! -e "$FINAL" && ! -e "$TMP" ]] || { echo "Destination already exists" >&2; exit 2; }
mkdir -m 700 -p "$TMP/postgres" "$TMP/minio/$MINIO_BUCKET" "$TMP/manifests" "$TMP/logs"
mark_incomplete() { local rc=$?; if [[ -d "$TMP" ]]; then printf 'status=INCOMPLETE\nbackup_id=%s\n' "$BACKUP_ID" >"$TMP/INCOMPLETE"; fi; exit "$rc"; }
trap mark_incomplete EXIT

docker exec "$PG_CONTAINER" sh -lc 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null
docker exec "$MINIO_CONTAINER" sh -lc 'curl -fsS http://localhost:9000/minio/health/live >/dev/null'
docker exec "$PG_CONTAINER" sh -ceu 'pg_dump --format=custom --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >"$TMP/postgres/corpus.dump" 2>"$TMP/logs/postgres.log"
[[ -s "$TMP/postgres/corpus.dump" ]] || { echo "Empty PostgreSQL dump" >&2; exit 3; }
docker exec -i "$PG_CONTAINER" pg_restore --list <"$TMP/postgres/corpus.dump" >"$TMP/manifests/postgres_contents.txt" 2>>"$TMP/logs/postgres.log"

MINIO_ROOT_USER="$(docker exec "$MINIO_CONTAINER" sh -lc 'printf "%s" "$MINIO_ROOT_USER"')"
MINIO_ROOT_PASSWORD="$(docker exec "$MINIO_CONTAINER" sh -lc 'printf "%s" "$MINIO_ROOT_PASSWORD"')"
[[ -n "$MINIO_ROOT_USER" && -n "$MINIO_ROOT_PASSWORD" ]] || { echo "MinIO credentials unavailable" >&2; exit 2; }
mc() {
  docker run --rm --user "$(id -u):$(id -g)" --network "container:$MINIO_CONTAINER" --volume "$TMP/minio:/backup" \
    --env "MINIO_ROOT_USER=$MINIO_ROOT_USER" --env "MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD" --env HOME=/tmp \
    --entrypoint /bin/sh "$MINIO_MC_IMAGE" -ceu \
    'mc alias set source http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null; exec mc "$@"' sh "$@"
}
mc stat "source/$MINIO_BUCKET" >/dev/null
mc mirror "source/$MINIO_BUCKET" "/backup/$MINIO_BUCKET" --config-dir /tmp/mc-config \
  2>"$TMP/logs/minio.log" || { echo "MinIO copy failed" >&2; exit 4; }
mc ls --recursive --json "source/$MINIO_BUCKET" | wc -l | tr -d ' ' >"$TMP/manifests/minio_source_count.txt"
find "$TMP/minio/$MINIO_BUCKET" -type f | wc -l | tr -d ' ' >"$TMP/manifests/minio_copy_count.txt"
[[ "$(cat "$TMP/manifests/minio_source_count.txt")" == "$(cat "$TMP/manifests/minio_copy_count.txt")" ]] || { echo "MinIO object count mismatch" >&2; exit 4; }

python3 - "$TMP" "$BACKUP_MODE" "$BACKUP_TARGET_ID" "$PG_CONTAINER" "$MINIO_CONTAINER" "$MINIO_BUCKET" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
manifest = {"schema": 2, "status": "COMPLETE", "mode": sys.argv[2], "target_id": sys.argv[3],
            "postgres_container": sys.argv[4], "minio_container": sys.argv[5], "minio_bucket": sys.argv[6],
            "postgres_dump": "postgres/corpus.dump", "coherence":
            "offline_app_stop_and_writer_path_attested" if sys.argv[2] == "offline_app" else "validated_write_freeze_required",
            "minio_object_count": int((root / "manifests/minio_source_count.txt").read_text())}
(root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY
(cd "$TMP" && find postgres minio manifests MANIFEST.json -type f ! -path 'manifests/SHA256SUMS' -print0 | sort -z | xargs -0 sha256sum > manifests/SHA256SUMS)
(cd "$TMP" && sha256sum --check manifests/SHA256SUMS >/dev/null)
printf 'status=COMPLETE\nbackup_id=%s\n' "$BACKUP_ID" >"$TMP/COMPLETE"
(cd "$TMP" && sha256sum COMPLETE > COMPLETION.SHA256)
(cd "$TMP" && sha256sum --check COMPLETION.SHA256 >/dev/null)
chmod -R go-rwx "$TMP"
mv --no-clobber "$TMP" "$FINAL"
trap - EXIT
printf 'Backup published: %s\n' "$FINAL"
