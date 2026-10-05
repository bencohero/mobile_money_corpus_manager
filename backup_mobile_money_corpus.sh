#!/usr/bin/env bash
# Sauvegarde cohérente PostgreSQL + MinIO pour Mobile Money Corpus Manager.
#
# Prérequis : docker compose, mc (client MinIO), sha256sum et flock.
# L'alias MinIO doit déjà être configuré avec `mc alias set`.
# Le script ne supprime aucune sauvegarde et n'affiche aucun secret.

set -Eeuo pipefail
umask 077

SCRIPT_NAME="$(basename "$0")"
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/.env}"
REQUESTED_BACKUP_ROOT="${BACKUP_ROOT:-}"
REQUESTED_APP_SERVICE="${APP_SERVICE:-}"
REQUESTED_POSTGRES_SERVICE="${POSTGRES_SERVICE:-}"
REQUESTED_MINIO_ALIAS="${MINIO_ALIAS:-}"
REQUESTED_MINIO_BUCKET="${MINIO_BUCKET:-}"
REQUESTED_BACKUP_ID="${BACKUP_ID:-}"

usage() {
  cat <<EOF
Usage:
  PROJECT_DIR=/chemin/du/projet \\
  MINIO_ALIAS=corpus-minio \\
  MINIO_BUCKET=nom-du-bucket \\
  BACKUP_ROOT=/var/backups/mobile_money \\
  ./${SCRIPT_NAME}

Variables optionnelles :
  ENV_FILE           Fichier d'environnement (défaut : PROJECT_DIR/.env)
  APP_SERVICE        Service Docker Compose de l'application (défaut : app)
  POSTGRES_SERVICE   Service PostgreSQL (défaut : postgres)
  BACKUP_ID          Identifiant UTC personnalisé

Le script arrête uniquement APP_SERVICE pendant la sauvegarde puis le redémarre.
EOF
}

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

fail() {
  log "ERREUR : $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "commande introuvable : $1"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

for command_name in docker mc sha256sum flock find sort xargs; do
  require_command "$command_name"
done

[[ -d "$PROJECT_DIR" ]] || fail "répertoire du projet introuvable : $PROJECT_DIR"
cd "$PROJECT_DIR"

docker compose version >/dev/null 2>&1 || fail "Docker Compose n'est pas disponible"

# Charge le fichier sans afficher son contenu. Il doit respecter la syntaxe shell.
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

# Les variables fournies à l'invocation restent prioritaires sur .env.
BACKUP_ROOT="${REQUESTED_BACKUP_ROOT:-${BACKUP_ROOT:-/var/backups/mobile_money}}"
APP_SERVICE="${REQUESTED_APP_SERVICE:-${APP_SERVICE:-app}}"
POSTGRES_SERVICE="${REQUESTED_POSTGRES_SERVICE:-${POSTGRES_SERVICE:-postgres}}"
MINIO_ALIAS="${REQUESTED_MINIO_ALIAS:-${MINIO_ALIAS:-corpus-minio}}"
MINIO_BUCKET="${REQUESTED_MINIO_BUCKET:-${MINIO_BUCKET:-${CORPUS_BUCKET:-}}}"
BACKUP_ID="${REQUESTED_BACKUP_ID:-${BACKUP_ID:-$(date -u +%Y%m%dT%H%M%SZ)}}"
BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_ID}"
LOCK_FILE="${BACKUP_ROOT}/.backup.lock"
[[ -n "$MINIO_BUCKET" ]] || fail "MINIO_BUCKET (ou CORPUS_BUCKET) n'est pas défini"

install -d -m 700 "$BACKUP_ROOT"
exec 9>"$LOCK_FILE"
flock -n 9 || fail "une autre sauvegarde est déjà en cours"

[[ ! -e "$BACKUP_DIR" ]] || fail "la destination existe déjà : $BACKUP_DIR"
install -d -m 700 \
  "$BACKUP_DIR/postgres" \
  "$BACKUP_DIR/minio/$MINIO_BUCKET" \
  "$BACKUP_DIR/manifests" \
  "$BACKUP_DIR/logs"

PG_DUMP="$BACKUP_DIR/postgres/mobile_money.dump"
PG_LOG="$BACKUP_DIR/logs/postgres.log"
MINIO_LOG="$BACKUP_DIR/logs/minio.log"
APP_WAS_RUNNING=0

compose() {
  docker compose "$@"
}

