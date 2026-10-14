# G8.5-R — Prévol final

## Statut : PASS — migration autorisée

Contrôles lecture seule effectués avant migration :

| Contrôle | Résultat |
|---|---|
| Attestation externe restic/fichiers | PASS; snapshot `a4b07220`, dépôt `3ca53008`, SHA et restauration vérifiés |
| Release | PASS; worktree `/tmp/g8-2-release`, HEAD exact et propre |
| Gel applicatif | PASS; aucun conteneur `app` dans la stack |
| Sessions PostgreSQL externes | PASS; `0` dans `pg_stat_activity` au contrôle |
| Révision initiale | PASS; `0005_workshop_attribution` |
| Comptages | PASS; users 21, participants 17, utterances 13, recordings 15, transcriptions 1, audit_logs 116 |
| Archive locale | PASS; `sha256sum -c manifests/SHA256SUMS`, `COMPLETE` et 30/30 objets |
| Rollback coordonné | PASS pour la récupérabilité des fichiers; restauration complète des services non revendiquée |
| Volumes | PASS; PostgreSQL et MinIO existants conservés, aucune recréation/suppression |
| Checkout utilisateur | PASS; non modifié par les opérations de release |

La migration explicite est autorisée. L’accès public et les écritures restent gelés.
