# Plan de migration 0005 → 0008

Statut : plan préparé, migration de production non exécutée.

## Séquence contrôlée

1. Geler les écritures applicatives et inventorier les volumes : utilisateurs, participants,
   ateliers, langues, prises, objets MinIO, transcriptions/historique, audit et compteurs.
2. Faire un `pg_dump --format=custom` PostgreSQL et un miroir MinIO avec vérification des
   tailles et SHA-256. Conserver les sauvegardes hors des volumes applicatifs.
3. Restaurer les deux sauvegardes dans un environnement isolé (`db-restore` et
   `minio-restore` du Compose de test), puis vérifier que les comptes, participants,
   ateliers, prises et transcriptions sont lisibles.
4. Diagnostiquer avant migration les codes de langue absents/invalides, les références
   participant/atelier/utterance orphelines et les objets audio manquants.
5. Sur la copie restaurée uniquement, exécuter successivement `alembic upgrade 0006_...`,
   `0007_integrity_and_transcription_versions`, puis `0008_rate_limit_buckets`.
6. Vérifier après chaque étape l’unicité des identités multilingues, les références,
   l’historique de transcription, les compteurs de prises, les contraintes PostgreSQL et
   `alembic current` = `0008_rate_limit_buckets`.
7. Répéter les tests HTTP, audio Range, transcription concurrente, exports SHA-256,
   permissions, CSRF, rate limiting, liveness et readiness.
8. En cas d’échec, arrêter l’application, restaurer PostgreSQL et MinIO ensemble, puis
   revalider les SHA-256 et la version Alembic. Il n’existe pas de downgrade métier sûr.

## Fenêtre et retour arrière

L’estimation initiale est de 30–60 minutes hors correction de données : sauvegarde,
restauration de contrôle, migration et smoke tests. La durée réelle doit être mesurée sur
une copie de taille représentative. La mise en production reste bloquée tant que cette
mesure, le test de restauration et la validation humaine des écarts ne sont pas signés.

La migration ne doit jamais être lancée avec les volumes de production dans ce ticket.
