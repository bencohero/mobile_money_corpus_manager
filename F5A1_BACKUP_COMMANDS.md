# F.5A.1 — Commandes proposées (ne pas exécuter avant approbation)

Ce document est un runbook de revue. Les blocs sont intentionnellement non exécutés dans ce ticket. Ils ciblent explicitement les conteneurs de production et refusent le dépôt comme destination.

## Variables opérateur

```bash
set -Eeuo pipefail
umask 077
PROJECT=/home/sangouman/apps/mobile_money_corpus_manager_v0_1
set -a
source "$PROJECT/.env"
set +a
BACKUP_ROOT=/var/backups/mobile-money-corpus
BACKUP_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_TMP="$BACKUP_ROOT/.run.$BACKUP_ID.tmp"
RUN_FINAL="$BACKUP_ROOT/$BACKUP_ID"
DB=mobile_money_corpus_manager_v0_1-db-1
MINIO=mobile_money_corpus_manager_v0_1-minio-1
APP=mobile_money_corpus_manager_v0_1-app-1
BUCKET=mobile-money-corpus
EXPECTED_DB_IMAGE_ID=sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685
EXPECTED_MINIO_IMAGE_ID=sha256:a1ea29fa28355559ef137d71fc570e508a214ec84ff8083e39bc5428980b015e
EXPECTED_APP_IMAGE_ID=sha256:c2e3e50e3e74d2901cbe5308b77ac9c4d0dab660668b836f6bda4b23a49f2467
```

## Contrôles obligatoires avant confirmation

```bash
test "$BACKUP_ROOT" = /var/backups/mobile-money-corpus
test ! -e "$RUN_FINAL" && test ! -e "$RUN_TMP"
test "$PWD" = "$PROJECT"
docker inspect --format '{{.Name}} {{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$APP" "$DB" "$MINIO"
test "$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$DB")" = mobile_money_corpus_manager_v0_1
test "$(docker inspect -f '{{index .Config.Labels "com.docker.compose.service"}}' "$DB")" = db
test "$(docker inspect -f '{{index .Config.Labels "com.docker.compose.service"}}' "$MINIO")" = minio
test "$(docker inspect -f '{{index .Config.Labels "com.docker.compose.service"}}' "$APP")" = app
test "$(docker inspect -f '{{.Image}}' "$DB")" = "$EXPECTED_DB_IMAGE_ID"
test "$(docker inspect -f '{{.Image}}' "$MINIO")" = "$EXPECTED_MINIO_IMAGE_ID"
test "$(docker inspect -f '{{.Image}}' "$APP")" = "$EXPECTED_APP_IMAGE_ID"
case "$(docker inspect -f '{{range .Mounts}}{{.Name}}={{.Destination}} {{end}}' "$DB")" in *mobile_money_corpus_manager_v0_1_pgdata=/var/lib/postgresql/data\ *) ;; *) exit 1 ;; esac
case "$(docker inspect -f '{{range .Mounts}}{{.Name}}={{.Destination}} {{end}}' "$MINIO")" in *mobile_money_corpus_manager_v0_1_miniodata=/data\ *) ;; *) exit 1 ;; esac
docker exec "$DB" sh -lc 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker exec "$MINIO" sh -lc 'curl -fsS http://localhost:9000/minio/health/live >/dev/null'
docker exec "$APP" python -m alembic current
df -h /var/backups /
test "$(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)" -ge 0
```

Les valeurs d’environnement doivent être injectées sans les imprimer. La commande doit aussi comparer les digests complets à ceux approuvés dans la fiche de changement, et vérifier que le PostgreSQL hôte `postgres:18` n’est jamais utilisé.

## Gel et drain — précondition non satisfaite aujourd’hui

```bash
# À remplacer par le mécanisme de maintenance validé, jamais improvisé.
# Exiger : nouvelles écritures refusées, requêtes en vol = 0, workers = 0.
test "$WRITE_FREEZE_VALIDATED" = YES
test "$WRITE_DRAIN_CONFIRMED" = YES
```

Ne pas utiliser `docker compose stop app` comme preuve de drain. Ne pas activer ou modifier Traefik dans cette procédure.

