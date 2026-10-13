# G8.1 — Tests de sauvegarde

## Tests exécutés

| Contrôle | Résultat |
|---|---|
| `bash -n scripts/backup_local.sh` | PASS |
| `bash -n tests/test_backup_local.sh` | PASS |
| Reproduction de `printf '%s\\0'` | PASS — absence de NUL démontrée |
| Noms contenant espaces et retour ligne | PASS — pipeline NUL + SHA-256 valide |
| Volume MinIO vide isolé | PASS — manifeste limité à `MANIFEST.json` |
| `git diff --check` | PASS |

Le test de non-régression est [tests/test_backup_local.sh](tests/test_backup_local.sh). Il ne contacte aucun conteneur et n’écrit que dans un répertoire temporaire créé par le test.

## Test d’archive historique

L’archive existante `/home/sangouman/mobile-money-corpus-backups/20261012T233614Z` a validé les entrées de `manifests/SHA256SUMS` et contient `COMPLETE`. En revanche, son `COMPLETION.SHA256` ne contient pas le nom de fichier; `sha256sum --check COMPLETION.SHA256` échoue. Elle n’est donc pas promue comme nouvelle archive G8.1.

Une exécution complète de `backup_local.sh` sur la production n’a pas été lancée : le prévol lecture seule ne fournit pas d’attestation `FROZEN` courante ni de destination d’archive approuvée. Aucun volume n’a été touché.
