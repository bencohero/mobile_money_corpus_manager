# F5A6 — prévol `offline_app`

Le mode cible est `BACKUP_MODE=offline_app`. Il accepte exactement deux états applicatifs :

- `APP_STOPPED` : le conteneur existe et `State.Running=false` ;
- `APP_ABSENT` : `docker inspect` échoue pour le conteneur attendu.

Dans les deux cas, PostgreSQL et MinIO doivent être les conteneurs nommés attendus, avec les images attendues, en fonctionnement et sains. Le script contrôle également :

- `CONFIRM_TARGET=YES` ;
- `OFFLINE_WRITERS_ATTESTED=YES` ;
- `BACKUP_APPROVED=YES` ;
- client MinIO présent et vérifié par SHA-256 fourni par l’opérateur ;
- verrou `flock` ;
- destination finale et `.incomplete` inexistantes ;
- zéro session PostgreSQL concurrente ;
- révision Alembic `0005_workshop_attribution` ;
- absence d’arrêt, démarrage ou redéploiement automatique.

La vérification automatique ne prouve pas l’absence de processus hôte, d’écriture MinIO externe, de tâche cron/systemd ou d’application partageant des secrets. L’opérateur doit documenter ces chemins avant de fournir l’attestation. Une attestation manquante ou une cible inattendue bloque immédiatement.

Le prévol réel du 2026-10-11 trouve `APP_STOPPED`, PostgreSQL 16.15 sain, MinIO sain, zéro session concurrente observée et la révision attendue. L’application n’est pas absente dans cet état ; le cas absent est néanmoins couvert par le test synthétique.
