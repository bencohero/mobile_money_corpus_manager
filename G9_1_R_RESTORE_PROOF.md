# G9.1-R — Preuve de restauration isolée

Aucune cible isolée n’a été créée et aucune restauration n’a été exécutée.

## Conditions de cible

- projet Compose g91-r-restore ;
- réseau g91-r-restore-isolated ;
- volumes g91-r-restore-* uniquement ;
- PostgreSQL 16 et MinIO dédiés ;
- application release exacte ;
- aucun réseau frontend ou backend de production ;
- aucun volume de production monté ;
- commande app directe, sans migration.

Avant écriture :

~~~bash
docker compose -p g91-r-restore -f g91-r-restore.compose.yml config --quiet
docker network inspect g91-r-restore-isolated
docker volume ls --format '{{.Name}}' | grep '^g91-r-restore-'
~~~

Restaurer avec scripts/restore.sh depuis l’image tools G8.8-B, en mode
isolated, avec endpoint MinIO explicitement isolé et backup monté en lecture
seule. Vérifier PostgreSQL, MinIO, Alembic 0008, /ready et /health.

Commande de restore après création et inspection de la cible :

~~~bash
docker run --rm --network g91-r-restore-isolated \
  -v "$RUN:/backup:ro" -v "$PWD/scripts:/workspace/scripts:ro" \
  mobile-money-corpus-tools:g8-8-b-local bash -ceu '\
    mc alias set isolated http://g91-r-restore-minio:9000 "$MINIO_USER" "$MINIO_PASSWORD" >/dev/null; \
    env BACKUP_PATH=/backup TARGET_DATABASE_URL=postgresql://restore:REDACTED@g91-r-restore-db:5432/restore \
      RESTORE_MODE=isolated RESTORE_TARGET_ID=isolated-g9-1 MINIO_ALIAS=isolated \
      MINIO_BUCKET=mobile-money-corpus RESTORE_MINIO_ENDPOINT=http://g91-r-restore-minio:9000 \
      CONFIRM_RESTORE=YES /workspace/scripts/restore.sh'
~~~

Aucun alembic upgrade, redémarrage de production, migration ou ouverture
publique n’est inclus. Toute connexion de la cible vers production impose STOP.
