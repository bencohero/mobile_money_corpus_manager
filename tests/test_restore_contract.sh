#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
SCRIPT="$ROOT/scripts/restore.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
pass=0
expect_fail() { if "$@" >/dev/null 2>&1; then fail "expected refusal: $*"; fi; pass=$((pass + 1)); }
expect_ok() { "$@" >/dev/null 2>&1 || fail "expected success: $*"; pass=$((pass + 1)); }

FAKE="$TMP/bin"; mkdir -p "$FAKE"
cat >"$FAKE/pg_restore" <<'SH'
#!/usr/bin/env bash
printf '%s\n' "$*" >>"${FAKE_LOG:?}"
exit 0
SH
cat >"$FAKE/mc" <<'SH'
#!/usr/bin/env bash
set -eu
case "${1:-}" in
  alias) [ "${2:-}" = export ] && printf '{"url":"http://isolated-minio:9000"}\n' ;;
  mb) ;;
  mirror) printf 'mirror\n' >>"${FAKE_LOG:?}" ;;
  ls) printf '{"key":"object.wav"}\n' ;;
  *) exit 2 ;;
esac
SH
chmod 750 "$FAKE/pg_restore" "$FAKE/mc"
export PATH="$FAKE:$PATH" FAKE_LOG="$TMP/fake.log"

make_common() {
  local root="$1" schema="$2"
  mkdir -p "$root"
  if [ "$schema" = 1 ]; then
    mkdir "$root/minio"
    printf dump >"$root/postgres.dump"
    printf audio >"$root/minio/object.wav"
    printf '{"schema":1,"mode":"synthetic","target_id":"synthetic","postgres_dump":"postgres.dump","minio_bucket":"test-bucket","minio_file_count":1}\n' >"$root/MANIFEST.json"
    printf '{"key":"object.wav"}\n' >"$root/minio_inventory.jsonl"
    (cd "$root" && sha256sum postgres.dump minio/object.wav >SHA256SUMS && sha256sum MANIFEST.json >MANIFEST.SHA256)
  else
    mkdir -p "$root/postgres" "$root/minio/test-bucket" "$root/manifests" "$root/logs"
    printf dump >"$root/postgres/corpus.dump"
    printf audio >"$root/minio/test-bucket/object.wav"
    printf log >"$root/logs/postgres.log"; printf log >"$root/logs/minio.log"
    printf x >"$root/manifests/postgres_contents.txt"
    printf 1 >"$root/manifests/minio_source_count.txt"
    printf 1 >"$root/manifests/minio_copy_count.txt"
    printf '{"schema":2,"status":"COMPLETE","mode":"synthetic","target_id":"synthetic","postgres_dump":"postgres/corpus.dump","minio_bucket":"test-bucket","minio_object_count":1}\n' >"$root/MANIFEST.json"
    printf 'status=COMPLETE\n' >"$root/COMPLETE"
    (cd "$root" && find postgres minio manifests MANIFEST.json -type f ! -path 'manifests/SHA256SUMS' -print0 | sort -z | xargs -0 sha256sum >manifests/SHA256SUMS && sha256sum COMPLETE >COMPLETION.SHA256)
  fi
}

run_restore() {
  BACKUP_PATH="$1" TARGET_DATABASE_URL='postgresql://isolated_user:pw@isolated-db:5432/isolated' RESTORE_MODE=isolated RESTORE_TARGET_ID=isolated-g8-8-a MINIO_ALIAS=isolated MINIO_BUCKET=test-bucket RESTORE_MINIO_ENDPOINT=http://isolated-minio:9000 CONFIRM_RESTORE=YES "$SCRIPT"
}

V1="$TMP/schema1"; make_common "$V1" 1; expect_ok run_restore "$V1"
V2="$TMP/schema2"; make_common "$V2" 2; expect_ok run_restore "$V2"

MISSING="$TMP/missing"; cp -a "$V2" "$MISSING"; rm "$MISSING/MANIFEST.json"; expect_fail run_restore "$MISSING"
BAD="$TMP/bad"; cp -a "$V2" "$BAD"; printf corrupt >>"$BAD/postgres/corpus.dump"; expect_fail run_restore "$BAD"
INCOMPLETE="$TMP/incomplete"; cp -a "$V2" "$INCOMPLETE"; rm "$INCOMPLETE/COMPLETE"; expect_fail run_restore "$INCOMPLETE"
EXTRA="$TMP/extra"; cp -a "$V2" "$EXTRA"; printf unexpected >"$EXTRA/unexpected.txt"; expect_fail run_restore "$EXTRA"
expect_fail env BACKUP_PATH="$V2" TARGET_DATABASE_URL='postgresql://isolated_user:pw@isolated-db:5432/isolated' RESTORE_MODE=isolated RESTORE_TARGET_ID=mobile_money_corpus_manager_v0_1 MINIO_ALIAS=isolated MINIO_BUCKET=test-bucket RESTORE_MINIO_ENDPOINT=http://isolated-minio:9000 CONFIRM_RESTORE=YES "$SCRIPT"
expect_fail env BACKUP_PATH="$V2" TARGET_DATABASE_URL='postgresql://corpus:pw@mobile-money-corpus-db:5432/corpus' RESTORE_MODE=isolated RESTORE_TARGET_ID=isolated-g8-8-a MINIO_ALIAS=isolated MINIO_BUCKET=test-bucket RESTORE_MINIO_ENDPOINT=http://isolated-minio:9000 CONFIRM_RESTORE=YES "$SCRIPT"

[ "$(grep -c '^mirror$' "$FAKE_LOG")" = 2 ] || fail "negative cases reached MinIO restore"
echo "restore contract tests: PASS ($pass cases)"
