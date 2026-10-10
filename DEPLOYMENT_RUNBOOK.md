# Deployment runbook

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

## Retour arrière

Restaurer l’image précédente et, si le schéma a changé, restaurer PostgreSQL et MinIO
depuis le même point de sauvegarde. Ne pas mélanger une base restaurée avec un bucket
postérieur sans analyse de réconciliation.
