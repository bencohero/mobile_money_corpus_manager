# G4 — État de préparation au déploiement

## Points validés

- HEAD candidate exact et worktree contrôlés.
- Différence avec `main` documentée par G3; aucun merge vers `main`.
- Scripts et preuves de sauvegarde F5A6–F5A8 conservés byte à byte par rapport à `main`.
- Archive F5A7.2 vérifiée par SHA-256 et restaurée uniquement dans le clone.
- Migrations 0006–0008 exécutées avec données conservées et état Alembic à 0008.
- Stack isolée, sans ports publiés, sans partage de volumes ou réseau de production.
- Suite Python : 158 pass, 1 skip, 8 warnings.
- Suite JavaScript : 10 pass.
- Readiness, redémarrage et réconciliation : réussis.

## Actions avant promotion

1. Exécuter les tests navigateur manuels mobile et desktop.
2. Exécuter dans CI le scanner de dépendances complet et le contrôle de secrets.
3. Retirer la migration implicite de la commande de démarrage ou l’encadrer par une procédure de déploiement approuvée.
4. Rejouer la restauration isolée comme procédure de rollback et archiver sa preuve.

La promotion vers `main` et le déploiement réel ne sont pas autorisés par G4.
