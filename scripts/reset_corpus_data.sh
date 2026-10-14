#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
ENV_FILE="${ENV_FILE:-.env}"
MC_IMAGE="${MC_IMAGE:-minio/mc:latest}"
BACKUP_ROOT="${BACKUP_ROOT:-./backups}"

APP_SERVICE="app"
DB_SERVICE="db"
MINIO_SERVICE="minio"

EXPECTED_CONFIRMATION="PURGER-CORPUS-ET-PARTICIPANTS"

log() {
    printf '[%s] %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}

fail() {
    log "ERREUR : $*" >&2
    exit 1
}

command -v docker >/dev/null 2>&1 ||
    fail "Docker est introuvable."

docker compose version >/dev/null 2>&1 ||
    fail "Docker Compose est indisponible."

[[ -f "$COMPOSE_FILE" ]] ||
    fail "Fichier Compose introuvable : $COMPOSE_FILE"

[[ -f "$ENV_FILE" ]] ||
    fail "Fichier d'environnement introuvable : $ENV_FILE"

# Charge les variables sans les afficher.
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

required_variables=(
    POSTGRES_DB
    POSTGRES_USER
    MINIO_BUCKET
    MINIO_ROOT_USER
    MINIO_ROOT_PASSWORD
)

for variable in "${required_variables[@]}"; do
    [[ -n "${!variable:-}" ]] ||
        fail "Variable obligatoire absente : $variable"
done

services="$(docker compose -f "$COMPOSE_FILE" ps --services)"

for service in "$APP_SERVICE" "$DB_SERVICE" "$MINIO_SERVICE"; do
    grep -Fxq "$service" <<< "$services" ||
        fail "Service Compose introuvable : $service"
done

DB_CONTAINER="$(docker compose -f "$COMPOSE_FILE" ps -q "$DB_SERVICE")"
MINIO_CONTAINER="$(docker compose -f "$COMPOSE_FILE" ps -q "$MINIO_SERVICE")"

[[ -n "$DB_CONTAINER" ]] ||
    fail "Le conteneur PostgreSQL n'est pas démarré."

[[ -n "$MINIO_CONTAINER" ]] ||
    fail "Le conteneur MinIO n'est pas démarré."

timestamp="$(date -u +'%Y%m%dT%H%M%SZ')"
BACKUP_DIR="${BACKUP_ROOT}/before_corpus_reset_${timestamp}"
PG_BACKUP="${BACKUP_DIR}/postgres.dump"
MINIO_BACKUP_DIR="${BACKUP_DIR}/minio"
MINIO_INVENTORY="${BACKUP_DIR}/minio_inventory.jsonl"

mkdir -p "$MINIO_BACKUP_DIR"

app_stopped=0

restart_app() {
    if [[ "$app_stopped" -eq 1 ]]; then
        log "Redémarrage du service application..."
        docker compose -f "$COMPOSE_FILE" start "$APP_SERVICE" >/dev/null || true
    fi
}

trap restart_app EXIT

log "Arrêt temporaire de l'application..."
docker compose -f "$COMPOSE_FILE" stop "$APP_SERVICE"
app_stopped=1

log "Création de la sauvegarde PostgreSQL..."

docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        --format=custom \
        --no-owner \
        --no-acl \
        --username="$POSTGRES_USER" \
        --dbname="$POSTGRES_DB"' \
    > "$PG_BACKUP"

[[ -s "$PG_BACKUP" ]] ||
    fail "La sauvegarde PostgreSQL est vide."

log "Vérification de la structure de la sauvegarde PostgreSQL..."

docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" \
    pg_restore --list < "$PG_BACKUP" >/dev/null

log "Sauvegarde PostgreSQL valide."

log "Vérification de l'image Docker MinIO Client..."
docker image inspect "$MC_IMAGE" >/dev/null 2>&1 ||
    docker pull "$MC_IMAGE"

run_mc() {
    docker run --rm \
        --network "container:${MINIO_CONTAINER}" \
        --volume "$(realpath "$MINIO_BACKUP_DIR"):/backup" \
        --env MINIO_ROOT_USER \
        --env MINIO_ROOT_PASSWORD \
        --env MINIO_BUCKET \
        --entrypoint /bin/sh \
        "$MC_IMAGE" \
        -c '
            set -eu
            mc alias set local \
                http://127.0.0.1:9000 \
                "$MINIO_ROOT_USER" \
                "$MINIO_ROOT_PASSWORD" >/dev/null
            "$@"
        ' sh "$@"
}

log "Vérification du bucket MinIO..."
run_mc mc stat "local/${MINIO_BUCKET}" >/dev/null

log "Inventaire des objets MinIO..."
run_mc mc ls --recursive --json "local/${MINIO_BUCKET}" \
    > "$MINIO_INVENTORY"

log "Copie des objets MinIO..."
run_mc mc mirror \
    --overwrite \
    "local/${MINIO_BUCKET}" \
    "/backup/${MINIO_BUCKET}"

source_object_count="$(wc -l < "$MINIO_INVENTORY" | tr -d ' ')"
backup_file_count="$(
    find "${MINIO_BACKUP_DIR}/${MINIO_BUCKET}" -type f 2>/dev/null |
        wc -l |
        tr -d ' '
)"

