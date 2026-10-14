# G9.1 — Précontrôle avant sauvegarde finale

Runbook préparatoire uniquement. Les commandes ne sont pas exécutées dans G9.1.
Toute commande contactant la production, créant une archive ou modifiant le gel
exige une approbation opérateur distincte.

Références : release 8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6, Alembic
0008_rate_limit_buckets, projet mobile_money_corpus_manager_v0_1.

~~~bash
set -Eeuo pipefail
PROJECT=mobile_money_corpus_manager_v0_1
APP="$PROJECT-app-1"; DB="$PROJECT-db-1"; MINIO="$PROJECT-minio-1"
RELEASE=8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6
BACKUP_ROOT=/var/backups/mobile-money-corpus
MINIO_BUCKET=mobile-money-corpus
docker inspect --type=container "$APP" "$DB" "$MINIO"
test "$(docker inspect -f '{{.State.Status}}' "$DB")" = running
test "$(docker inspect -f '{{.State.Status}}' "$MINIO")" = running
test "$(docker inspect -f '{{.Config.Image}}' "$APP")" = "mobile_money_corpus_manager_g8_5_r:$RELEASE"
docker exec "$APP" python -m alembic current
test "$(docker exec "$APP" python -m alembic current | tr -d '\r')" = '0008_rate_limit_buckets (head)'
docker volume inspect "$PROJECT"_pgdata "$PROJECT"_miniodata "$PROJECT"_tmpaudio
docker network inspect "$PROJECT"_backend frontend
df -h "$BACKUP_ROOT"
test -d "$BACKUP_ROOT" && test "$(stat -c '%a' "$BACKUP_ROOT")" = 700
~~~

Refuser si l’image, le schéma, les services, les volumes, le réseau ou la
destination diffèrent. Ne pas appliquer de migration pour rendre le contrôle
passant.

~~~bash
docker exec "$DB" sh -ceu \
  'psql -AtX -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
   "select count(*) from pg_stat_activity where datname=current_database() and pid<>pg_backend_pid()"'
docker exec "$DB" sh -ceu \
  'psql -AtX -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
   "select version_num from alembic_version"'
~~~

Capturer hors dépôt release, état des services, volumes/réseaux, révision
Alembic, compteurs des tables métier et inventaire MinIO JSON, sans secrets.

~~~bash
docker run --rm --network none mobile-money-corpus-tools:g8-8-b-local \
  sh -ceu 'python3 --version; pg_restore --version; mc --version; sha256sum --version | head -1'
bash -n scripts/backup_local.sh scripts/restore.sh
bash tests/test_restore_contract.sh
~~~

