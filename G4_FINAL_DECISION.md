# G4 — Décision finale

## Décision

**PREPROD_VERIFIED_WITH_WARNINGS**

## Motifs

La candidate `g3-candidate` au commit `9d8c0b1feaf86e22cf8c7e8ae8b1fafdf1e8ae41` fonctionne dans une stack de préproduction isolée sur les données restaurées F5A7.2. Les migrations 0006, 0007 et 0008 ont atteint le head sans perte d’intégrité; la suite applicative a produit 158 succès, 1 test ignoré et 8 avertissements; les contrôles JavaScript ont produit 10 succès; la readiness, les redémarrages et la réconciliation PostgreSQL/MinIO sont verts.

Les avertissements sont non bloquants mais doivent être levés avant promotion : absence de navigateur graphique pour la validation visuelle manuelle, scanner de dépendances exhaustif non relancé dans l’image d’outils minimale, et migration Alembic actuellement déclenchée par la commande de démarrage de test.

## Portée et interdictions respectées

Aucun merge, cherry-pick, déploiement, redémarrage de production, accès public, migration de production ou modification de l’archive F5A7.2 n’a été effectué. Les ressources G4 restent isolées et les worktrees préexistants ont été conservés.

Promotion vers `main` : **non autorisée par ce ticket**; elle requiert une approbation distincte après levée des avertissements.
