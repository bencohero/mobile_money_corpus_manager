# G8.5 — Démarrage applicatif contrôlé

## Statut : NON AUTORISÉ / NON EXÉCUTÉ

Le démarrage applicatif n’a pas été effectué, car la migration préalable est bloquée. Au contrôle, seuls les services PostgreSQL et MinIO de la stack étaient actifs; aucun conteneur `app` n’était présent dans `docker compose ps`.

Les volumes existants observés sont conservés :

- `mobile_money_corpus_manager_v0_1_pgdata` → `/var/lib/postgresql/data`;
- `mobile_money_corpus_manager_v0_1_miniodata` → `/data`.

Aucune readiness HTTP, aucun log applicatif et aucun contrôle de démarrage sans migration implicite ne sont déclarés, puisqu’aucun démarrage n’a eu lieu. L’accès public reste fermé et le gel des écritures est maintenu.

Après levée du STOP, le démarrage devra utiliser l’image correspondant exactement à la release autorisée, uniquement le service applicatif nécessaire, les volumes existants, puis vérifier `/ready`, les logs et l’absence de commande Alembic dans l’entrypoint applicatif.
