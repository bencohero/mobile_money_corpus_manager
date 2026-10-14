# F5A4 — runbook corrigé de déploiement contrôlé

Ce runbook est préparatoire. Les commandes ci-dessous n’ont pas été exécutées sur la production.

## Références figées

```bash
set -Eeuo pipefail
PROJECT='mobile_money_corpus_manager_v0_1'
OLD_APP="${PROJECT}-app-1"
DB="${PROJECT}-db-1"
MINIO="${PROJECT}-minio-1"
CANDIDATE='f5a4-candidate@sha256:b1fb0b134d00cdcd02acab3c020163fec94f2cfb8e0bf3042087a8f5610de778'
STATE_HOST='/var/lib/mobile-money-corpus/write-freeze'
STATE_CONTAINER='/freeze-state/state.json'
DEST='/var/backups/mobile-money-corpus'
```

Image actuellement active : `sha256:c2e3e50e3e74d2901cbe5308b77ac9c4d0dab660668b836f6bda4b23a49f2467`.
Candidate F5A4 : `sha256:b1fb0b134d00cdcd02acab3c020163fec94f2cfb8e0bf3042087a8f5610de778`.

## Précontrôles sans appeler l’ancienne gate

L’image active ne contient pas `app.write_freeze`. Le contrôle Alembic doit donc être exécuté depuis l’application active, et non depuis `db` et non via `app.write_freeze` :

```bash
docker inspect --type=container "$OLD_APP" "$DB" "$MINIO"
docker inspect --type=image "$CANDIDATE"
docker exec "$OLD_APP" python -m alembic current
test "$(docker exec "$OLD_APP" python -m alembic current | tr -d '\r')" = '0005_workshop_attribution (head)'
test "$(docker inspect -f '{{.State.Status}}' "$DB")" = running
test "$(docker inspect -f '{{.State.Status}}' "$MINIO")" = running
docker volume inspect mobile_money_corpus_manager_v0_1_pgdata mobile_money_corpus_manager_v0_1_miniodata mobile_money_corpus_manager_v0_1_tmpaudio
```

Ne jamais exécuter `python -m app.write_freeze` dans `$OLD_APP`. Après remplacement seulement, le contrôle équivalent est :

```bash
docker exec "${PROJECT}-app-1" python -m alembic current
docker exec "${PROJECT}-app-1" python -m app.write_freeze check --phase OPEN
```

## Préparer et vérifier l’état partagé

La création de ce chemin exige une autorisation distincte et n’a pas été faite dans ce ticket :

```bash
install -d -o 10001 -g 10001 -m 700 "$STATE_HOST"
test -d "$STATE_HOST" && test "$(stat -c '%U:%G:%a' "$STATE_HOST")" = 'appuser:appuser:700'
```

Avant exposition de la candidate, lancer un conteneur éphémère de la candidate avec le même montage, mais sans accès réseau de production :

```bash
docker run --rm --user 10001:10001 \
  -e WRITE_FREEZE_STATE_FILE="$STATE_CONTAINER" \
  -v "$STATE_HOST:/freeze-state" \
  "$CANDIDATE" python -m app.write_freeze check --phase OPEN
stat -c '%U:%G:%a %n' "$STATE_HOST" "$STATE_HOST/state.json" 2>/dev/null || true
```

L’absence initiale de `state.json` est acceptable et signifie `OPEN`; toute corruption, permission incorrecte ou état illisible doit faire échouer le contrôle. La candidate F5A4 ne transforme plus un JSON corrompu en `OPEN` : elle échoue fermée.

## Remplacement du seul service `app`

Ne pas utiliser le Dockerfile/Compose HEAD : il exige les migrations `0008`. Préparer hors dépôt un override Compose temporaire contenant uniquement :

```yaml
services:
  app:
    image: f5a4-candidate@sha256:b1fb0b134d00cdcd02acab3c020163fec94f2cfb8e0bf3042087a8f5610de778
    build: null
    user: "10001:10001"
    environment:
      WRITE_FREEZE_STATE_FILE: /freeze-state/state.json
    volumes:
      - tmpaudio:/tmp/audio
      - /var/lib/mobile-money-corpus/write-freeze:/freeze-state
```

Le digest dans l’override doit être vérifié contre `docker image inspect`; la valeur canonique est celle indiquée plus haut, sans raccourci. Valider avant action :

```bash
docker compose -p "$PROJECT" -f docker-compose.yml -f /path/to/f5a4-app.override.yml config --quiet
docker compose -p "$PROJECT" -f docker-compose.yml -f /path/to/f5a4-app.override.yml config | \
  sed -n '/^  app:/,/^  [a-z]/p'
```

Le diff de configuration doit montrer seulement l’image, le montage d’état et la variable d’état du service `app`. Refuser si `db`, `minio`, `traefik`, `pgdata`, `miniodata` ou `tmpaudio` sont modifiés.

## Fenêtre d’interruption contrôlée

L’ancienne image ne peut pas geler les écritures. L’interruption est donc obtenue par arrêt gracieux de l’unique conteneur `app`, sans modification de Traefik : les lectures et écritures sont indisponibles pendant la transition. Durée cible : 2–5 minutes, avec seuil d’arrêt à 60 secondes pour le drainage HTTP.

```bash
docker update --restart=no "$OLD_APP"
docker stop --time 60 "$OLD_APP"
test "$(docker inspect -f '{{.State.Status}}' "$OLD_APP")" = exited
docker ps --filter "name=${PROJECT}-app" --format '{{.Names}} {{.Status}}'
docker compose -p "$PROJECT" -f docker-compose.yml -f /path/to/f5a4-app.override.yml up -d --no-deps --force-recreate app
```

Cette séquence ne redémarre ni PostgreSQL, ni MinIO, ni Traefik et ne touche pas aux volumes de données. Avant de rendre la candidate accessible, contrôler :

```bash
docker exec "${PROJECT}-app-1" python -m alembic current
docker exec "${PROJECT}-app-1" python -m app.write_freeze check --phase OPEN
docker inspect "${PROJECT}-app-1" --format '{{json .Mounts}}'
docker inspect "${PROJECT}-app-1" --format '{{.Config.Image}} {{.Config.User}}'
curl --fail --silent --show-error https://APP_HOST/ready >/dev/null
```

Ne pas laisser une ancienne image configurée avec `restart: unless-stopped` reprendre automatiquement la place de la candidate. Le retour arrière est une commande manuelle distincte et est interdit pendant `DRAINING` ou `FROZEN`.

## Gel et capture

Après validation de la candidate et avant toute capture :

```bash
docker exec "${PROJECT}-app-1" python -m app.write_freeze freeze --timeout 60
docker exec "${PROJECT}-app-1" python -m app.write_freeze check --phase FROZEN
```

Maintenir `FROZEN` pendant PostgreSQL et MinIO. Utiliser ensuite `scripts/backup_local.sh` avec les cibles explicites `DB`, `MINIO`, le bucket `mobile-money-corpus`, le client MinIO épinglé par digest et `BACKUP_ROOT="$DEST"`. La destination doit être validée séparément ; ce ticket ne la crée pas.

## Reprise

Après `COMPLETE`, `COMPLETION.SHA256`, `SHA256SUMS`, `pg_restore --list`, comptages MinIO et rapport opérateur :

```bash
docker exec "${PROJECT}-app-1" python -m app.write_freeze check --phase FROZEN
docker exec "${PROJECT}-app-1" python -m app.write_freeze unfreeze
docker exec "${PROJECT}-app-1" python -m app.write_freeze check --phase OPEN
curl --fail --silent --show-error https://APP_HOST/ready >/dev/null
```
