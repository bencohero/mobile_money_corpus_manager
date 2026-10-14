# G9.1 — Sauvegarde et validation

## Gel OPEN → DRAINING → FROZEN

Vérifier que l’image active contient réellement la gate :

~~~bash
docker exec "$APP" python -m app.write_freeze status
docker exec "$APP" python -m app.write_freeze check --phase OPEN
docker exec "$APP" python -m app.write_freeze freeze --timeout 60
docker exec "$APP" python -m app.write_freeze check --phase FROZEN
docker exec "$APP" python -m app.write_freeze status
~~~

La preuve doit montrer phase FROZEN et active_writes=0. Si le module ou l’état
partagé échoue, ou si le drain expire, STOP : ne pas forcer FROZEN.

## Capture schema 2

~~~bash
BACKUP_ROOT="$BACKUP_ROOT" \
BACKUP_MODE=production BACKUP_TARGET_ID=mobile_money_corpus_manager_v0_1 \
PG_CONTAINER="$DB" MINIO_CONTAINER="$MINIO" MINIO_BUCKET="$MINIO_BUCKET" \
MINIO_MC_IMAGE='quay.io/minio/aistor/mc@sha256:23511e340cbabf07e6a8b53f9c434975708f22f3c047d6beeddc17bf1a5aed88' \
BACKUP_CONFIRM=PRODUCTION_BACKUP_AUTHORIZED \
EXPECTED_PG_IMAGE_ID='sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685' \
EXPECTED_MINIO_SERVICE=minio EXPECTED_PG_SERVICE=db scripts/backup_local.sh
~~~

Le résultat doit contenir MANIFEST.json schema 2, COMPLETE,
COMPLETION.SHA256, postgres/corpus.dump, manifestes, journaux et
minio/<bucket>/. Un répertoire .run.*.incomplete n’est jamais transféré.

~~~bash
RUN=/var/backups/mobile-money-corpus/IDENTIFIANT
test -f "$RUN/COMPLETE"
(cd "$RUN" && sha256sum --check COMPLETION.SHA256)
(cd "$RUN" && sha256sum --check manifests/SHA256SUMS)
docker run --rm --network none -v "$RUN:/backup:ro" postgres:16-alpine \
  pg_restore --list /backup/postgres/corpus.dump >/dev/null
test "$(cat "$RUN/manifests/minio_source_count.txt")" = \
     "$(cat "$RUN/manifests/minio_copy_count.txt")"
~~~

Après validation, enregistrer les empreintes externes et ne pas supprimer
l’archive locale avant confirmation de la copie externe.

~~~bash
docker exec "$APP" python -m app.write_freeze check --phase FROZEN
docker exec "$APP" python -m app.write_freeze unfreeze
docker exec "$APP" python -m app.write_freeze check --phase OPEN
~~~

