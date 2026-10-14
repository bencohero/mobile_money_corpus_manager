# G6 — Simulation d’intégration

## Procédure

Une worktree temporaire détachée de `main` a été créée sous `/tmp/g6-merge-sim`. La commande exécutée était équivalente à :

```text
git merge --no-commit --no-ff g5-hardening
```

Résultat : merge automatique sans conflit, arrêté avant tout commit. `main` n’a pas été modifiée.

## Contrôles du résultat simulé

- `git diff --check` : PASS.
- Tests JavaScript : 10 pass.
- Compilation Python : PASS.
- Les scripts F5 restent byte-identiques dans le résultat simulé.
- La suite Python complète est passée sur la candidate dans la stack Docker isolée : 159 pass, 1 skip, 8 warnings.

## Commit de merge envisagé

Si la candidate est corrigée puis approuvée, le merge envisagé serait un merge non fast-forward de `g5-hardening` dans `main`, avec un nouveau commit généré par le mainteneur au moment de l’opération. Aucun hash de merge réel ne doit être annoncé à l’avance. Le parent candidat attendu est `48742eb9c1dbcb4ca60ee0c77d2a13c2cca90338`.

## Retour arrière Git

Avant merge, créer un tag ou conserver le SHA `32edc8716869f67aee0c09123a93b0e454012f33`. En cas d’échec avant publication, abandonner le merge. Après publication, revenir par revert du commit de merge selon la politique de dépôt, ou restaurer explicitement `main` vers le SHA validé par une opération approuvée. Ne pas supprimer les branches/worktrees sans autorisation.
