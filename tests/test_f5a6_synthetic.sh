#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/scripts/backup_local.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
MOCK="$TMP/mock"
mkdir -p "$MOCK"

cat >"$MOCK/docker" <<'EOF'
#!/usr/bin/env bash
set -u
if [[ "$1" == inspect ]]; then
  name="${@: -1}"
  [[ "$name" == "$PG_CONTAINER" || "$name" == "$MINIO_CONTAINER" || ( "$name" == "$APP_CONTAINER" && "${APP_MODE:-stopped}" != absent ) ]] || exit 1
  case "$name" in
    "$PG_CONTAINER") printf '%s\n' '{"Name":"'"/$PG_CONTAINER"'","Config":{"Image":"postgres:16-alpine"},"State":{"Running":true}}';;
    "$MINIO_CONTAINER") printf '%s\n' '{"Name":"'"/$MINIO_CONTAINER"'","Config":{"Image":"minio/minio:RELEASE.2025-04-22T22-12-26Z"},"State":{"Running":true}}';;
    *) if [[ "${APP_MODE:-stopped}" == active ]]; then running=true; else running=false; fi; printf '%s\n' '{"Name":"'"/$APP_CONTAINER"'","Config":{"Image":"app:test"},"State":{"Running":'"$running"'}}';;
  esac
  exit 0
fi
if [[ "$1" == exec ]]; then
  cmd="${*:3}"
  [[ "$cmd" == *pg_isready* || "$cmd" == *curl* ]] && exit 0
  [[ "$cmd" == *pg_dump* ]] && { [[ "${PG_FAIL:-0}" == 1 ]] && exit 7; printf 'synthetic dump\n'; exit 0; }
  [[ "$cmd" == *pg_restore* ]] && { [[ "${TRUNCATED:-0}" == 1 ]] && exit 8; printf 'synthetic toc\n'; exit 0; }
  [[ "$cmd" == *'SELECT version()'* ]] && { printf 'PostgreSQL 16 synthetic\n'; exit 0; }
  [[ "$cmd" == *pg_stat_activity* ]] && { printf '%s\n' "${ACTIVE_SESSIONS:-0}"; exit 0; }
  [[ "$cmd" == *version_num* ]] && { printf '0005_workshop_attribution\n'; exit 0; }
  [[ "$cmd" == *'SELECT table_name'* ]] && { printf 'recordings|1\n'; exit 0; }
  [[ "$cmd" == *raw_object* ]] && { printf 'audio/raw.wav\naudio/wav.wav\n'; exit 0; }
fi
exit 0
EOF
cat >"$MOCK/mc" <<'EOF'
#!/usr/bin/env bash
set -u
case "$1" in
  alias|stat) exit 0;;
  mirror) [[ "${MC_FAIL:-0}" == 1 ]] && exit 9; mkdir -p "$3/audio"; printf x >"$3/audio/raw.wav"; printf x >"$3/audio/wav.wav";;
  find) printf 'f5a6-source/mobile-money-corpus/audio/raw.wav\nf5a6-source/mobile-money-corpus/audio/wav.wav\n';;
esac
EOF
chmod 755 "$MOCK/docker" "$MOCK/mc"
MC_HASH="$(sha256sum "$MOCK/mc" | awk '{print $1}')"

run() {
  local name="$1" expected="$2"; shift 2
  local root="$TMP/$name"; mkdir -p "$root"
  set +e
  PATH="$MOCK:$PATH" PROJECT_DIR="$ROOT" BACKUP_ROOT="$root" BACKUP_ID="$name" \
    PG_CONTAINER=f5a6-db MINIO_CONTAINER=f5a6-minio APP_CONTAINER=f5a6-app \
    MINIO_ENDPOINT=http://synthetic MINIO_ACCESS_KEY=synthetic MINIO_SECRET_KEY=synthetic \
    MC_BIN="$MOCK/mc" MC_SHA256="$MC_HASH" CONFIRM_TARGET=YES BACKUP_APPROVED=YES \
    OFFLINE_WRITERS_ATTESTED=YES "$@" "$SCRIPT"
  local rc=$?
  set -e
  if [[ "$expected" == 0 ]]; then
    [[ "$rc" -eq 0 ]] || { echo "FAIL $name expected success got=$rc" >&2; exit 1; }
  else
    [[ "$rc" -ne 0 ]] || { echo "FAIL $name expected refusal/failure" >&2; exit 1; }
  fi
}

run stopped 0 env APP_MODE=stopped
run absent 0 env APP_MODE=absent
run active 1 env APP_MODE=active
run no_attestation 1 env OFFLINE_WRITERS_ATTESTED=NO
run active_session 1 env APP_MODE=stopped ACTIVE_SESSIONS=1
run pg_dump_failed 1 env APP_MODE=stopped PG_FAIL=1
run minio_failed 1 env APP_MODE=stopped MC_FAIL=1
run truncated_dump 1 env APP_MODE=stopped TRUNCATED=1
mkdir -p "$TMP/existing_archive/existing_archive"
run existing_archive 1 env APP_MODE=stopped
run complete 0 env APP_MODE=absent
test -f "$TMP/complete/complete/COMPLETE"
test -f "$TMP/complete/complete/COMPLETION.SHA256"
test -f "$TMP/complete/complete/reports/backup_report.json"
echo "F5A6 synthetic guard/capture tests: 10 passed"
