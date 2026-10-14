# F5A7 — rapport d’exécution

## Statut

`BLOCKED_BEFORE_EXECUTION`

Le prévol a été exécuté le 2026-10-11. Début : contrôle en lecture seule avant 13:10:46 UTC. Fin du prévol : 13:10:46 UTC. Aucune capture réelle n’a été lancée.

## Référence et cibles

- Branche : `main`.
- Commit vérifié : `e4d9c905f8b7077a65cc0ef9e4e68f2236c2680a`.
- PostgreSQL : `mobile_money_corpus_manager_v0_1-db-1`, image `postgres:16-alpine`, PostgreSQL 16.15, base `corpus`.
- MinIO : `mobile_money_corpus_manager_v0_1-minio-1`, image `minio/minio:RELEASE.2025-04-22T22-12-26Z`, bucket cible non modifié.
- Application : `mobile_money_corpus_manager_v0_1-app-1`, présente mais arrêtée (`APP_STOPPED`).
- Révision : `0005_workshop_attribution`.

## Résultats du prévol

- PostgreSQL et MinIO actifs et sains.
- Zéro session PostgreSQL concurrente observée sur `corpus`.
- Volumes de production consommés uniquement par les conteneurs attendus.
- Aucune autre instance applicative ne partage ces volumes Docker.
- Aucun processus de collecte/transcription/import/réconciliation de production identifié.
- Aucune tâche planifiée pertinente identifiée ; les timers observés sont système et non liés au corpus.
- Espace libre : 93 GiB sur 193 GiB.
- `/var/backups/mobile-money-corpus/` absente ; aucun fichier de sauvegarde créé.
- Client MinIO épinglé disponible sous forme d’image digestée : `quay.io/minio/aistor/mc@sha256:23511e340cbabf07e6a8b53f9c434975708f22f3c047d6beeddc17bf1a5aed88`.

## Blocage

Les clients MinIO externes, processus hôte disposant de secrets, tâches externes et chemins d’écriture hors Docker ne peuvent pas être exclus automatiquement. L’attestation `OFFLINE_WRITERS_ATTESTED=YES` n’a pas été fournie par l’opérateur et n’a pas été générée automatiquement.

Par conséquent, aucune destination n’a été créée, aucun secret n’a été utilisé pour une capture, et aucun service de production n’a été modifié. Une nouvelle tentative nécessite l’attestation complémentaire et une nouvelle autorisation explicite.
