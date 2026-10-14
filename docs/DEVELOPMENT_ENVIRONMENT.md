# Environnement Docker de développement

Cet environnement est autonome et réservé au développement de Mobile Money Corpus Manager. Il n'utilise ni le réseau Traefik, ni les volumes, secrets, base PostgreSQL ou stockage MinIO de production. L'application et MinIO sont publiés uniquement sur la boucle locale du VPS afin d'être utilisés via un tunnel SSH. Le réseau bridge dédié n'est pas marqué `internal`, car cette option empêche la publication de ports avec le moteur Docker utilisé sur le VPS ; aucune interface publique ni réseau Traefik ne lui est toutefois attaché.

## Prérequis et configuration

- Docker Engine et Docker Compose v2 (`docker compose version`).
- Le dépôt cloné sur le VPS.
- Aucun fichier `.env.dev` contenant des secrets ne doit être ajouté à Git.

Créer le fichier local puis générer des valeurs distinctes de la production :

```bash
cp .env.dev.example .env.dev
umask 077
openssl rand -base64 32
```

Remplacer chaque valeur `CHANGE_ME` par une valeur aléatoire longue. `JWT_SECRET` et `WORKSHOP_CODE_SECRET` doivent être différents. Le fichier `.env.dev` reste local au VPS.

## Validation et démarrage

Toutes les commandes ci-dessous ciblent explicitement le Compose dev :

```bash
docker compose --env-file .env.dev -f docker-compose.dev.yml config --quiet
docker compose --env-file .env.dev -f docker-compose.dev.yml up -d --build
docker compose --env-file .env.dev -f docker-compose.dev.yml ps
```

L'image runtime contient `/app/alembic.ini`, `/app/migrations/env.py`, le paquet `app`, FFmpeg et le client PostgreSQL. Les migrations ne sont pas remplacées par `create_all()` : elles doivent être appliquées explicitement sur la base dev.

## Migrations et diagnostics

```bash
docker compose --env-file .env.dev -f docker-compose.dev.yml run --rm \
  --entrypoint python app -m alembic -c /app/alembic.ini upgrade head

docker compose --env-file .env.dev -f docker-compose.dev.yml run --rm \
  --entrypoint python app -m alembic -c /app/alembic.ini current

docker compose --env-file .env.dev -f docker-compose.dev.yml logs --tail=200 app
```

Après `upgrade head`, le healthcheck de l'application doit passer. L'application vérifie la révision Alembic au démarrage et initialise automatiquement le bucket `mobile-money-corpus-dev` dans le MinIO dev.

## Accès par tunnel SSH

Les seuls ports hôte publiés sont `127.0.0.1:8081`, `127.0.0.1:9100` et `127.0.0.1:9101` :

```bash
ssh \
  -L 8081:127.0.0.1:8081 \
  -L 9101:127.0.0.1:9101 \
  utilisateur@adresse-du-vps
```

Puis ouvrir l'application sur `http://127.0.0.1:8081` et la console MinIO sur `http://127.0.0.1:9101`. L'API S3 MinIO est disponible sur `http://127.0.0.1:9100` si nécessaire.

## Tests et contrôles d'isolation

Les contrôles statiques sont exécutables sans arrêter ni supprimer de service :

```bash
pytest -q tests/test_dev_environment.py
docker compose --env-file .env.dev -f docker-compose.dev.yml config | \
  grep -Ei 'traefik|loadbalancer|routers|Host\\(' || true
docker compose --env-file .env.dev -f docker-compose.dev.yml ps
```

La première commande doit réussir. La seconde ne doit produire aucun résultat. Pour un stack démarré, inspecter le réseau sans afficher les variables :

```bash
docker inspect mobile_money_corpus_dev-app-1 \
  --format '{{json .NetworkSettings.Networks}}'
```

Le seul réseau attendu est `mobile_money_corpus_dev_internal`; il ne doit pas y avoir de réseau Traefik ou `frontend`. Les ports affichés par `ps` doivent commencer par `127.0.0.1:`.

## Arrêt, sauvegarde et réinitialisation

Arrêter les services sans supprimer les volumes :

```bash
docker compose --env-file .env.dev -f docker-compose.dev.yml down
```

Une sauvegarde dev peut être faite avec les scripts existants en fournissant explicitement les paramètres dev et une destination dédiée. Ne jamais pointer `TARGET_DATABASE_URL`, `MINIO_BUCKET` ou un chemin de sauvegarde vers la production.

La réinitialisation des données dev est destructive et doit être exceptionnelle. Vérifier d'abord le projet et les noms exacts, puis demander confirmation avant de supprimer uniquement les volumes `mobile_money_corpus_dev_postgres_data` et `mobile_money_corpus_dev_minio_data`. Ne jamais utiliser cette procédure sur `docker-compose.yml` de production et ne jamais lancer `docker compose down -v` sur la production.

## Différences avec la production

La production utilise `docker-compose.yml`, `APP_ENV=production`, les volumes `pgdata`/`miniodata`, le réseau interne `backend` et le réseau externe `frontend` avec des labels Traefik. Le dev utilise `docker-compose.dev.yml`, `APP_ENV=development`, les volumes nommés `mobile_money_corpus_dev_*`, un unique réseau bridge dédié `mobile_money_corpus_dev_internal`, aucun label Traefik et uniquement des ports liés à `127.0.0.1`.
