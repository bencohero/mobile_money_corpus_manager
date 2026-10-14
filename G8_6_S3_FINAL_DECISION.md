# G8.6-S3 — Décision finale

## `AUTH_RESTORED`

Les attestations opérateur sont complètes :

```text
login=303 admin-users=200 logout=303
old_login=401
```

Les contrôles complémentaires sont passants : `/ready` et `/health` à 200,
Alembic `0008_rate_limit_buckets`, comptes `admin`/`benco`/`laurent` actifs et
ADMIN, PostgreSQL stable hors deux audits `LOGIN` attendus, MinIO identique et
`ADMIN_PASSWORD` runtime cohérent avec `.env`.

L'accès public reste fermé, les écritures métier générales restent gelées,
`JWT_SECRET` n'a pas été modifié et aucune migration, redémarrage ou suppression
de volume n'a été effectué.

## Suite autorisée

État suivant : `READY_FOR_G8_6_R_APPROVAL`. Le plan de reprise est documenté
dans [G8_6_R_RESUMPTION_PLAN.md](G8_6_R_RESUMPTION_PLAN.md). Aucun test
d'écriture G8.6-R n'est exécuté par cette décision.

