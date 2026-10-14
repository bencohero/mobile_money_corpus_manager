# G8.5 — Vérifications pré-migration

Date du contrôle : 2026-10-13 (Europe/Berlin). Mode : lecture seule.

## Références opérateur

- Release autorisée : `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`
- Archive locale : `20261012T235937Z`
- Snapshot restic annoncé : `a4b07220`
- Révision initiale : `0005_workshop_attribution`
- Révision cible : `0008_rate_limit_buckets`
- SHA manifeste attendu : `041a3f62994f3839f1b35a4d758ac1f0ca645ac1e3bacd6a856340c172ff20a8`

## Matrice de contrôle

| Contrôle | Résultat | Preuve / décision |
|---|---|---|
| Release disponible | PASS | Le commit autorisé existe localement et contient `scripts/migrate.sh`. |
| Release réellement utilisée | **FAIL** | Le checkout courant est `b672697a34196841cd5fd9714520166b6edb345b`, pas la release autorisée. L’image applicative inspectée n’est pas attribuée à ce commit. |
| Gel des écritures | PASS partiel | Aucun conteneur `app` dans `docker compose ps`; aucun processus de sauvegarde/migration observé. La vérification externe des clients n’est pas démontrée par ce seul hôte. |
| Données inchangées depuis sauvegarde | PASS pour PostgreSQL | Révision et comptages courants identiques au manifeste : users 21, participants 17, utterances 13, recordings 15, transcriptions 1, audit_logs 116. |
| Révision Alembic | PASS | `alembic_version = 0005_workshop_attribution`. |
| Archive locale | PASS | `sha256sum -c manifests/SHA256SUMS` OK; SHA du manifeste conforme; `COMPLETE` présent. |
| Rollback coordonné PostgreSQL/MinIO | **FAIL / NON ATTESTÉ** | `G8_1_OFFSITE_ATTESTATION.md` est encore `PENDING`; aucune preuve locale de `restic check`, restauration isolée et clé hors VPS pour `a4b07220`. |
| Volumes recréés | PASS | Les volumes existants `mobile_money_corpus_manager_v0_1_pgdata` et `..._miniodata` sont montés par les conteneurs actuels. Aucune commande de recréation n’a été exécutée. |
| Accès public / écritures | MAINTENU FERMÉ | Aucun démarrage applicatif ni ouverture publique effectués. |

## STOP

Le contrôle s’arrête avant migration. Une condition obligatoire échoue : l’instance contrôlée n’utilise pas la release autorisée et la récupérabilité externe coordonnée PostgreSQL/MinIO n’est pas attestée. Ne pas exécuter `scripts/migrate.sh`, ne pas démarrer l’application et ne pas modifier les volumes avant renouvellement de ces attestations.

Les modifications et fichiers non suivis déjà présents dans le checkout ont été conservés; aucun nettoyage Git, push distant ou changement de données n’a été effectué.
