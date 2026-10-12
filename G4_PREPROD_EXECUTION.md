# G4 — Exécution préproduction

## Périmètre

- Branche : `g3-candidate`
- Commit contrôlé : `9d8c0b1feaf86e22cf8c7e8ae8b1fafdf1e8ae41`
- Base : `main@32edc87`
- Commit applicatif G3 : `7d5c180`
- Archive : `/home/sangouman/mobile-money-corpus-backups/20261011T133947Z` (lecture seule)

## Isolement

Stack Compose projet `g4-preprod`, sans ports publiés : PostgreSQL 16, MinIO, application candidate, outils de restauration et service de test. Le réseau observé est `g4-preprod_default`; les volumes dédiés portent le préfixe `mobile-money-corpus-f-lot-`. Aucun de ces éléments ne correspond au réseau, aux volumes ou aux conteneurs de production, qui ont été vérifiés mais non modifiés.

La configuration Compose a été validée (`config --quiet`). Les identifiants de test sont fournis uniquement par la configuration Compose de test et ne sont pas reproduits ici.

## Sauvegarde et restauration

La vérification `sha256sum -c manifests/SHA256SUMS` a retourné `OK` pour tous les éléments de F5A7.2, notamment le dump PostgreSQL et les 30 objets MinIO. La restauration isolée a réussi. Comptage initial : schéma `0005_workshop_attribution`, 21 utilisateurs, 17 participants, 15 enregistrements, 1 transcription, 30 objets MinIO.

Un dump de point de restauration pré-migration a été créé dans le volume de preuves G4 : SHA-256 `1304e63f3f69bdf145e9e51be20784846776ca4c4c2aa1d1ca18d048923082a5`. Des dumps intermédiaires ont aussi été créés après 0006 et 0007.

## Migrations

Les migrations ont été exécutées sur le clone, par étapes, sans toucher à la production : 0006, 0007, puis 0008. L’état final Alembic est `0008_rate_limit_buckets (head)`. Les comptages post-migration avant les tests sont restés à 17 participants, 15 enregistrements et 1 transcription; 0007 a créé 1 entrée d’historique baseline et 0008 a créé 0 bucket initial.

## Exploitation contrôlée

L’application a répondu `{"status":"ready"}`. PostgreSQL, MinIO et l’application ont été redémarrés dans la stack G4; la readiness, le schéma `0008` et les données sont restés disponibles. La réconciliation exécutée après les tests a retourné `[]`.

Observation : la commande `app-test` du Compose de test exécute `alembic upgrade head` au démarrage. La migration contrôlée a néanmoins été effectuée avant ce démarrage; ce comportement doit être désactivé ou explicitement assumé avant production pour éviter une migration implicite.

## Conclusion d’exécution

Exécution isolée réussie. Aucun accès public, aucune ressource de production et aucune archive originale n’ont été modifiés.
