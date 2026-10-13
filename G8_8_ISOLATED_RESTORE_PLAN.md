# G8.8 — Plan de restauration isolée

## Isolation requise

- cible PostgreSQL dédiée, volume dédié et réseau Docker dédié ;
- cible MinIO dédiée, bucket dédié et volume dédié ;
- aucun hostname, volume, réseau ou secret de production réutilisé ;
- aucune connexion sortante vers les services de production ;
- application de restauration arrêtée après les contrôles, si nécessaire.

## Séquence proposée, non exécutée

1. Vérifier les sommes et le manifest du backup.
2. Restaurer le dump PostgreSQL dans la cible isolée avec `pg_restore`.
3. Miroiter les objets MinIO vers le bucket isolé avec `mc`.
4. Vérifier le nombre d’objets, les tailles et SHA-256.
5. Démarrer uniquement l’application isolée, confirmer `alembic current`,
   `/ready` et `/health`.
6. Exécuter `scripts/reconcile.py --json` et exiger `[]`.
7. Comparer les inventaires DB/MinIO à la source.
8. Documenter durée, RPO/RTO, logs et résultat de rollback sans toucher à la
   production.

## Critères d’arrêt

Arrêt immédiat en cas de cible ambiguë, volume partagé, réseau de production,
écart de somme, objet manquant/orphelin, migration implicite, secret exposé,
ou connexion applicative vers production.
