# G6.1 — Nettoyage Git

## État initial et final

- HEAD initial de `g5-hardening` : `48742eb9c1dbcb4ca60ee0c77d2a13c2cca90338`.
- HEAD nettoyé : `31070e26cfc58721c1d9ed2809c5d82194677da2`.
- `main` reste à `32edc8716869f67aee0c09123a93b0e454012f33`.
- Aucune modification non committée préexistante dans le worktree candidate ; l’état final est propre.

## Actions

- Inventaire initial : 12 fichiers `.pyc` suivis sous `app/__pycache__` et `scripts/__pycache__`.
- Ajout des exclusions `__pycache__/`, `*.py[cod]`, caches pytest, couverture, rapports Playwright, résultats de tests, `node_modules`, `dist` et `build`.
- Retrait des 12 artefacts de l’index par `git rm --cached` ; aucune source Python supprimée.
- Commit dédié : `31070e2 chore: remove generated Python artifacts`.
- Historique existant non réécrit.

## Vérifications

- Artefacts générés suivis après nettoyage : `0`.
- `git diff --check` : OK.
- Les fichiers Python applicatifs, migrations et scripts restent présents.
- Les artefacts recréés localement pendant les tests sont ignorés et ne sont pas suivis.
