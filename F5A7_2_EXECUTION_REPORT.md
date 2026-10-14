# F5A7.2 — rapport d’exécution

## Décision

`BACKUP_COMPLETED_VERIFIED`

Date UTC du prévol : 2026-10-11. Première tentative : `13:36:25Z` (échec technique, conservée). Nouvelle tentative autorisée : `13:39:47Z`. Fin des contrôles : `13:40:51Z`.

## Attestation opérateur

L’opérateur a confirmé :

1. aucune autre application n’utilise les identifiants PostgreSQL/MinIO de production ;
2. aucun autre processus, script, tâche planifiée ou client externe n’effectue d’écriture pendant la sauvegarde ;
3. l’autorisation d’une sauvegarde locale réelle unique a été donnée dans F5A7.

Ces éléments sont enregistrés comme attestation déclarative opérateur. Ils ne sont pas présentés comme des vérifications techniques automatiques.

## Prévol technique réussi

- Branche : `main`.
- Commit : `e4d9c905f8b7077a65cc0ef9e4e68f2236c2680a`.
- PostgreSQL : `mobile_money_corpus_manager_v0_1-db-1`, `postgres:16-alpine`, PostgreSQL 16.15, sain.
- MinIO : `mobile_money_corpus_manager_v0_1-minio-1`, image attendue, endpoint sain.
- Application : `mobile_money_corpus_manager_v0_1-app-1`, arrêtée (`APP_STOPPED`).
- Révision Alembic : `0005_workshop_attribution`.
- Sessions PostgreSQL concurrentes observées : `0`.
- Volumes de production : consommés uniquement par les conteneurs attendus.
- Cohérence source préalable : 30 objets MinIO et 30 références audio PostgreSQL.
- Espace libre : 93 GiB.
- Tests synthétiques F5A6 : `10 passed`.
- Client MinIO : image digestée vérifiée `quay.io/minio/aistor/mc@sha256:23511e340cbabf07e6a8b53f9c434975708f22f3c047d6beeddc17bf1a5aed88`.

## Capture commencée

- Destination : `/home/sangouman/mobile-money-corpus-backups/`.
- Identifiant : `20261011T133625Z`.
- Archive conservée : `/home/sangouman/mobile-money-corpus-backups/20261011T133625Z.incomplete`.
- Dump PostgreSQL créé : `postgres/corpus.dump`, 60 629 octets.
- SHA-256 du dump : `c03d2e8a4072fe572b2400cb2fb990d59c8926b5f921defc234cf5d255982d21`.
- Copie MinIO : non commencée.

## Capture vérifiée

- Identifiant final : `20261011T133947Z`.
- Archive : `/home/sangouman/mobile-money-corpus-backups/20261011T133947Z`.
- Taille archive : environ 5.5 MiB.
- Dump PostgreSQL : 60 629 octets.
- MinIO : 30 objets, 5 289 708 octets.
- Références PostgreSQL : 30 ; manquants 0 ; orphelins 0.
- Aucun service de production arrêté, redémarré ou modifié.
- Aucun secret détecté dans les artefacts de l’archive.

## Blocage

La validation `pg_restore --list` a échoué car le script appelait `docker exec` sans attacher stdin (`-i`), ce qui transmettrait EOF à `pg_restore`. Le fichier dump réel reste présent et non vide; il n’a pas été déclaré valide par le contrôle requis.

Le script a été corrigé pour utiliser `docker exec -i`, puis une nouvelle tentative explicitement autorisée a réussi. La première archive `.incomplete` reste conservée. Aucun service ou objet source n’a été modifié.
