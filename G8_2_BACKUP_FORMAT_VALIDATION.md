# G8.2 — Validation du format de sauvegarde

Le script de release corrigé produit désormais :

- `manifests/SHA256SUMS` via `find -print0`, `sort -z`, `xargs --null --no-run-if-empty`;
- `COMPLETE`;
- `COMPLETION.SHA256` avec une ligne standard `sha256sum COMPLETE`, incluant le nom de fichier;
- une vérification immédiate `sha256sum --check COMPLETION.SHA256` avant publication atomique.

Le test de non-régression vérifie la reproduction de `printf '%s\\0'`, les noms avec espaces et retour ligne, ainsi que le format à deux champs de `COMPLETION.SHA256`.

Résultat : PASS dans le worktree intégré `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`.
