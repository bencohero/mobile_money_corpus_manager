# G8.5-R — Exécution de migration

## Statut : PASS

### Commande exécutée

Depuis `/tmp/g8-2-release`, HEAD `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6` :

```text
ALEMBIC_TARGET=0008_rate_limit_buckets scripts/migrate.sh
```

Exécution dans l’image runtime construite depuis ce worktree, contre les services PostgreSQL/MinIO existants.

### Résultat

- Code retour : `0`.
- Durée réelle : `8,59 s`.
- Sortie Alembic finale : `0008_rate_limit_buckets (head)`.
- Chaîne vérifiée : `0005 → 0006 → 0007 → 0008`.
- Tables créées présentes : `participant_language_sequences`, `transcription_history`, `rate_limit_buckets`.
- Index/contraintes vérifiés : index d’expiration de rate limit, clés primaires, contrôles de non-négativité et clés étrangères de l’historique.
- Comptages historiques inchangés : users 21; participants 17; utterances 13; recordings 15; transcriptions 1; audit_logs 116.
- MinIO live vérifié : 30 objets, 5 289 708 octets; cohérent avec l’archive.

Aucun échec n’a déclenché de rollback. Aucun rollback partiel PostgreSQL n’a été effectué.
