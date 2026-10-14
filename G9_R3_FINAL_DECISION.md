# G9-R3 — Décision finale

## `PUBLIC_OPEN_NO_GO`

Le déploiement de la release corrigée est réussi et l’application est saine, mais l’ouverture publique est refusée pour une raison de sécurité critique: le dashboard Traefik est accessible sur le port public `8090`, avec HTTP 200 sur l’interface et l’API.

Éléments validés: correction TrustedHost/healthcheck commitée; `162 passed`; image digestée; Compose `build=null`; sauvegarde/restauration G9-R2 valides; Alembic `0008`; route HTTPS applicative fonctionnelle; volumes PostgreSQL/MinIO préservés; rollback préparé.

Action bloquante opérateur: traiter l’exposition du dashboard Traefik dans l’infrastructure, puis refaire le smoke test externe. La copie externe reste `EXTERNAL_BACKUP_PENDING_MANUAL_OPERATOR_ACTION` et ne bloque pas les opérations locales.
