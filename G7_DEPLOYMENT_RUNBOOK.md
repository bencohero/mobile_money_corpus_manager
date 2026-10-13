# G7 — Runbook de déploiement (préparation uniquement)

## GO/NO-GO avant action

- **GO** seulement si : approbation explicite obtenue, SHA release confirmé, copie VPS indépendante attestée, espace disque suffisant, sauvegarde immédiate possible et accès rollback testé.
- **NO-GO** si : production non identifiée, écritures non gelées, sauvegarde incohérente, révision inattendue, copie indépendante absente, ou contrôle post-migration incomplet.

## Procédure préparée

1. Confirmer le SHA `main@889fd5b` et les images/manifests SHA-256.
2. Annoncer le gel et bloquer les écritures applicatives/workers.
3. Vérifier qu’aucune session d’écriture ne subsiste.
4. Exécuter la sauvegarde PostgreSQL/MinIO immédiate préparée dans `G7_BACKUP_READINESS.md`.
5. Vérifier dump, manifestes, sommes, objets, tailles et copie indépendante. **NO-GO** à la moindre divergence.
6. Arrêter contrôlément les services concernés ; ne pas supprimer les volumes.
7. Vérifier `alembic current` et les préconditions de données.
8. Exécuter explicitement `scripts/migrate.sh` avec cible `0008_rate_limit_buckets`.
9. Vérifier révision, tables, contraintes, index, comptages et état `rate_limit_buckets`.
10. Démarrer l’image applicative compatible avec `0008`; attendre readiness 200.
11. Vérifier logs sans migration implicite et exécuter login, upload, prises multiples, transcription, vérification, export, autorisations et rate limiting.
12. Réconcilier PostgreSQL/MinIO : références audio, objets, tailles, checksums, audit et absence d’orphelins.
13. **GO final** si tous les contrôles sont verts ; lever le gel et surveiller.

## Rollback coordonné

En cas d’échec, conserver le gel, capturer logs/SHA/révision, arrêter la version incompatible, restaurer PostgreSQL et MinIO depuis la sauvegarde immédiatement préalable, vérifier la révision restaurée et les objets, puis redémarrer la version compatible avec le schéma restauré. Ne lever le gel qu’après validation explicite.

## Interdictions G7

Aucune étape ci-dessus n’a été exécutée sur la production. Aucun push, déploiement, `alembic upgrade` réel, redémarrage de production ou modification de volume réel n’est autorisé par ce document.
