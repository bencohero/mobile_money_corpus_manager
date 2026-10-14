# G8 — Prévol de déploiement

Date de contrôle : 2026-10-13 (Europe/Berlin)

## Références

- Release attendue : `889fd5b018f038d6166d8ef0afa976426392fa79`
- Révision production observée : `0005_workshop_attribution`
- Révision cible : `0008_rate_limit_buckets`
- Worktree de release contrôlée : `/tmp/g6-2-merge-prep`

## Résultats

| Contrôle | Résultat |
|---|---|
| SHA `main` | conforme, `889fd5b018f038d6166d8ef0afa976426392fa79` |
| Worktrees | inventoriés, conservés ; aucun reset/nettoyage destructif |
| Worktree de release | propre, HEAD conforme |
| Worktree courant | modifications et rapports existants préservés |
| PostgreSQL | `postgres:16-alpine`, sain, conteneur inchangé |
| MinIO | `RELEASE.2025-04-22T22-12-26Z`, sain, conteneur inchangé |
| Application | conteneur absent ; aucun service applicatif actif |
| Volumes | `pgdata`, `miniodata`, `tmpaudio` conservés |
| Révision Alembic | `0005_workshop_attribution` |
| Compose release | `docker compose config --quiet` réussi sans afficher les valeurs |
| Disque | 87 Go disponibles, 56 % utilisés ; inodes 7 % utilisés |
| Sessions PostgreSQL | aucune session externe observée lors du contrôle |

Les ports PostgreSQL/MinIO ne sont pas publiés sur l’hôte. Aucun processus de déploiement automatique, push Git ou redémarrage n’a été déclenché.

## Point d’arrêt

Le prévol ne permet pas de poursuivre vers la migration : aucun dépôt restic ni montage/copie Kubuntu n’est disponible ou attestable sur cet hôte. La procédure G8 impose une copie externe récupérable avant toute migration.

Conclusion prévol : **NO-GO — arrêt avant migration**.