## Capture proposée après validation du gel

```bash
install -d -m 700 "$BACKUP_ROOT" "$RUN_TMP/postgres" "$RUN_TMP/minio/$BUCKET" "$RUN_TMP/manifests" "$RUN_TMP/logs"
test ! -e "$RUN_FINAL"

# Comptages sans identifiants ni contenu textuel.
docker exec "$DB" sh -lc 'for t in participants users workshops workshop_codes recordings recording_submissions recording_take_counters transcriptions audit_logs; do printf "%s=" "$t"; psql -X -qAt -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select count(*) from public.$t"; done' > "$RUN_TMP/manifests/counts.txt"

# Dump PostgreSQL ciblant explicitement le conteneur production.
docker exec "$DB" sh -ceu 'pg_dump --format=custom --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$RUN_TMP/postgres/corpus.dump"
test -s "$RUN_TMP/postgres/corpus.dump"
docker exec "$DB" pg_restore --list < "$RUN_TMP/postgres/corpus.dump" > "$RUN_TMP/manifests/postgres_contents.txt"

# Miroir MinIO à réaliser avec un client mc épinglé et des identifiants injectés,
# connecté au réseau du conteneur MINIO (endpoint 127.0.0.1:9000) et au bucket exact.
# Le client doit échouer si le bucket ou l’endpoint ne correspondent pas.
docker run --rm --network "container:$MINIO" \
  --volume "$RUN_TMP/minio:/backup" \
  --env MINIO_ROOT_USER --env MINIO_ROOT_PASSWORD \
  minio/mc:<digest-approuvé> sh -ceu \
  'mc alias set prod http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
   mc stat "prod/'"$BUCKET"'" >/dev/null
   mc mirror "prod/'"$BUCKET"'" /backup/'"$BUCKET"''

# Inventaire et comptage côté source/copie, sans afficher les noms.
docker run --rm --network "container:$MINIO" --env MINIO_ROOT_USER --env MINIO_ROOT_PASSWORD minio/mc:<digest-approuvé> sh -ceu \
  'mc alias set prod http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null; mc ls --recursive --json "prod/'"$BUCKET"'" | wc -l' > "$RUN_TMP/manifests/minio_source_count.txt"
find "$RUN_TMP/minio/$BUCKET" -type f | wc -l > "$RUN_TMP/manifests/minio_copy_count.txt"
test "$(tr -d ' ' < "$RUN_TMP/manifests/minio_source_count.txt")" = "$(tr -d ' ' < "$RUN_TMP/manifests/minio_copy_count.txt")"

printf 'target_project=mobile_money_corpus_manager_v0_1\npostgres_container=%s\nminio_container=%s\npostgres_database=corpus\nminio_bucket=%s\ncoherence=validated_write_freeze_required\n' "$DB" "$MINIO" "$BUCKET" > "$RUN_TMP/manifests/metadata.txt"
find "$RUN_TMP/postgres" "$RUN_TMP/minio" "$RUN_TMP/manifests" -type f -print0 | sort -z | xargs -0 sha256sum > "$RUN_TMP/manifests/SHA256SUMS"
sha256sum --check "$RUN_TMP/manifests/SHA256SUMS"

# Publication atomique : aucune archive existante n’est réécrite.
mv --no-clobber "$RUN_TMP" "$RUN_FINAL"
chmod -R go-rwx "$RUN_FINAL"
```

## Vérification et reprise

```bash
test -d "$RUN_FINAL"
sha256sum --check "$RUN_FINAL/manifests/SHA256SUMS"
docker exec "$APP" python scripts/reconcile.py --json > "$RUN_FINAL/manifests/post_capture_reconcile.json"
# Vérifier le code retour et les états des trois conteneurs avant reprise.
docker inspect --format '{{.Name}} {{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$APP" "$DB" "$MINIO"
# Reprise uniquement après validation du rapport et du drain inverse.
```

Un échec laisse `RUN_TMP` isolé et doit être signalé comme sauvegarde incomplète ; il ne doit jamais être renommé en archive validée ni écraser un run existant. Aucun `restore.sh` n’est inclus dans le flux de production.
