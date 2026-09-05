# Lot P0-A
Le lot ajoute une configuration stricte en production, Alembic, des controles audio bornes, une compensation MinIO apres erreur et une reconciliation en lecture seule.
APP_ENV=development conserve create_all pour un environnement local. TEST et production exigent une migration explicite.
La migration 0001 utilise les metadonnees SQLAlchemy pour representer le schema actuel. Pour une base existante creee par create_all, faire une sauvegarde, verifier le schema, puis creer la table alembic_version par alembic stamp 0001_initial; ne jamais lancer upgrade contre la production sans copie isolee.
Variables: APP_ENV, COOKIE_SECURE, MIN_AUDIO_DURATION_SECONDS, MAX_AUDIO_DURATION_SECONDS, FFPROBE_TIMEOUT_SECONDS, MAX_CONCURRENT_CONVERSIONS et BACKUP_DIR.
La reconciliation est non destructive: python -m scripts.reconcile. Les corrections exigent une procedure revue.
Limites: concurrence locale a un processus; lecture audio encore en memoire; aucun VPS n'a ete contacte.

## P0-A.2
Le lot P0-A.2 est partiellement valide; voir docs/P0A2_INTEGRATION_RECOVERY.md et RAPPORT_VALIDATION_P0A2.md.
