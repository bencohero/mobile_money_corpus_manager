# G9-R3 — Déploiement

Déploiement effectué avec le Compose du dépôt et l’overlay release, sans build pendant le déploiement:

```sh
docker compose -p mobile_money_corpus_manager_v0_1 \
  -f docker-compose.yml -f docker-compose.release.yml \
  up -d --no-build --no-deps app
```

Résultat: `mobile_money_corpus_manager_v0_1-app-1` est `healthy`, image digest `sha256:9ce9a636…617077`, revision `2698530f…c36ae`, `/ready` 200, Alembic `0008_rate_limit_buckets (head)`, réseaux `frontend` et backend présents, labels Traefik corrects. PostgreSQL et MinIO sont restés actifs sur leurs volumes existants; l’ancien conteneur G8.5-R est arrêté et conservé pour rollback.

Rollback: arrêter le nouveau service puis redémarrer l’ancien conteneur G8.5-R; ne restaurer aucune donnée et ne pas recréer PostgreSQL/MinIO.
