# G9-R2 — Validation Compose

Le Compose du dépôt a été validé avec variables de production injectées sans afficher les secrets. Un overlay ajouté pour la release fixe l’image par digest et neutralise `build`:

`docker compose -f docker-compose.yml -f docker-compose.release.yml config --quiet` → PASS.

Preuve rendue: `app.image=mobile-money-corpus@sha256:3f13523f19c919b979cbaed70919205811d19d535e9e36077150ce43a96a9417`, `build=null`.

Les labels Traefik sont conservés: `enable=true`, réseau `frontend`, Host `corpus-moore.bencoherolab.com`, entrypoint `websecure`, TLS, resolver `ovhcloud`, service `mobile-money-corpus`, port interne `8000`. Réseaux `backend` et `frontend`, healthcheck, dépendances et volumes sont ceux du Compose du dépôt. PostgreSQL et MinIO n’ont aucun port publié.

Blocage trouvé dans la configuration applicative: le healthcheck appelle `localhost`, mais la production réduit les hôtes de confiance à `APP_HOST` par défaut; `/ready` répond donc 400. Le fichier de configuration serveur Traefik n’a pas été modifié.
