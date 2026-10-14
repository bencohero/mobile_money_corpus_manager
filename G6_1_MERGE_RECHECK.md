# G6.1 — Nouvelle simulation de merge

## Procédure

Une worktree temporaire `/tmp/g6-1-merge-sim` a été créée depuis `main@32edc87`, puis la candidate nettoyée a été intégrée avec :

```text
git merge --no-commit --no-ff g5-hardening
```

Résultat : merge automatique sans conflit, arrêté avant commit. `main` n’a pas été modifiée.

## Contrôles

- `git diff --check` : OK.
- Artefacts générés suivis dans le résultat : `0`.
- Tests JavaScript sur le résultat simulé : `10 passed`.
- Scripts F5A6–F5A8 : inchangés.
- La simulation ne produit aucun commit de merge réel.