log "Objets inventoriés dans MinIO : ${source_object_count}"
log "Fichiers copiés localement       : ${backup_file_count}"

if [[ "$source_object_count" -ne "$backup_file_count" ]]; then
    fail "Le nombre d'objets sauvegardés ne correspond pas à l'inventaire."
fi

(
    cd "$BACKUP_DIR"
    sha256sum postgres.dump > SHA256SUMS
    find "minio/${MINIO_BUCKET}" -type f -print0 |
        sort -z |
        xargs -0 -r sha256sum >> SHA256SUMS
)

log "Sauvegardes créées dans : $BACKUP_DIR"
log "Aucune donnée n'a encore été supprimée."

printf '\nCette opération supprimera définitivement :\n'
printf '  - les participants ;\n'
printf '  - les enregistrements et transcriptions ;\n'
printf '  - les compteurs de prises et reçus de soumission ;\n'
printf '  - tous les objets du bucket MinIO "%s".\n\n' "$MINIO_BUCKET"
printf 'Les utilisateurs, intentions, migrations et le bucket seront conservés.\n\n'
printf 'Pour confirmer, saisissez exactement : %s\n> ' "$EXPECTED_CONFIRMATION"

read -r confirmation

[[ "$confirmation" == "$EXPECTED_CONFIRMATION" ]] ||
    fail "Confirmation incorrecte : purge annulée."

log "Vérification des tables PostgreSQL attendues..."

required_tables=(
    participants
    recordings
    transcriptions
    recording_take_counters
    recording_submissions
)

for table in "${required_tables[@]}"; do
    sql_query="SELECT to_regclass('public.${table}') IS NOT NULL;"

    exists="$(
        docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" sh -c \
            'PGPASSWORD="$POSTGRES_PASSWORD" psql \
                --username="$POSTGRES_USER" \
                --dbname="$POSTGRES_DB" \
                --tuples-only \
                --no-align \
                --command="$1"' \
            sh "$sql_query" |
            tr -d '[:space:]'
    )"

    if [[ "$exists" != "t" ]]; then
        fail "Table attendue absente : public.${table}. Aucune purge effectuée."
    fi
done

log "Suppression transactionnelle des données PostgreSQL..."

docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" psql \
        --set=ON_ERROR_STOP=1 \
        --username="$POSTGRES_USER" \
        --dbname="$POSTGRES_DB"' <<'SQL'
BEGIN;

TRUNCATE TABLE
    public.transcriptions,
    public.recording_submissions,
    public.recordings,
    public.recording_take_counters,
    public.participants
RESTART IDENTITY CASCADE;

COMMIT;
SQL

log "Vidage des objets MinIO..."

run_mc mc rm \
    --recursive \
    --force \
    --dangerous \
    "local/${MINIO_BUCKET}"

log "Contrôle PostgreSQL après purge..."

docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" psql \
        --username="$POSTGRES_USER" \
        --dbname="$POSTGRES_DB" \
        --command="
            SELECT '\''participants'\'' AS table_name, COUNT(*) FROM public.participants
            UNION ALL
            SELECT '\''recordings'\'', COUNT(*) FROM public.recordings
            UNION ALL
            SELECT '\''transcriptions'\'', COUNT(*) FROM public.transcriptions
            UNION ALL
            SELECT '\''recording_take_counters'\'', COUNT(*) FROM public.recording_take_counters
            UNION ALL
            SELECT '\''recording_submissions'\'', COUNT(*) FROM public.recording_submissions;
        "'

log "Contrôle MinIO après purge..."
remaining_objects="$(
    run_mc mc ls --recursive --json "local/${MINIO_BUCKET}" |
        wc -l |
        tr -d ' '
)"

if [[ "$remaining_objects" -ne 0 ]]; then
    fail "${remaining_objects} objet(s) subsistent dans MinIO."
fi

log "Purge terminée."
log "Le bucket MinIO a été conservé."
log "Sauvegarde de récupération : $BACKUP_DIR"
