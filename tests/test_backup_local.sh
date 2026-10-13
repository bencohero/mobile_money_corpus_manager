#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
SCRIPT="$ROOT/scripts/backup_local.sh"
TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
assert_file() { [[ -f "$1" ]] || fail "missing file: $1"; }

test -x "$SCRIPT" || fail "backup script is not executable"
bash -n "$SCRIPT"

# Reproduce G8's faulty quoting: '\\0' is two bytes (backslash + zero), not NUL.
buggy="$TMP/buggy"
printf '%s\\0' "postgres/corpus.dump" >"$buggy"
python3 - "$buggy" <<'PY'
from pathlib import Path
import sys
data = Path(sys.argv[1]).read_bytes()
assert data == b"postgres/corpus.dump\\0", repr(data)
assert b"\0" not in data
PY

# The corrected contract must preserve arbitrary pathnames through the NUL pipeline.
tree="$TMP/tree"
mkdir -p "$tree/postgres" "$tree/minio/bucket" "$tree/manifests"
printf 'dump\n' >"$tree/postgres/corpus.dump"
printf 'space\n' >"$tree/minio/bucket/name with spaces.wav"
printf 'newline\n' >"$tree/minio/bucket/name
with newline.wav"
printf '{}\n' >"$tree/MANIFEST.json"

(cd "$tree" && find postgres minio manifests MANIFEST.json -type f ! -path 'manifests/SHA256SUMS' -print0 |
  sort -z | xargs --null --no-run-if-empty sha256sum > manifests/SHA256SUMS)
(cd "$tree" && sha256sum --check manifests/SHA256SUMS >/dev/null)
assert_file "$tree/manifests/SHA256SUMS"

# An empty source volume is valid input to the checksum stage and must not invoke sha256sum.
empty="$TMP/empty"
mkdir -p "$empty/postgres" "$empty/minio" "$empty/manifests"
printf '{}\n' >"$empty/MANIFEST.json"
(cd "$empty" && find postgres minio manifests MANIFEST.json -type f ! -path 'manifests/SHA256SUMS' -print0 |
  sort -z | xargs --null --no-run-if-empty sha256sum > manifests/SHA256SUMS)
(cd "$empty" && sha256sum --check manifests/SHA256SUMS >/dev/null)
[[ "$(wc -l <"$empty/manifests/SHA256SUMS")" == 1 ]] || fail "empty-volume manifest has unexpected entries"

# Keep the implementation and test contract aligned.
rg -q "find postgres minio manifests MANIFEST\\.json .* -print0 .*xargs --null --no-run-if-empty sha256sum" "$SCRIPT" ||
  fail "backup script does not use the NUL-safe checksum pipeline"

echo "backup_local regression tests: PASS"
