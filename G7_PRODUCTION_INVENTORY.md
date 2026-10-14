# G7 — Inventaire production en lecture seule

## Git

- `main` : `889fd5b018f038d6166d8ef0afa976426392fa79`.
- Parents : `32edc8716869f67aee0c09123a93b0e454012f33` et `31070e26cfc58721c1d9ed2809c5d82194677da2`.
- `g5-hardening` : `31070e26cfc58721c1d9ed2809c5d82194677da2`.
- Worktrees existants conservés ; le worktree courant contient des changements antérieurs non liés et n’a pas été écrasé.

## Services observés

Lecture Docker effectuée sans `up`, `down`, `restart` ni modification de volume.

- PostgreSQL : conteneur `mobile_money_corpus_manager_v0_1-db-1`, `postgres:16-alpine`, PostgreSQL `16.15`, état `running/healthy`.
- MinIO : conteneur `mobile_money_corpus_manager_v0_1-minio-1`, image `minio/minio:RELEASE.2025-04-22T22-12-26Z`, état `running/healthy`.
- Application production : conteneur `mobile_money_corpus_manager_v0_1-app-1` absent ; la production n’est donc pas entièrement arrêtée, mais l’application n’est pas active.
- Volumes attendus : `..._pgdata`, `..._miniodata`, `..._tmpaudio`.
- Réseau backend interne observé ; réseau frontend géré séparément.
- Réseaux et volumes ont été inventoriés sans modification.

## Versions et schéma

- Révision Alembic PostgreSQL lue sans écriture : `0005_workshop_attribution`.
- Images de production déclarées : PostgreSQL 16 Alpine et MinIO daté ; l’image applicative est construite localement depuis le `Dockerfile`, avec Python 3.12 et dépendances verrouillées dans `requirements.txt`.
- Variables `.env` inspectées par noms uniquement ; aucune valeur secrète n’est reproduite.

## Capacité

Le système de fichiers dispose d’environ 87 GiB libres et 93 % d’inodes libres. La sauvegarde F5A7.2 occupe environ 5,5 MiB ; cette marge est suffisante pour le clone local, mais la capacité VPS doit être revalidée juste avant production.

## Réserve opérationnelle

La copie indépendante du VPS n’est pas démontrée dans cet environnement local. Elle doit être attestée par l’opérateur avant tout GO production.
