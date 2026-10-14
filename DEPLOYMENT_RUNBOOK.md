# Deployment runbook

## Préproduction Lot F

Valider la configuration sans production avec :

```bash
docker compose -f docker-compose.test.yml -f docker-compose.preprod.yml config --quiet
docker compose -f docker-compose.test.yml -f docker-compose.preprod.yml up -d db-test minio-test db-restore minio-restore app-test tools
docker compose -f docker-compose.test.yml -f docker-compose.preprod.yml run --rm test
docker compose -f docker-compose.test.yml -f docker-compose.preprod.yml down -v --remove-orphans
```

Le fichier `docker-compose.preprod.yml` impose le réseau et les volumes `mobile-money-corpus-f-lot-*`.
Ne pas utiliser cette recette avec les volumes de production.

## Pré-déploiement

- [ ] Sauvegardes PostgreSQL et MinIO vérifiées, hors hôte applicatif.
- [ ] Restauration isolée réussie et hashes audio comparés.
- [ ] `.env` contient des secrets non par défaut, `COOKIE_SECURE=true`, HTTPS et hôte de confiance.
- [ ] La cible Alembic est explicitement `0008_rate_limit_buckets`.
- [ ] Tests Python, Node, scans et smoke tests validés.

## Déploiement

1. Mettre l’application en maintenance et arrêter les écritures.
2. Capturer les versions Git, Docker et Alembic.
3. Appliquer la procédure de [MIGRATION_0005_TO_0008.md](MIGRATION_0005_TO_0008.md) uniquement après approbation.
4. Déployer l’image validée, attendre `/ready`, puis tester `/health`.
5. Tester connexion, capture, lecture Range, transcription, export et logout.

Responsables : données pour backup/écarts, exploitation pour fenêtre/retour arrière,
sécurité pour scanners/HTTPS, produit pour desktop/Android et parcours fonctionnels.
Critère d’arrêt : toute divergence de comptage, checksum, migration, readiness, sécurité
ou permission provoque l’arrêt des écritures et le retour à la sauvegarde coordonnée.

## Retour arrière

Restaurer l’image précédente et, si le schéma a changé, restaurer PostgreSQL et MinIO
depuis le même point de sauvegarde. Ne pas mélanger une base restaurée avec un bucket
postérieur sans analyse de réconciliation.
