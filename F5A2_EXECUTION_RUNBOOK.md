# F.5A.2 — Runbook d’exécution proposé

Ce runbook n’a pas été exécuté sur la production. Il suppose qu’une image déployée et vérifiée contient le garde d’écriture, et qu’une autorisation explicite a été reçue.

## 1. Variables et cible

```bash
set -Eeuo pipefail
umask 077
PROJECT=/home/sangouman/apps/mobile_money_corpus_manager_v0_1
BACKUP_ROOT=/var/backups/mobile-money-corpus
BACKUP_ID="$(date -u +%Y%m%dT%H%M%SZ)"
PG_CONTAINER=mobile_money_corpus_manager_v0_1-db-1
MINIO_CONTAINER=mobile_money_corpus_manager_v0_1-minio-1
APP_CONTAINER=mobile_money_corpus_manager_v0_1-app-1
MINIO_BUCKET=mobile-money-corpus
MINIO_MC_IMAGE=quay.io/minio/aistor/mc@sha256:23511e340cbabf07e6a8b53f9c434975708f22f3c047d6beeddc17bf1a5aed88
EXPECTED_PG_IMAGE_ID=sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685
EXPECTED_MINIO_IMAGE_ID=sha256:a1ea29fa28355559ef137d71fc570e508a214ec84ff8083e39bc5428980b015e
```

Charger les variables d’environnement sans les imprimer. Ne jamais utiliser le PostgreSQL 18 publié sur le port hôte.

## 2. Contrôles avant gel

```bash
test "$PWD" = "$PROJECT"
test ! -e "$BACKUP_ROOT/$BACKUP_ID"
test ! -e "$BACKUP_ROOT/.run.$BACKUP_ID.incomplete"
test "$(docker inspect -f '{{.Image}}' "$PG_CONTAINER")" = "$EXPECTED_PG_IMAGE_ID"
test "$(docker inspect -f '{{.Image}}' "$MINIO_CONTAINER")" = "$EXPECTED_MINIO_IMAGE_ID"
test "$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$PG_CONTAINER")" = mobile_money_corpus_manager_v0_1
test "$(docker inspect -f '{{index .Config.Labels "com.docker.compose.service"}}' "$PG_CONTAINER")" = db
test "$(docker inspect -f '{{index .Config.Labels "com.docker.compose.service"}}' "$MINIO_CONTAINER")" = minio
docker exec "$PG_CONTAINER" sh -lc 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker exec "$MINIO_CONTAINER" sh -lc 'curl -fsS http://localhost:9000/minio/health/live >/dev/null'
docker exec "$APP_CONTAINER" python -m alembic current
df -h /var/backups /
pgrep -af 'pg_dump|pg_restore|mc mirror|rclone|restic|borg' && exit 2 || true
```

Vérifier aussi que l’image applicative contient `/app/app/write_freeze.py` et que son SHA-256 est celui approuvé. Sinon, arrêter la procédure.

## 3. Geler et drainer

```bash
docker exec "$APP_CONTAINER" python -m app.write_freeze freeze --timeout 120
test "$(docker exec "$APP_CONTAINER" python -m app.write_freeze status)" = '{"active_writes": 0, "epoch": 1, "phase": "FROZEN"}'
```

Le gel doit rester `FROZEN` pendant toute la capture. Ne pas arrêter le conteneur, ne pas modifier Traefik et ne pas appeler Alembic.

## 4. Capturer

```bash
export BACKUP_ROOT BACKUP_MODE=production BACKUP_TARGET_ID=mobile_money_corpus_manager_v0_1
export PG_CONTAINER MINIO_CONTAINER MINIO_BUCKET MINIO_MC_IMAGE
export EXPECTED_PG_IMAGE_ID EXPECTED_MINIO_IMAGE_ID
export WRITE_FREEZE_ATTESTED=YES
export BACKUP_CONFIRM=PRODUCTION_BACKUP_AUTHORIZED
"$PROJECT/scripts/backup_local.sh"
```

Le script crée `/var/backups/mobile-money-corpus/.run.<UTC>.incomplete`, ne l’écrase jamais, puis le renomme en archive finale uniquement après vérifications. Il produit un dump PostgreSQL custom, un catalogue, une copie MinIO, des comptages anonymes, `MANIFEST.json`, `SHA256SUMS`, `COMPLETE` et `COMPLETION.SHA256`.

## 5. Contrôler avant reprise

```bash
ARCHIVE="$BACKUP_ROOT/$BACKUP_ID"
test -f "$ARCHIVE/COMPLETE"
test "$(sed -n '1p' "$ARCHIVE/COMPLETE")" = status=COMPLETE
(cd "$ARCHIVE" && sha256sum --check manifests/SHA256SUMS && sha256sum --check COMPLETION.SHA256)
docker exec "$APP_CONTAINER" python scripts/reconcile.py --json >"$ARCHIVE/manifests/post_capture_reconcile.json"
```

Le rapport de réconciliation doit être vide. Toute erreur conserve le gel, marque l’archive incomplète et déclenche une revue ; aucune reprise automatique ne doit avoir lieu.

## 6. Reprendre et contrôler

```bash
docker exec "$APP_CONTAINER" python -m app.write_freeze unfreeze
docker exec "$APP_CONTAINER" python -m app.write_freeze status
docker inspect --format '{{.Name}} {{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$APP_CONTAINER" "$PG_CONTAINER" "$MINIO_CONTAINER"
docker exec "$APP_CONTAINER" curl -fsS http://localhost:8000/ready >/dev/null
```

L’impact attendu est une courte indisponibilité des écritures et des réponses `503` pendant le gel. La durée finale doit être confirmée par une répétition synthétique représentative, pas déduite de la seule absence d’erreur.

## 7. Échecs et reprise opérationnelle

- Échec avant publication : conserver le dossier `.incomplete`, ne pas le renommer, relever uniquement code retour, phase et compteurs.
- Échec PostgreSQL ou MinIO : maintenir `FROZEN`, vérifier les logs sans secrets, puis décider reprise ou nouvelle capture complète.
- Échec du gel : rester en `DRAINING`, identifier la requête active ; ne jamais capturer en état non nul.
- Échec après publication mais avant reprise : archive valide conservée, service toujours gelé jusqu’à décision.
- Reprise uniquement après SHA-256, comptages, catalogue PostgreSQL et réconciliation validés.
