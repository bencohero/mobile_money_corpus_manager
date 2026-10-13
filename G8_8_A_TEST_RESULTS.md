# G8.8-A — Résultats de tests

## Tests de contrat

`tests/test_restore_contract.sh` : PASS, 8 cas.

- schema 1 valide ;
- schema 2 valide ;
- manifest absent refusé ;
- somme invalide refusée ;
- archive incomplète refusée ;
- fichier inattendu refusé ;
- cible PostgreSQL de production refusée ;
- cible de restauration production refusée.

## Tests isolés réels

- `scripts/backup.sh` synthétique : PASS ;
- `scripts/backup_local.sh` synthétique : PASS, artefact schema 2 ;
- restauration PostgreSQL + MinIO schema 1 : PASS ;
- restauration PostgreSQL + MinIO schema 2 : PASS ;
- restauration de l’archive historique schema 2 : PASS ;
- PostgreSQL fixture actuelle : `0008_rate_limit_buckets`, compte
  `synthetic-account` retrouvé ;
- PostgreSQL historique : `0005_workshop_attribution` retrouvé ;
- MinIO : objets audio synthétiques retrouvés et comptés.

Les cibles utilisées étaient `g88-a-source-*` et `g88-a-restore-*`, sur le
réseau Docker dédié `g88-a-isolated`, sans volume de production.
