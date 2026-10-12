# G5 — Checklist de promotion

- [x] Branche dédiée `g5-hardening`; aucun merge vers `main`.
- [x] Démarrage sans migration implicite.
- [x] Migration explicite et garde de révision.
- [x] Tests migrations/restauration isolée.
- [x] `pip check` et `pip-audit` verts.
- [x] Contrôles secrets, Bandit et réseau exécutés.
- [x] Suite Python : 159 pass, 1 skip, 8 warnings.
- [x] Suite JavaScript : 10 pass.
- [ ] Validation navigateur graphique réelle.
- [x] Rollback 0005 par restauration démontré sur clone.
- [ ] Nouvelle sauvegarde immédiate avant toute migration réelle.
- [ ] Approbation distincte de promotion.

## Blocage résiduel

La validation navigateur reste manuelle/en attente. Le candidat est techniquement durci mais ne doit pas être promu avant clôture de cette case ou acceptation formelle du risque.
