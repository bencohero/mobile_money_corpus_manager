# G8.8-A — Contrat backup/restore versionné

## Contrat schema 1 — historique `backup.sh`

Racine exacte : `MANIFEST.json`, `MANIFEST.SHA256`, `SHA256SUMS`,
`postgres.dump`, `minio/`, `minio_inventory.jsonl`.

Le manifest porte `schema=1`, `postgres_dump=postgres.dump`,
`minio_bucket` et `minio_file_count`. Les deux listes SHA-256 sont vérifiées
depuis la racine. Le nombre d’objets MinIO attendu doit correspondre au manifest.

## Contrat schema 2 — `backup_local.sh`

Racine exacte : `MANIFEST.json`, `COMPLETE`, `COMPLETION.SHA256`,
`postgres/`, `minio/`, `manifests/`, `logs/`.

Le manifest porte `schema=2`, `status=COMPLETE`,
`postgres_dump=postgres/corpus.dump`, `minio_bucket` et
`minio_object_count`. Les chemins attendus sont stricts ; `minio/<bucket>/`
est l’unique sous-arbre d’objets. `COMPLETION.SHA256` vérifie `COMPLETE` et
`manifests/SHA256SUMS` vérifie exactement le dump, le manifest et les objets.

## Règles communes

- schéma inconnu, statut incomplet, lien symbolique, chemin absolu ou `..` :
  refus ;
- fichier manquant, inattendu, non couvert par SHA-256 ou somme invalide :
  refus ;
- cible PostgreSQL et endpoint MinIO doivent être explicitement isolés ;
- `RESTORE_TARGET_ID` doit commencer par `isolated-` ou `synthetic-` ;
- le backup source n’est jamais modifié ;
- aucun restore de production n’est permis par le consommateur.

Le consommateur corrigé est `scripts/restore.sh` dans ce worktree isolé.
