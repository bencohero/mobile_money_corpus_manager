# G8.5-R — Décision finale

## `DEPLOYED_AWAITING_SMOKE_TEST`

La migration contrôlée est réussie et l’application est démarrée de façon contrôlée depuis la release autorisée.

### Preuves principales

- Attestation restic/fichiers vérifiée : snapshot `a4b07220`, dépôt `3ca53008`, `restic check --read-data` PASS, restauration de 102 fichiers/dossiers, sommes SHA PASS.
- Worktree de release propre et HEAD exact : `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`.
- Migration explicite réussie vers `0008_rate_limit_buckets`, code retour 0, durée 8,59 s.
- Données historiques inchangées; PostgreSQL et MinIO cohérents.
- Readiness HTTP PASS; aucune migration implicite dans les logs.
- Image applicative sur le réseau backend uniquement; accès public fermé.

### Restrictions maintenues

- Pas d’ouverture publique.
- Pas de dégel des écritures.
- Aucun push Git distant.
- Aucun nettoyage Git destructif.
- Aucun volume supprimé ou recréé.

La prochaine étape autorisée est une recette/smoke test explicitement approuvée, avec écritures contrôlées. La preuve externe reste qualifiée comme restauration vérifiée des fichiers, et non comme restauration complète des services PostgreSQL/MinIO.
