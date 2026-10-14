# G9-R2 — Construction release

Worktree: `/tmp/g9-r2-release-8f688e8`

Commit: `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`

Image construite depuis le Dockerfile candidat:

- tag: `mobile-money-corpus:8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`
- image ID / manifeste: `sha256:3f13523f19c919b979cbaed70919205811d19d535e9e36077150ce43a96a9417`
- taille: 269655875 octets
- labels: `org.opencontainers.image.revision` fixé au SHA exact

Contrôles: `compileall` PASS; image runtime PASS; `/app/alembic.ini`, migrations jusqu’à `0008`, `app/write_freeze.py`, scripts de sauvegarde/restauration présents; aucun `.env` et aucun placeholder de secret trouvé dans `/app`.

`pytest` hôte n’est pas installé. L’exécution Compose de tests n’a pas abouti car le volume de test PostgreSQL préexistant est corrompu/incompatible (`invalid checkpoint record`); aucun volume n’a été supprimé. Le démarrage isolé de l’image a fonctionné, mais son healthcheck `/ready` retourne 400 avec `Host: localhost` à cause de `TrustedHostMiddleware` en production.

Manifeste reproductible: [G9_R2_RELEASE_MANIFEST.json](G9_R2_RELEASE_MANIFEST.json).
