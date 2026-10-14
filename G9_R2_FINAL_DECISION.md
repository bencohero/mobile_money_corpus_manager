# G9-R2 — Décision finale

## `PUBLIC_OPEN_NO_GO`

Blocages précis:

1. Le healthcheck de la release renvoie 400 avec `Host: localhost` en production (`TrustedHostMiddleware`), donc la stack ne peut pas être déclarée saine avec le Compose actuel.
2. Le domaine HTTPS répond 404: le routage applicatif n’est pas actif sur l’instance observée.
3. Le dashboard Traefik est effectivement accessible sur `:8090` (HTML et API en 200), défaut critique incompatible avec l’ouverture publique.
4. La suite de tests Compose n’a pas produit de résultat exploitable car un volume PostgreSQL de test préexistant est corrompu; `pytest` n’est pas disponible sur l’hôte.

Éléments validés: candidat exact identifié; worktree propre; image reconstruite et digestée; Compose overlay image-only validé; sauvegarde locale schema 2 validée; restauration PostgreSQL/MinIO isolée validée; aucun `docker cp`, aucune modification Traefik, aucun secret de production exposé dans les livrables.

Risque résiduel documenté: `EXTERNAL_BACKUP_PENDING_MANUAL_OPERATOR_ACTION`. L’opérateur doit réaliser la copie Kubuntu/restic séparément.

Prochaine action obligatoire: corriger versionnellement le couple healthcheck/TrustedHost, traiter l’exposition du dashboard côté infrastructure selon la procédure opérateur, reconstruire une nouvelle image, puis refaire les tests publics complets. Aucun déploiement ou dégel métier n’est autorisé avant ces preuves.
