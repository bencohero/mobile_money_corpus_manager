#!/usr/bin/env bash
set -euo pipefail

# Offline-style harness: fake pg_dump/pg_restore/mc operate only on temp files.
# It proves target guards, manifest creation, hashes and isolated restore flow.
root=$(mktemp -d); bin="$root/bin"; source="$root/source"; restore="$root/restore"
mkdir -p "$bin" "$source/minio" "$restore"
trap 'rm -rf "$root"' EXIT
printf 'synthetic postgres\n' > "$source/seed.sql"
printf 'synthetic audio\n' > "$source/audio.wav"

cat > "$bin/pg_dump" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
out=""
for arg in "$@"; do case "$arg" in --file=*) out=${arg#--file=};; esac; done
printf 'synthetic postgres dump\n' > "$out"
SH
cat > "$bin/pg_restore" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf 'synthetic restore invoked\n' > "${RESTORE_MARKER:?}"
SH
cat > "$bin/mc" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
case "$1" in
  alias) exit 0 ;;
  mirror)
    src="${@: -2:1}"; dst="${@: -1}"
    if [ -d "$src" ]; then :; else mkdir -p "$dst"; printf 'synthetic audio\n' > "$dst/audio.wav"; fi
    ;;
  ls) printf '{"key":"audio.wav","size":16}\n' ;;
  *) echo "unsupported synthetic mc operation" >&2; exit 1 ;;
esac
SH
chmod 750 "$bin"/pg_dump "$bin"/pg_restore "$bin"/mc

backup_dir="$root/backups"
export PATH="$bin:$PATH" BACKUP_DIR="$backup_dir" BACKUP_MODE=synthetic BACKUP_TARGET_ID=synthetic
export POSTGRES_DB=synthetic POSTGRES_USER=synthetic PGHOST=synthetic-db
export MINIO_ALIAS=synthetic MINIO_ENDPOINT=synthetic:9000 MINIO_ACCESS_KEY=synthetic MINIO_SECRET_KEY=synthetic MINIO_BUCKET=synthetic
backup_output=$(scripts/backup.sh)
backup_path=${backup_output##* }
[ -f "$backup_path/MANIFEST.json" ]
[ -f "$backup_path/MANIFEST.SHA256" ]
[ -f "$backup_path/minio/audio.wav" ]
export RESTORE_MODE=synthetic RESTORE_TARGET_ID=synthetic CONFIRM_RESTORE=YES
export TARGET_DATABASE_URL=postgresql://synthetic/restore RESTORE_MARKER="$root/restored"
restore_output=$(BACKUP_PATH="$backup_path" scripts/restore.sh)
[ -f "$RESTORE_MARKER" ]
printf 'synthetic backup/restore passed: %s\n' "$restore_output"
