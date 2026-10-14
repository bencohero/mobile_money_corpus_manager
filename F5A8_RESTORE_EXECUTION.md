# F5A8 — exécution de restauration isolée

## Décision

`RESTORE_VERIFIED`

Archive testée : `/home/sangouman/mobile-money-corpus-backups/20261011T133947Z`.

L’archive a été vérifiée avant restauration : permissions restrictives (`0700` pour les répertoires, `0600` pour les fichiers sensibles), `SHA256SUMS` valide, `COMPLETE` cohérent avec `COMPLETION.SHA256`, et archive finale non modifiée après la sauvegarde.

## Environnement temporaire

Ressources créées exclusivement pour F5A8 :

- réseau `f5a8-restore-net`, identifiant `923f3d7132faed0c5a0a5dc18d29361ee8c2befbcf693298de1cf01bd6a92bac` ;
- conteneur PostgreSQL `f5a8-restore-db`, identifiant `4f2210bba780cc48227719f314070001d887814db9b019999af00e64ffddbf9b`, image `postgres:16-alpine` ;
- conteneur MinIO `f5a8-restore-minio`, identifiant `dc586d840b3e4fb92cede91d6720f3befd171c6964e92eb0f8ef8bc3bfffc05a`, image `minio/minio:RELEASE.2025-04-22T22-12-26Z`.

Aucun port n’a été publié sur l’hôte. Aucun réseau de production n’a été attaché. Les images ont créé deux volumes anonymes internes pour `/var/lib/postgresql/data` et `/data`; ils n’étaient pas partagés avec la production et ont été supprimés après validation, avec les deux conteneurs et le réseau F5A8 uniquement.

Les identifiants utilisés étaient synthétiques et ne sont pas reproduits ici. Aucune migration Alembic n’a été exécutée.

## Étapes exécutées

1. Création d’une base temporaire vide PostgreSQL 16.
2. Restauration de `postgres/corpus.dump` avec `pg_restore --no-owner --exit-on-error`.
3. Création du bucket temporaire `f5a8-corpus` dans MinIO isolé.
4. Copie des 30 objets depuis l’archive locale.
5. Vérification des tables, contraintes, relations, comptages, révision Alembic, références audio et WAV.
6. Nettoyage limité aux ressources F5A8 identifiées après validation.

La production est restée inchangée : PostgreSQL et MinIO actifs, application arrêtée, volumes et réseau de production conservés.
