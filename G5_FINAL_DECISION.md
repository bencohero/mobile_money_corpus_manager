# G5 — Décision finale

## Décision

**READY_WITH_WARNINGS**

## Justification

Le durcissement des migrations est réalisé : aucun chemin de démarrage validé n’exécute automatiquement Alembic, la commande explicite `scripts/migrate.sh` est disponible et le garde-fou de révision refuse le démarrage sur schéma incompatible. La stack G5 isolée a restauré F5A7.2, migré explicitement vers 0008, redémarré sans migration implicite et démontré une restauration isolée au schéma 0005.

Les validations sécurité sont vertes : `pip check`, `pip-audit`, tests applicatifs, contrôles de secrets et Compose. La suite finale compte 159 tests Python réussis, 1 ignoré et 8 avertissements; les 10 tests JavaScript réussissent.

La réserve restante est la validation visuelle réelle : aucun navigateur compatible n’était disponible. Elle est explicitement en attente dans `G5_BROWSER_VALIDATION.md`. La décision n’autorise ni merge vers `main` ni déploiement; elle autorise uniquement une revue de promotion conditionnelle après clôture de cette réserve.
