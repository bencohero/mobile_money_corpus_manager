# F.5A.2 — Validation de la sauvegarde locale

Date : 2026-10-11. Aucun conteneur de production, volume de production, Traefik, migration ou donnée réelle n’a été modifié.

## Décision

**BLOQUÉ pour autorisation réelle.**

La procédure corrigée est exécutable et validée avec des données synthétiques, mais l’image actuellement déployée ne contient pas le garde d’écriture préparé dans le dépôt. Les fichiers applicatifs dans l’image de production ont des SHA-256 différents du dépôt local et `app/write_freeze.py` est absent de l’image. Une sauvegarde réelle ne peut donc pas être déclarée cohérente avant déploiement contrôlé de ce mécanisme, ou d’un mécanisme équivalent présent dans l’image réellement exécutée.

## Corrections livrées

- Nouveau script : [scripts/backup_local.sh](scripts/backup_local.sh).
- Les manifestes utilisent des chemins relatifs à la racine de l’archive ; ils restent valides après le renommage atomique.
- `SHA256SUMS` exclut sa propre sortie et `COMPLETION.SHA256` référence `COMPLETE` avec un chemin relatif.
- Une archive n’est publiée qu’après dump lisible, comptage MinIO égal, contrôles SHA-256 et marqueur `COMPLETE`.
- Toute erreur laisse un répertoire caché `*.incomplete/INCOMPLETE` et aucun dossier final valide.
- Cibles contrôlées par nom, mode, image/digest optionnels, labels Compose optionnels et bucket explicite.
- Client MinIO épinglé utilisé pour les tests : `quay.io/minio/aistor/mc@sha256:23511e340cbabf07e6a8b53f9c434975708f22f3c047d6beeddc17bf1a5aed88`.
- Les identifiants MinIO sont lus depuis l’environnement du conteneur ciblé et transmis à un conteneur client éphémère ; ils ne sont ni écrits dans les manifestes ni affichés dans les logs.
- `pg_dump --format=custom` et `pg_restore --list` sont compatibles avec PostgreSQL 16. MinIO est joint sur le réseau du conteneur au endpoint `127.0.0.1:9000`.

## Validation synthétique exécutée

Conteneurs neufs, réseau dédié `f5a2-isolated`, PostgreSQL `16-alpine` et MinIO `RELEASE.2025-04-22T22-12-26Z`, avec `tmpfs` uniquement. Deux lignes synthétiques et deux objets synthétiques ont été injectés.

Résultats :

- dump PostgreSQL produit et catalogue `pg_restore --list` lisible ;
- 2 objets source = 2 objets copiés ;
- `SHA256SUMS` et `COMPLETION.SHA256` vérifiés après publication ;
- publication atomique réussie ;
- restauration dans PostgreSQL/MinIO distincts réussie ; 2 lignes et 2 objets retrouvés ;
- échec PostgreSQL : pas de dossier final, marqueur `INCOMPLETE` ;
- échec MinIO : pas de dossier final, marqueur `INCOMPLETE` ;
- dump tronqué : vérification SHA-256 refusée.

## État de la production observée

La stack `mobile_money_corpus_manager_v0_1` est restée `running`, avec PostgreSQL et MinIO `healthy`. L’image applicative actuelle annonce Alembic `0005_workshop_attribution`, contient seulement les migrations jusqu’à `0005`, et ne contient pas le garde `write_freeze`. Cette dérive entre image déployée et dépôt doit être résolue par un déploiement séparé et approuvé.
