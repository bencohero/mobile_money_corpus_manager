# G6 — Revue Git de promotion

## État contrôlé

- `main` : `32edc8716869f67aee0c09123a93b0e454012f33` (`update backup script`)
- `g3-candidate` : `9898c4807f8dc1460cf9b56f74b0ed16dc85d86`
- `g5-hardening` : `48742eb9c1dbcb4ca60ee0c77d2a13c2cca90338`
- Worktree candidate : propre après restauration des artefacts générés par le contrôle.
- Worktree de travail G6 : modifications antérieures non liées présentes ; elles n’ont pas été modifiées.

## Historique candidat

`g5-hardening` est linéaire depuis `main` par `7d5c180`, `9d8c0b1`, `9898c48`, `2be2dbe`, puis `48742eb`.

Le correctif responsive G5.1 est intégré par `48742eb` (`Validate candidate with real Chromium browser`, 2026-10-12 16:07:38 +0200). Ce commit modifie notamment `app/static/style.css`, `app/templates/base.html`, `app/templates/recordings.html` et ajoute les contrôles/captures G5.1. Les preuves rapportent 72 contrôles, zéro overflow et zéro erreur navigateur inattendue.

## Diff et scripts F5

- `git diff --check main...g5-hardening` : propre.
- Merge simulé `main + g5-hardening` : automatique, sans conflit, arrêté avant commit.
- `scripts/backup_local.sh` : même blob dans `main` et candidate (`2a8180b88d5bda37a6e6ecf7fbbe3ef0012827db`).
- Les livrables F5A6, F5A7 et F5A8 sont présents dans les deux historiques et aucune modification de script de sauvegarde n’est introduite par G5.

## Secrets et fichiers générés

Les scans de motifs de clés privées, AWS et tokens connus ne trouvent aucune valeur secrète. Les exemples `.env` sont des modèles, pas des secrets.

Constat bloquant : 12 fichiers `__pycache__/*.pyc` sont versionnés dans `g5-hardening` (`app/` et `migrations/`). Ils sont des artefacts générés et violent le critère d’absence de fichiers générés. Ils doivent être retirés par un commit de nettoyage avant promotion ; ce ticket ne modifie pas la candidate.

## Conclusion Git

La topologie et le contenu fonctionnel sont intégrables, mais la candidate n’est pas promouvable en l’état à cause des `.pyc` suivis. Aucun merge vers `main` n’a été effectué.
