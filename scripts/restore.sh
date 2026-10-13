#!/usr/bin/env bash
# Restore only a versioned backup contract into an explicitly isolated target.
set -Eeuo pipefail

: "${BACKUP_PATH:?BACKUP_PATH is required}"
: "${TARGET_DATABASE_URL:?TARGET_DATABASE_URL is required}"
: "${RESTORE_MODE:?RESTORE_MODE must be synthetic or isolated}"
: "${RESTORE_TARGET_ID:?RESTORE_TARGET_ID is required}"
: "${MINIO_ALIAS:?MINIO_ALIAS is required}"
: "${MINIO_BUCKET:?MINIO_BUCKET is required}"
: "${RESTORE_MINIO_ENDPOINT:?RESTORE_MINIO_ENDPOINT is required}"
: "${CONFIRM_RESTORE:?Set CONFIRM_RESTORE=YES explicitly}"

die() { echo "restore refused: $*" >&2; exit 2; }
[ "$CONFIRM_RESTORE" = YES ] || die "CONFIRM_RESTORE must be YES"
case "$RESTORE_MODE" in synthetic|isolated) ;; *) die "unknown RESTORE_MODE" ;; esac
case "$RESTORE_TARGET_ID" in
  mobile_money_corpus_manager_v0_1|production|prod|"") die "production or empty restore target" ;;
  isolated-*|synthetic-*|synthetic) ;;
  *) die "restore target must be explicitly isolated or synthetic" ;;
esac
case "$TARGET_DATABASE_URL" in
  *mobile_money_corpus_manager_v0_1-db-1*|*mobile-money-corpus-db*|*://corpus@*|*://%2F*)
    die "production PostgreSQL target" ;;
esac
case "$RESTORE_MINIO_ENDPOINT" in
  *mobile_money_corpus_manager_v0_1*|*mobile-money-corpus-minio*|*corpus-moore.bencoherolab.com*)
    die "production MinIO or public endpoint" ;;
esac
case "$MINIO_ALIAS" in production|prod|"") die "ambiguous MinIO alias" ;; esac

BACKUP_PATH=$(realpath "$BACKUP_PATH") || die "backup path is not readable"
[ -d "$BACKUP_PATH" ] || die "backup path is not a directory"

# Validate the directory shape and select exactly one supported contract.
CONTRACT=$(python3 - "$BACKUP_PATH" <<'PY'
import json, os, pathlib, sys

root = pathlib.Path(sys.argv[1])
manifest_path = root / "MANIFEST.json"
if not manifest_path.is_file() or manifest_path.is_symlink():
    raise SystemExit("missing MANIFEST.json")

def safe(rel):
    p = pathlib.PurePosixPath(rel)
    return not p.is_absolute() and ".." not in p.parts and "\\" not in rel

for base, dirs, files in os.walk(root, followlinks=False):
    for name in dirs + files:
        full = pathlib.Path(base) / name
        rel = full.relative_to(root).as_posix()
        if not safe(rel) or full.is_symlink():
            raise SystemExit(f"unsafe or symlinked backup path: {rel}")

try:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
except Exception as exc:
    raise SystemExit(f"invalid MANIFEST.json: {exc}")

schema = manifest.get("schema")
if schema == 1:
    required = {"MANIFEST.json", "MANIFEST.SHA256", "SHA256SUMS",
                "postgres.dump", "minio", "minio_inventory.jsonl"}
    if {p.name for p in root.iterdir()} != required:
        raise SystemExit("schema 1 has missing or unexpected top-level entries")
    if manifest.get("postgres_dump") != "postgres.dump":
        raise SystemExit("schema 1 postgres_dump mismatch")
    if not isinstance(manifest.get("minio_file_count"), int):
        raise SystemExit("schema 1 minio_file_count missing")
    if not (root / "minio").is_dir():
        raise SystemExit("schema 1 minio directory missing")
    print(1)
elif schema == 2:
    required = {"MANIFEST.json", "COMPLETE", "COMPLETION.SHA256",
                "postgres", "minio", "manifests", "logs"}
    if {p.name for p in root.iterdir()} != required:
        raise SystemExit("schema 2 has missing or unexpected top-level entries")
    if manifest.get("status") != "COMPLETE":
        raise SystemExit("schema 2 is not COMPLETE")
    if manifest.get("postgres_dump") != "postgres/corpus.dump":
        raise SystemExit("schema 2 postgres_dump mismatch")
    if not isinstance(manifest.get("minio_object_count"), int):
        raise SystemExit("schema 2 minio_object_count missing")
    exact = {
        "postgres": {"corpus.dump"},
        "manifests": {"SHA256SUMS", "postgres_contents.txt",
                      "minio_source_count.txt", "minio_copy_count.txt"},
        "logs": {"postgres.log", "minio.log"},
    }
    for dirname, names in exact.items():
        if {p.name for p in (root / dirname).iterdir()} != names:
            raise SystemExit(f"schema 2 {dirname} has missing or unexpected entries")
    bucket = manifest.get("minio_bucket")
    if not isinstance(bucket, str) or not bucket or not safe(bucket):
        raise SystemExit("schema 2 invalid minio_bucket")
    bucket_dir = root / "minio" / bucket
    if not bucket_dir.is_dir() or {p.name for p in (root / "minio").iterdir()} != {bucket}:
        raise SystemExit("schema 2 MinIO bucket layout is ambiguous")
    print(2)
else:
    raise SystemExit("unknown backup contract schema")
PY
)

