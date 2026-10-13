# G9.1 — Restauration complète isolée

Utiliser un projet Compose, un réseau et des volumes dédiés à G9.1. Aucun nom
de volume, réseau, bucket, hostname ou secret de production ne doit être
réutilisé.

Préparer PostgreSQL 16, MinIO et l’image applicative exacte de la release. Le
service app démarre directement avec uvicorn : aucune commande alembic upgrade,
create_all ou migration ne doit être au démarrage.

~~~bash
docker compose -p g91-restore -f /path/to/g91-restore.compose.yml config --quiet
docker compose -p g91-restore -f /path/to/g91-restore.compose.yml up -d db minio
docker inspect g91-restore-db-1 g91-restore-minio-1
docker network inspect g91-restore-isolated
~~~

Configurer l’alias MinIO vers http://g91-restore-minio:9000, puis exécuter
scripts/restore.sh avec RESTORE_MODE=isolated, une cible isolated-*, l’URL
PostgreSQL g91-restore-db et l’image tools G8.8-B.

~~~bash
docker run --rm --network g91-restore-isolated \
  -v "$RUN:/backup:ro" -v "$PWD/scripts:/workspace/scripts:ro" \
  mobile-money-corpus-tools:g8-8-b-local \
  bash -ceu 'mc alias set isolated http://g91-restore-minio:9000 "$MINIO_USER" "$MINIO_PASSWORD" >/dev/null;
    env BACKUP_PATH=/backup TARGET_DATABASE_URL=postgresql://restore:REDACTED@g91-restore-db:5432/restore \
      RESTORE_MODE=isolated RESTORE_TARGET_ID=isolated-g9-1 MINIO_ALIAS=isolated \
      MINIO_BUCKET=mobile-money-corpus RESTORE_MINIO_ENDPOINT=http://g91-restore-minio:9000 \
      CONFIRM_RESTORE=YES /workspace/scripts/restore.sh'
~~~

Les credentials sont des placeholders et doivent être injectés sans être écrits
dans le dépôt ou les logs.

~~~bash
docker exec g91-restore-app-1 python -m alembic current
test "$(docker exec g91-restore-app-1 python -m alembic current | tr -d '\r')" = '0008_rate_limit_buckets (head)'
curl --fail --silent http://127.0.0.1:PORT/ready
curl --fail --silent http://127.0.0.1:PORT/health
docker exec g91-restore-app-1 python scripts/reconcile.py --json
~~~

Le contrôle doit produire [] et code 0. Toute migration implicite, readiness
défaillante ou connexion vers la production arrête la validation.
