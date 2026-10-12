# F5A6 — audit de `main`

Date de contrôle : 2026-10-11, dépôt `/home/sangouman/apps/mobile_money_corpus_manager_v0_1`.

## Référence

- Branche : `main`.
- Commit : `e4d9c905f8b7077a65cc0ef9e4e68f2236c2680a` (`Remove backups dir to repos`).
- Les changements préexistants non liés (`.env.dev`, `backups/`, cache Graphify) ont été conservés.
- Le dépôt contenait `backup_mobile_money_corpus.sh`, qui arrêtait/redémarrait l’application, utilisait `mc mirror --overwrite`, publiait directement le répertoire final et ne gérait pas `offline_app`. Il ne satisfaisait donc pas F5A6.
- Les documents P0-A/P0-A2 décrivent des outils antérieurs, mais `scripts/backup.sh` et `scripts/reconcile.py` ne sont pas présents dans `main` au moment du contrôle.

## Cibles vérifiées en lecture seule

| Cible | Observation |
|---|---|
| `mobile_money_corpus_manager_v0_1-db-1` | présent, `postgres:16-alpine`, sain, PostgreSQL 16.15 |
| `mobile_money_corpus_manager_v0_1-minio-1` | présent, `minio/minio:RELEASE.2025-04-22T22-12-26Z`, endpoint health sain |
| `mobile_money_corpus_manager_v0_1-app-1` | présent mais arrêté (`Exited`), donc `APP_STOPPED`, pas `APP_ABSENT` dans l’état observé |
| volumes de production | `mobile_money_corpus_manager_v0_1_pgdata`, `mobile_money_corpus_manager_v0_1_miniodata` |
| destination proposée | `/var/backups/mobile-money-corpus/` absente |

Le PostgreSQL 18 `postgres`, ainsi que les PostgreSQL 17/16 d’autres projets, ont été vus sur le VPS et sont explicitement exclus. Les conteneurs F5A2/F5A3 et `mobile_money_corpus_manager_dev` sont des environnements distincts ; leur absence de partage de volumes doit rester une vérification opérateur au lancement.

Contrôles lecture seule effectués : Compose config, inventaire conteneurs/images/volumes/réseaux, santé PostgreSQL/MinIO, espace disque. Résultat : 93 GiB disponibles sur 193 GiB, `/var/backups/mobile-money-corpus/` absente. PostgreSQL rapporte la révision `0005_workshop_attribution` et zéro autre session dans `pg_stat_activity` au moment du contrôle. Comptages observés : users 21, participants 17, utterances 13, recordings 15, transcriptions 1, audit_logs 115.

## Limites et décision

Impossible d’exclure automatiquement les processus hôte, clients MinIO externes, tâches planifiées, identifiants partagés ou accès administrateur hors Docker. Une attestation opérateur est donc obligatoire et le script refuse toute exécution sans `OFFLINE_WRITERS_ATTESTED=YES`. Aucune sauvegarde réelle, migration, redémarrage, arrêt ou modification de données n’a été effectuée.

Décision : `READY_FOR_AUTHORIZATION`, sous réserve des conditions de `F5A6_EXECUTION_APPROVAL.md`.
