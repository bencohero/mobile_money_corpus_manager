# G9-R2 — Déploiement contrôlé

## État

Déploiement non exécuté. La condition préalable de sécurité n’est pas satisfaite.

Le rollback préparé est l’image actuellement active identifiée par le conteneur applicatif: `mobile_money_corpus_manager_g8_5_r:8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`. Aucun volume PostgreSQL/MinIO de production n’a été recréé, restauré ou modifié par une opération de déploiement.

Commande préparée, à exécuter seulement après correction/revalidation:

```sh
docker compose -f docker-compose.yml -f docker-compose.release.yml up -d --no-build app
```

La commande utilise explicitement l’image digestée, conserve les volumes et réutilise les labels Traefik du dépôt. Elle ne modifie pas Traefik. Avant exécution, corriger le healthcheck/TrustedHost de façon versionnée puis reconstruire et retagger une nouvelle release; ne pas patcher le conteneur actif.

`EXTERNAL_BACKUP_PENDING_MANUAL_OPERATOR_ACTION` reste un risque résiduel, pas un échec technique Codex.
