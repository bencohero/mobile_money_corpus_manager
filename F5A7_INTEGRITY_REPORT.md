# F5A7 — rapport d’intégrité

## Capture

Aucune archive réelle n’existe. Il n’y a donc pas d’identifiant de sauvegarde, de dump, d’inventaire MinIO ou de manifeste à valider.

## Contrôles réalisés avant capture

- Commit Git conforme : réussi.
- Identité Compose, images, labels, réseaux et volumes des trois cibles : conformes.
- PostgreSQL 16.15 sain : réussi.
- MinIO sain : réussi.
- Révision Alembic : `0005_workshop_attribution`, conforme.
- Sessions PostgreSQL concurrentes : `0` observée.
- Destination de sauvegarde : absente.
- Espace disponible : 93 GiB.
- Client MinIO approuvé : digest d’image vérifié, mais non utilisé pour capturer.

## Contrôles non exécutés

`pg_dump`, `pg_restore --list`, SHA-256 d’archive, inventaire complet du bucket, comparaison tailles/empreintes, cohérence références audio et publication `COMPLETE` n’ont pas été exécutés sur les données réelles.

## Limites

La preuve d’absence d’écriture externe requiert une attestation opérateur couvrant MinIO, PostgreSQL, l’hôte, Docker, cron/systemd, secrets partagés et clients hors conteneurs. Elle reste manquante ; aucune conclusion de sauvegarde intégrale ou de restaurabilité ne peut être tirée.
