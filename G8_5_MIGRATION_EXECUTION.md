# G8.5 — Exécution de migration

## Statut : BLOCKED — NON EXÉCUTÉE

La migration n’a pas été lancée. Le STOP de la phase pré-migration est obligatoire :

1. le checkout courant est `b672697a34196841cd5fd9714520166b6edb345b`, et non la release autorisée `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`;
2. l’attestation externe/restic du snapshot `a4b07220` n’est pas présente (`G8_1_OFFSITE_ATTESTATION.md` reste `PENDING`).

La commande approuvée, à exécuter uniquement après levée du STOP, est celle de l’interface de la release autorisée :

```bash
ALEMBIC_TARGET=0008_rate_limit_buckets scripts/migrate.sh
```

Cette commande doit être lancée depuis exactement la release autorisée, avec capture de stdout/stderr et durée. Elle doit ensuite confirmer `alembic current`, les révisions `0006`, `0007`, `0008`, le schéma et l’intégrité PostgreSQL/MinIO. Aucun log de migration, aucune durée et aucun résultat post-migration ne peuvent être déclarés dans cette phase.

Révision observée avant arrêt : `0005_workshop_attribution`.
