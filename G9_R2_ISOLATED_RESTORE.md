# G9-R2 — Restauration isolée

Restauration effectuée dans le réseau dédié `g88-a-isolated`, avec `g88-a-restore-db` et `g88-a-restore-minio`; l’archive était montée en lecture seule. Aucun volume de production n’a été utilisé.

Après remise à zéro du seul schéma `public` et du seul bucket de restauration isolé, la restauration schema 2 a réussi:

- 36 objets MinIO restaurés, cardinalité vérifiée;
- 18 enregistrements PostgreSQL;
- Alembic: `0008_rate_limit_buckets`;
- empreintes et manifestes de l’archive vérifiés;
- réconciliation de présence PostgreSQL/MinIO compatible avec les inventaires.

La première tentative a été arrêtée par une dépendance PostgreSQL du `--clean`; elle a concerné exclusivement la cible isolée. La seconde tentative propre est celle retenue.
