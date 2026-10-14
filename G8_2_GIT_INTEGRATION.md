# G8.2 — Intégration Git

## Relation des versions

- `b672697` est la branche de travail `remediation-a-stabilisation-securite` et n’est pas l’ancêtre de `889fd5b`.
- `889fd5b` (`main`, `g6-2-merge-prep`) descend de `32edc87` (`origin/main`).
- Le correctif a été développé dans `/tmp/g8-2-backup-fix`, worktree propre basé sur `889fd5b`.
- Commit dédié : `d58862f65841274b411a1c73bb404df765fb2a23`.
- Intégration non destructive par cherry-pick dans `g8-2-release-integration` : `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`.

Le worktree utilisateur, `main`, `g6-2-merge-prep` et les autres worktrees existants n’ont pas été écrasés. Aucun push distant n’a été effectué.

## Contrôles

Dans le worktree de release : `bash -n scripts/backup_local.sh tests/test_backup_local.sh`, `tests/test_backup_local.sh` et `git diff --check` sont PASS.
