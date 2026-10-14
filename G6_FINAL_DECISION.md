# G6 — Décision finale

## Décision

**BLOCKED**

## Motifs

La candidate `g5-hardening` (`48742eb9c1dbcb4ca60ee0c77d2a13c2cca90338`) est fonctionnellement validée : Python 159 pass/1 skip/8 warnings, JavaScript 10 pass, preuves Playwright G5.1 à 72 contrôles, migration explicite, garde Alembic, restauration isolée et simulation de merge sans conflit.

La promotion est toutefois bloquée par deux écarts de contrôle :

1. 12 fichiers `__pycache__/*.pyc` sont suivis dans Git, contrairement à l’exigence d’absence de fichiers générés.
2. Les scans Bandit, pip-audit et gitleaks n’ont pas été rejoués dans l’environnement G6 faute d’outils disponibles ; les rapports G5 existants ne remplacent pas complètement une revalidation finale.

## Conditions de sortie

- Retirer les `.pyc` et corriger `.gitignore` dans un commit candidat distinct.
- Rejouer la suite complète et les trois scanners dans l’environnement outillé.
- Refaire l’inventaire Git, la simulation de merge et les contrôles Compose.
- Obtenir une nouvelle décision d’approbation avant tout merge ou déploiement.

Aucun merge, déploiement, migration PostgreSQL réel, modification MinIO réel, redémarrage de production ou modification de sauvegarde n’a été effectué par G6.
