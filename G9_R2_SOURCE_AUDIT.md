# G9-R2 — Audit source

Date: 2026-10-13

## Résultat

Le candidat validé pour reconstruction est `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`, branche `g8-2-release-integration`. Il s’agit aussi de la release active de référence demandée. Le checkout courant `g8-8-b-tools` pointe sur `b672697` et contient de nombreuses modifications locales et artefacts d’audits; il n’a pas été utilisé pour construire l’image.

Branches inspectées: `main`, `dev`, `g3-candidate`, `g5-hardening`, `g6-2-merge-prep`, `g8-2-release-integration`, `g8-8-b-tools`, `remediation-a-stabilisation-securite`.

Le candidat a été vérifié dans `/tmp/g9-r2-release-8f688e8`, worktree détaché propre, sans modification Git. Les différences `8f688e8..b672697` incluent notamment des suppressions d’artefacts/audits, des changements UI, des scripts de sauvegarde et des fichiers générés; elles ne sont pas une base sûre implicite de release.

## Architecture observée

- `docker-compose.yml`: services `app`, `db`, `minio`.
- `app`: réseaux `backend` interne et `frontend` externe; aucun port publié; healthcheck `/ready`; dépend de PostgreSQL et MinIO sains; restart `unless-stopped`.
- `db` et `minio`: backend uniquement, volumes nommés persistants, aucun port publié.
- Traefik: labels présents sur `app`, route `websecure`, TLS, resolver `ovhcloud`, service interne port `8000`, réseau `frontend`.
- `Dockerfile`: runtime multi-stage, UID `10001`, migrations, scripts, `alembic.ini`; aucune copie manuelle de code dans un conteneur.
- Migrations candidates jusqu’à `0008_rate_limit_buckets`.

Les valeurs d’exemple de `.env.example` sont des placeholders explicites et ne sont pas utilisées comme production. Aucun secret réel n’a été écrit dans les rapports.
