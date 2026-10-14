# G6.1 — Décision finale

## Décision

**READY_WITH_WARNINGS**

## Justification

R1 est levé par le commit de nettoyage `31070e26cfc58721c1d9ed2809c5d82194677da2` : aucun `.pyc`, `__pycache__` ou autre artefact généré n’est suivi, les règles `.gitignore` sont en place, et les sources sont préservées.

R2 est levé : `pip check`, `pip-audit`, Bandit, Gitleaks dépôt complet, Gitleaks diff de release, recherche complémentaire de secrets et contrôles Compose ont été exécutés. Aucune vulnérabilité critique ou haute n’est présente et aucune fuite de secret n’a été détectée.

## Avertissements acceptés

- Bandit : trois alertes faibles liées à `subprocess` et une alerte moyenne B108 sur le chemin `/tmp`, formellement justifiées dans `G6_1_SECURITY_SCAN.md`.
- Huit warnings Python de dépréciation.
- Les preuves navigateur G5.1 utilisent un microphone simulé ; G6.1 n’a introduit aucun changement fonctionnel ou visuel.

La candidate `g5-hardening@31070e2` est prête pour une approbation de merge conditionnelle. Aucun merge vers `main`, déploiement, migration réelle, modification MinIO ou modification d’archive n’a été effectué.
