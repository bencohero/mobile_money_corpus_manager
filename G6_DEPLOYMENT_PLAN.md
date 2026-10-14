# G6 — Checklist opérateur de promotion et déploiement

Le déploiement réel est hors périmètre G6. Cette checklist doit être exécutée par un opérateur autorisé après approbation distincte.

## Avant migration

- [ ] Confirmer SHA de release, tag, version applicative et images réellement utilisées.
- [ ] Vérifier les manifestes et calculer/vérifier les SHA-256 des artefacts.
- [ ] Vérifier que `main` contient le merge approuvé et que la candidate n’a plus de `.pyc` suivis.
- [ ] Prendre immédiatement une nouvelle sauvegarde PostgreSQL custom et MinIO, hors dépôt et hors volumes de production applicatifs.
- [ ] Vérifier lisibilité, inventaire, taille, checksum et restauration de test de cette sauvegarde.
- [ ] Vérifier l’accès opérateur et la procédure de restauration coordonnée.

## Migration contrôlée

- [ ] Geler les écritures et confirmer le gel dans les logs/endpoint opérateur.
- [ ] Arrêter ou isoler les workers qui écrivent, selon le runbook approuvé.
- [ ] Vérifier la révision courante et les préconditions de données.
- [ ] Exécuter explicitement `scripts/migrate.sh` avec cible `0008_rate_limit_buckets`.
- [ ] Vérifier `alembic current`, les contraintes/index et les comptes de contrôle.
- [ ] Ne jamais laisser l’application effectuer une migration au démarrage.

## Redémarrage et contrôles

- [ ] Démarrer l’image compatible avec `0008`.
- [ ] Vérifier readiness, logs sans migration implicite et absence d’erreurs de schéma.
- [ ] Vérifier login, autorisations, enregistrement/upload, transcription, export et rate limiting.
- [ ] Vérifier PostgreSQL et MinIO : objets, compteurs, audit et intégrité.
- [ ] Lever le gel seulement après validation et décision opérateur.

## Échec / restauration

- [ ] Maintenir le gel et empêcher toute nouvelle écriture.
- [ ] Capturer logs, SHA, révision et état des services.
- [ ] Arrêter la version incompatible.
- [ ] Restaurer PostgreSQL et MinIO depuis la sauvegarde prise immédiatement avant migration, dans l’ordre documenté et de façon coordonnée.
- [ ] Vérifier la révision restaurée, les comptes, objets et parcours critiques.
- [ ] Redémarrer la version compatible avec le schéma restauré.
- [ ] Documenter l’incident et ne lever le gel qu’après validation explicite.
