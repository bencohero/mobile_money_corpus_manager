# F5A3 — runbook de déploiement contrôlé

Ce document prépare une exécution ; il n’a pas été exécuté sur production.

## Précontrôles

```bash
set -Eeuo pipefail
IMAGE='f5a3-candidate@sha256:170270493de28c7e4fffbf1cd396122680d4eb2684249edd8fd7e166be4493e2'
PROJECT='mobile_money_corpus_manager_v0_1'
docker inspect --type=image "$IMAGE"
docker inspect "$PROJECT-app-1" "$PROJECT-db-1" "$PROJECT-minio-1"
docker exec "$PROJECT-db-1" python -m alembic current
docker exec "$PROJECT-app-1" python -m app.write_freeze check --phase OPEN
docker volume inspect mobile_money_corpus_manager_v0_1_pgdata mobile_money_corpus_manager_v0_1_miniodata mobile_money_corpus_manager_v0_1_tmpaudio
```

Le dernier contrôle `OPEN` est exécuté seulement avant le remplacement contrôlé et après vérification que l’état partagé existe. Le nom de l’image, le projet, PostgreSQL 16, le bucket `mobile-money-corpus` et l’UID runtime doivent correspondre exactement à la fiche d’autorisation.

## Déploiement de la candidate

1. Construire et scanner la candidate hors production ; vérifier le digest ci-dessus.
2. Préparer hors volume de données un chemin d’état dédié, par exemple `/var/lib/mobile-money-corpus/write-freeze/state.json`, propriétaire UID `10001`, répertoire `0700`, fichier `0600`. Ne pas créer le chemin dans le présent ticket.
3. Mettre à jour uniquement l’image du service applicatif et monter ce même chemin dans tous les processus sous `WRITE_FREEZE_STATE_FILE`.
4. Ne pas appliquer Alembic : la candidate doit rester sur `0005`.
5. Effectuer un remplacement contrôlé, avec un seul processus à la fois si nécessaire, puis contrôler `/health`, la révision et la persistance de l’état. Ne pas exposer la candidate via Traefik avant les contrôles.

## Fenêtre et gel

Impact attendu : les lectures restent disponibles ; les nouvelles écritures sont refusées pendant le gel. La fenêtre cible est 5–10 minutes, à prolonger uniquement si `active_writes` ne descend pas à zéro.

```bash
docker exec "$PROJECT-app-1" python -m app.write_freeze freeze --timeout 60
docker exec "$PROJECT-app-1" python -m app.write_freeze check --phase FROZEN
docker exec "$PROJECT-app-1" python -m app.write_freeze status
```

Maintenir `FROZEN` pendant les deux captures. Utiliser ensuite le script audité, avec `PG_CONTAINER="$PROJECT-db-1"`, `MINIO_CONTAINER="$PROJECT-minio-1"`, `MINIO_BUCKET=mobile-money-corpus`, `BACKUP_MODE=production`, `BACKUP_TARGET_ID=mobile_money_corpus_manager_v0_1`, `MINIO_MC_IMAGE=quay.io/minio/aistor/mc@sha256:23511e340cbabf07e6a8b53f9c434975708f22f3c047d6beeddc17bf1a5aed88`, et `WRITE_FREEZE_ATTESTED=YES`. La destination doit être décidée et validée séparément ; elle ne doit pas être le dépôt Git ni un volume Docker de données.

## Reprise contrôlée

Ne reprendre qu’après présence de `COMPLETE`, validation de `COMPLETION.SHA256`, vérification de `SHA256SUMS`, dump lisible par `pg_restore --list`, égalité des comptages MinIO et rapport signé par l’opérateur.

```bash
docker exec "$PROJECT-app-1" python -m app.write_freeze check --phase FROZEN
docker exec "$PROJECT-app-1" python -m app.write_freeze unfreeze
docker exec "$PROJECT-app-1" python -m app.write_freeze check --phase OPEN
```

En cas d’échec : ne jamais créer `COMPLETE`, conserver le dossier `.incomplete`, conserver uniquement les journaux sans secrets/données personnelles, corriger ou abandonner la capture, puis reprendre via `unfreeze` seulement si l’application est saine. Si l’état reste `DRAINING` après le délai, déclarer l’incident, ne pas forcer `FROZEN`, et rétablir le service selon la procédure d’astreinte.

## Retour arrière

Si la candidate échoue hors gel, retirer la candidate du service applicatif via le mécanisme de déploiement validé et conserver l’état partagé. Si elle échoue pendant `FROZEN`, maintenir le gel jusqu’à contrôle des deux services ; ne jamais redémarrer avec un état non monté, car cela pourrait rouvrir les écritures silencieusement. Aucune restauration de données n’est incluse.

