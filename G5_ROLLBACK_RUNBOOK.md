# G5 — Runbook restauration et retour arrière

## Préconditions

1. Geler les écritures applicatives et confirmer le gel dans les journaux.
2. Capturer une nouvelle sauvegarde PostgreSQL custom et le contenu MinIO immédiatement avant toute migration réelle.
3. Vérifier `SHA256SUMS`, la révision Alembic et les comptages de référence.
4. Noter le commit applicatif et la révision cible.

## Migration contrôlée

1. Arrêter l’application ou maintenir le gel d’écriture.
2. Exécuter explicitement `scripts/migrate.sh` avec l’autorisation d’exploitation.
3. Vérifier la révision attendue, contraintes, séquences, comptages et réconciliation PostgreSQL/MinIO.
4. Démarrer le code compatible; l’application doit refuser toute révision divergente.
5. Lever le gel uniquement après readiness et contrôles fonctionnels.

## Retour arrière

Ne pas utiliser Alembic downgrade. Restaurer une sauvegarde cohérente PostgreSQL au schéma 0005 et les objets MinIO correspondants dans un environnement coordonné, puis redémarrer le code correspondant à la sauvegarde.

La procédure a été rejouée dans G5 sur `db-restore` et `minio-restore` : SHA-256 F5A7.2 valides, révision `0005_workshop_attribution`, 17 participants, 15 enregistrements et 1 transcription. La restauration est restée isolée.

## Vérifications post-restauration

- Révision Alembic attendue.
- Comptages et séquences.
- Contraintes et clés étrangères.
- Présence et hash des objets audio.
- Réconciliation PostgreSQL/MinIO.
- Readiness et parcours métier minimaux.
