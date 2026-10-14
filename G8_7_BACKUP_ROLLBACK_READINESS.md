# G8.7 — Préparation sauvegarde et rollback

## Passant

- snapshot restic `a4b07220`, dépôt `3ca53008` ; `restic check --read-data`
  attesté PASS ;
- restauration de 102 fichiers et sommes SHA-256 attestées PASS ;
- procédure de restauration isolée documentée dans `docs/BACKUP_RESTORE.md` ;
- `0008_rate_limit_buckets` confirmé sur la cible actuelle.

## Réserve bloquante pour GO public

La preuve disponible qualifie la restauration de fichiers, pas une restauration
complète et opérationnelle PostgreSQL + MinIO dans une cible isolée. Aucun
nouveau backup de production ni test de restauration coordonnée n’a été lancé
dans G8.7, conformément aux restrictions.

Avant ouverture, il faut une autorisation distincte pour :

1. exécuter le backup production avec gel contrôlé et destination hors dépôt ;
2. vérifier manifestes, dumps, objets et sommes ;
3. restaurer PostgreSQL et MinIO ensemble en environnement isolé ;
4. confirmer Alembic, cohérence des objets et procédure de rollback ;
5. conserver l’attestation hors VPS.