MANIFEST_BUCKET=$(python3 - "$BACKUP_PATH/MANIFEST.json" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
bucket = data.get("minio_bucket")
if not isinstance(bucket, str) or not bucket:
    raise SystemExit("manifest has no MinIO bucket")
print(bucket)
PY
)
[ "$MANIFEST_BUCKET" = "$MINIO_BUCKET" ] || die "requested bucket differs from manifest"

# A checksum file is not enough by itself: reject payload files that are not
# covered by it, and reject checksum entries that do not exist in the payload.
python3 - "$BACKUP_PATH" "$CONTRACT" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
contract = int(sys.argv[2])
checksum = root / ("SHA256SUMS" if contract == 1 else "manifests/SHA256SUMS")
covered = set()
for line in checksum.read_text(encoding="utf-8").splitlines():
    if not line or "  " not in line:
        raise SystemExit("invalid checksum manifest line")
    digest, rel = line.split("  ", 1)
    if len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
        raise SystemExit("invalid checksum digest")
    if not rel or pathlib.PurePosixPath(rel).is_absolute() or ".." in pathlib.PurePosixPath(rel).parts:
        raise SystemExit("unsafe checksum path")
    path = root / rel
    if not path.is_file() or path.is_symlink():
        raise SystemExit(f"checksum path missing: {rel}")
    covered.add(rel)
if contract == 1:
    actual = {"postgres.dump"}
    actual |= {(p.relative_to(root)).as_posix() for p in (root / "minio").rglob("*") if p.is_file()}
else:
    actual = {"MANIFEST.json"}
    for dirname in ("postgres", "minio", "manifests"):
        actual |= {(p.relative_to(root)).as_posix() for p in (root / dirname).rglob("*") if p.is_file() and p.name != "SHA256SUMS"}
if covered != actual:
    raise SystemExit(f"checksum coverage mismatch: covered={sorted(covered)} actual={sorted(actual)}")
PY

if [ "$CONTRACT" = 1 ]; then
  (cd "$BACKUP_PATH" && sha256sum -c MANIFEST.SHA256 >/dev/null) || die "schema 1 manifest checksum failed"
  (cd "$BACKUP_PATH" && sha256sum -c SHA256SUMS >/dev/null) || die "schema 1 content checksum failed"
  POSTGRES_DUMP="$BACKUP_PATH/postgres.dump"
  MINIO_SOURCE="$BACKUP_PATH/minio"
  EXPECTED_OBJECTS=$(python3 - "$BACKUP_PATH/MANIFEST.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["minio_file_count"])
PY
)
else
  (cd "$BACKUP_PATH" && sha256sum -c COMPLETION.SHA256 >/dev/null) || die "schema 2 completion checksum failed"
  (cd "$BACKUP_PATH" && sha256sum -c manifests/SHA256SUMS >/dev/null) || die "schema 2 content checksum failed"
  POSTGRES_DUMP="$BACKUP_PATH/postgres/corpus.dump"
  MINIO_SOURCE="$BACKUP_PATH/minio/$MANIFEST_BUCKET"
  EXPECTED_OBJECTS=$(python3 - "$BACKUP_PATH/MANIFEST.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["minio_object_count"])
PY
)
fi

[ -s "$POSTGRES_DUMP" ] || die "PostgreSQL archive missing or empty"
[ -d "$MINIO_SOURCE" ] || die "MinIO archive missing"
command -v pg_restore >/dev/null || die "pg_restore unavailable"
command -v mc >/dev/null || die "mc unavailable"

# The alias must resolve to the explicit isolated endpoint, not just have a safe name.
ALIAS_JSON=$(mc alias export "$MINIO_ALIAS") || die "cannot inspect MinIO alias"
python3 - "$ALIAS_JSON" "$RESTORE_MINIO_ENDPOINT" <<'PY'
import json, sys
try:
    data = json.loads(sys.argv[1])
except Exception as exc:
    raise SystemExit(f"invalid mc alias export: {exc}")
url = data.get("url") or data.get("URL")
if not isinstance(url, str) or url.rstrip("/") != sys.argv[2].rstrip("/"):
    raise SystemExit("MinIO alias endpoint does not match isolated endpoint")
PY

pg_restore --no-owner --clean --if-exists --dbname="$TARGET_DATABASE_URL" "$POSTGRES_DUMP"
mc mb --ignore-existing "$MINIO_ALIAS/$MINIO_BUCKET"
mc mirror --overwrite "$MINIO_SOURCE" "$MINIO_ALIAS/$MINIO_BUCKET"
ACTUAL_OBJECTS=$(mc ls --json --recursive "$MINIO_ALIAS/$MINIO_BUCKET" | wc -l | tr -d " ")
[ "$ACTUAL_OBJECTS" = "$EXPECTED_OBJECTS" ] || die "MinIO object count mismatch after restore"
printf "Restore completed for contract schema %s; run alembic current and scripts/reconcile.py.\n" "$CONTRACT"
