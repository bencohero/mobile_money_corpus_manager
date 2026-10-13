# G8.5-R — Démarrage applicatif contrôlé

## Statut : PASS — accès public fermé

- Image : `mobile_money_corpus_manager_g8_5_r:8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`.
- Provenance : label `org.opencontainers.image.revision=8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`.
- Image runtime vérifiée : CMD `uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers`.
- Conteneur : `mobile_money_corpus_manager_g8_5_r-app`.
- Réseau : backend uniquement (`mobile_money_corpus_manager_v0_1_backend`); aucun réseau frontend/Traefik attaché.
- Volume réutilisé : `mobile_money_corpus_manager_v0_1_tmpaudio`; aucun volume créé, supprimé ou recréé.
- PostgreSQL et MinIO existants laissés en place.
- Readiness : `/ready` répond `200` et `{"status":"ready"}` avec le Host de production.
- Logs : démarrage Uvicorn réussi; aucune occurrence de migration/Alembic implicite.

Un premier appel sans Host approuvé a répondu `400`, puis le contrôle avec le Host de production a répondu `200 OK`; cela confirme le contrôle d’hôte en production. L’accès public reste fermé et les écritures restent gelées.