restore_application() {
  local exit_code=$?
  trap - EXIT INT TERM

  if [[ "$APP_WAS_RUNNING" -eq 1 ]]; then
    log "Redémarrage du service applicatif ${APP_SERVICE}"
    if ! compose start "$APP_SERVICE" >/dev/null; then
      log "ERREUR : impossible de redémarrer ${APP_SERVICE}" >&2
      [[ "$exit_code" -ne 0 ]] || exit_code=1
    fi
  fi

  if [[ "$exit_code" -ne 0 ]]; then
    log "Sauvegarde incomplète : ${BACKUP_DIR}" >&2
  fi
  exit "$exit_code"
}

trap restore_application EXIT INT TERM

compose config --quiet
compose ps --status running --services | grep -Fxq "$POSTGRES_SERVICE" \
  || fail "le service PostgreSQL ${POSTGRES_SERVICE} n'est pas démarré"

mc alias list "$MINIO_ALIAS" >/dev/null 2>&1 \
  || fail "alias MinIO introuvable : ${MINIO_ALIAS}"
mc stat "${MINIO_ALIAS}/${MINIO_BUCKET}" >/dev/null 2>&1 \
  || fail "bucket MinIO inaccessible : ${MINIO_ALIAS}/${MINIO_BUCKET}"

if compose ps --status running --services | grep -Fxq "$APP_SERVICE"; then
  APP_WAS_RUNNING=1
  log "Mise en maintenance : arrêt du service ${APP_SERVICE}"
  compose stop "$APP_SERVICE" >/dev/null
else
  log "Le service ${APP_SERVICE} était déjà arrêté"
fi

log "Sauvegarde PostgreSQL au format custom"
if ! compose exec -T "$POSTGRES_SERVICE" sh -ceu \
  'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  >"$PG_DUMP" 2>"$PG_LOG"; then
  fail "échec de pg_dump ; consulter ${PG_LOG}"
fi
[[ -s "$PG_DUMP" ]] || fail "le dump PostgreSQL est vide"

log "Validation de l'archive PostgreSQL"
if ! compose exec -T "$POSTGRES_SERVICE" pg_restore --list \
  <"$PG_DUMP" >"$BACKUP_DIR/manifests/postgres_contents.txt" \
  2>>"$PG_LOG"; then
  fail "l'archive PostgreSQL n'est pas lisible par pg_restore"
fi

log "Sauvegarde du bucket MinIO ${MINIO_BUCKET}"
if ! mc mirror --overwrite \
  "${MINIO_ALIAS}/${MINIO_BUCKET}" \
  "$BACKUP_DIR/minio/$MINIO_BUCKET" \
  >"$MINIO_LOG" 2>&1; then
  fail "échec de la sauvegarde MinIO ; consulter ${MINIO_LOG}"
fi

log "Vérification du nombre d'objets MinIO"
SOURCE_OBJECTS="$(mc find "${MINIO_ALIAS}/${MINIO_BUCKET}" --type f | wc -l | tr -d ' ')"
BACKUP_OBJECTS="$(find "$BACKUP_DIR/minio/$MINIO_BUCKET" -type f | wc -l | tr -d ' ')"
[[ "$SOURCE_OBJECTS" == "$BACKUP_OBJECTS" ]] \
  || fail "nombre d'objets différent : source=${SOURCE_OBJECTS}, sauvegarde=${BACKUP_OBJECTS}"

log "Création du manifeste"
{
  printf 'backup_id=%s\n' "$BACKUP_ID"
  printf 'created_at_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'project_dir=%s\n' "$PROJECT_DIR"
  printf 'postgres_service=%s\n' "$POSTGRES_SERVICE"
  printf 'postgres_format=custom\n'
  printf 'minio_alias=%s\n' "$MINIO_ALIAS"
  printf 'minio_bucket=%s\n' "$MINIO_BUCKET"
  printf 'minio_backup_mode=mc_mirror_latest_objects\n'
  printf 'minio_source_objects=%s\n' "$SOURCE_OBJECTS"
  printf 'minio_backup_objects=%s\n' "$BACKUP_OBJECTS"
  printf 'application_was_stopped=%s\n' "$APP_WAS_RUNNING"
} >"$BACKUP_DIR/manifests/metadata.txt"

compose images >"$BACKUP_DIR/manifests/docker_images.txt"
printf 'completed_at_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  >"$BACKUP_DIR/manifests/SUCCESS"

log "Calcul des empreintes SHA-256"
(
  cd "$BACKUP_DIR"
  find postgres minio manifests logs \
    -type f ! -name sha256sums.txt -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    >manifests/sha256sums.txt
  sha256sum --check manifests/sha256sums.txt >/dev/null
)

log "Sauvegarde terminée : ${BACKUP_DIR}"
log "PostgreSQL : $(du -h "$PG_DUMP" | cut -f1)"
log "MinIO : ${BACKUP_OBJECTS} objets"
