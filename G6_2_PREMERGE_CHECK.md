# G6.2 — Prévol merge local

## Références autorisées

- `main` avant merge : `32edc8716869f67aee0c09123a93b0e454012f33`.
- `g5-hardening` : `31070e26cfc58721c1d9ed2809c5d82194677da2`.
- Tag de protection : `pre-g6-2-merge-20261012`, pointant exactement vers `32edc8716869f67aee0c09123a93b0e454012f33`.

## Prévol

- Worktree courant modifié : laissé intact ; aucune modification écrasée.
- Worktrees `g3-candidate`, `g5-hardening` et les worktrees temporaires conservés.
- 12 `.pyc` retirés de l’index dans le commit `31070e2`; aucun artefact généré suivi.
- Résultats G6.1 disponibles et décision `READY_WITH_WARNINGS`.
- Scripts F5A6–F5A8 vérifiés identiques entre `main` et candidate.
- Aucun hook actif de merge/commit/push ne déclenche un déploiement détecté.
- Aucun `git push`, `alembic upgrade` réel ou commande de production exécuté.
