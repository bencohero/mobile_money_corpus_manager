# G9-R3 — Correction healthcheck

Commit: `2698530f7a77a6d9222049c0d911f49fb56c36ae` on `g9-r3-healthcheck`.

En production, `app.main` transforme `TRUSTED_HOSTS=*` en `APP_HOST` et installe `TrustedHostMiddleware`; le healthcheck Compose envoyait `Host: localhost`, donc `/ready` répondait 400. Le Dockerfile ne définit aucun `HEALTHCHECK`; le healthcheck applicatif est celui de `docker-compose.yml`.

Correction: le healthcheck conserve `TrustedHostMiddleware` et envoie `Host: ${APP_HOST}` vers `http://127.0.0.1:8000/ready`. Tests ajoutés pour `/health` et `/ready` avec l’hôte autorisé et un hôte interdit.

Résultat: `16 passed, 1 skipped`; le conteneur corrigé est devenu healthy en production isolée.
