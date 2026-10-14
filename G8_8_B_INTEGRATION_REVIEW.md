# G8.8-B — Revue d’intégration

## Périmètre

- Release de référence : `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`.
- Worktree G8.8-A : `/tmp/g8-8-a-worktree`.
- Commit exact G8.8-A : `b672697a34196841cd5fd9714520166b6edb345b`.
- Branche locale préparée : `g8-8-b-tools`.
- Aucun merge, commit de production, push ou action distante effectuée.

## Écart trouvé et intégré localement

Le `restore.sh` livré par le commit A était encore schema 1 uniquement :
`postgres.dump`, `minio/`, `SHA256SUMS` et `MANIFEST.SHA256` à la racine. Il ne
pouvait donc pas consommer le schema 2 de `backup_local.sh` (`postgres/`,
`manifests/`, `logs/`, `COMPLETE`). La version locale accepte explicitement les
schemas 1 et 2, vérifie la forme exacte, les sommes et la destination isolée.

Le test ajouté `tests/test_restore_contract.sh` couvre les huit cas contractuels
annoncés par G8.8-A. Le changement préexistant de `scripts/backup_local.sh`
(pipeline SHA-256 vide avec `xargs --no-run-if-empty`) est conservé et son test
de régression passe.

## Protection production

Le restore exige `CONFIRM_RESTORE=YES`, un mode `synthetic` ou `isolated`, un
identifiant `synthetic*`/`isolated*`, un alias MinIO non ambigu et un endpoint
explicitement égal à l’endpoint isolé. Les hostnames, alias et endpoint publics
de production sont refusés avant restauration.

Conclusion d’intégration : validée localement, non fusionnée en production.
