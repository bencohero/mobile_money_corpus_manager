# G9-R3 — Validation Compose

Commande validée:

```sh
docker compose -f docker-compose.yml -f docker-compose.release.yml config --quiet
```

Rendu effectif: `app.image=mobile-money-corpus@sha256:9ce9a636481ad7726b62340df0f0d3debcf8ff75153a04245fc564df5a617077`, `build=null`, healthcheck avec `Host: corpus-moore.bencoherolab.com`, réseaux `backend` et `frontend`, labels Traefik conservés, aucun port publié pour PostgreSQL ou MinIO.

Le serveur Traefik n’a pas été modifié.
