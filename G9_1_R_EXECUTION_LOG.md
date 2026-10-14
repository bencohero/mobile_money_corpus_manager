# G9.1-R — Journal d’exécution

## Décision de session

Statut : BLOCKED avant exécution.

Aucune autorisation opérateur explicite couvrant capture production, gel,
transfert Kubuntu et restauration isolée n’a été fournie. Seules des inspections
locales en lecture seule ont été réalisées.

## Précontrôles lecture seule

| Contrôle | Résultat |
|---|---|
| App conteneur | mobile_money_corpus_manager_g8_5_r-app |
| Image app | release 8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6 |
| PostgreSQL | mobile_money_corpus_manager_v0_1-db-1, postgres:16-alpine |
| MinIO | mobile_money_corpus_manager_v0_1-minio-1, RELEASE.2025-04-22T22-12-26Z |
| Réseau backend | mobile_money_corpus_manager_v0_1_backend |
| Volumes | pgdata, miniodata, tmpaudio de production identifiés |
| Gate | app.write_freeze importable dans l’image release |
| Outillage | image G8.8-B disponible, digest sha256:6f33d7802d969e86ba855696862e981d78305523e402a814b1c04ffbac64654f |
| Capture | non exécutée |
| Gel | non exécuté |
| Transfert | non exécuté |
| Restauration | non exécutée |
| Ouverture publique | non exécutée |

## Résultats live de la phase A

- Hôte local : `vmi3474447`; utilisateur : `sangouman`.
- Alembic PostgreSQL : `0008_rate_limit_buckets`.
- État de gel observé : `OPEN`, `active_writes=0`, `epoch=0`.
- Sessions PostgreSQL autres que la session de contrôle : `1` ; cela ne
  constitue pas une preuve d’absence d’activité métier et impose de poursuivre
  le contrôle avant gel.
- Compteurs lus : users `24`, participants `18`, utterances `13`, recordings
  `18`, transcriptions `2`, audit_logs `154`.
- Processus connus `pg_dump`, `pg_restore`, `mc mirror`, `rclone`, `restic` ou
  `borg` : aucun, hors commande de recherche elle-même.
- `/var/backups/mobile-money-corpus` : absent.
- `/var/lib/mobile-money-corpus/write-freeze` côté hôte : absent.
- `restic` : absent sur l’hôte courant.
- Aucun hôte Kubuntu réel n’est configuré dans SSH; `kubuntu`, `kubuntu-host`
  et `vps-prod` ne sont que des noms SSH non résolus par la configuration.

Le contrôle runtime app.write_freeze status reste une étape post-autorisation :
il n’a pas été lancé pour éviter toute initialisation ou modification d’état
partagé avant autorisation.

Le run est arrêté avant toute écriture, gel, transfert et création d’archive.
