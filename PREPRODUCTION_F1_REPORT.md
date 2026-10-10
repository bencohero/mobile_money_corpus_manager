# Rapport préproduction F.1 — recette VPS et décision Go/No-Go

Date : 2026-10-11  
Release candidate : `cb87475513721fc5816272ee41beaff3b9b13f8a`  
Décision : **NO-GO**.

## Figer la release

- `git rev-parse HEAD` : `cb87475513721fc5816272ee41beaff3b9b13f8a`.
- `git status --short` : propre après exclusion de l’horodatage généré par Graphify.
- Images étiquetées avec `org.opencontainers.image.revision` égal au SHA : runtime
  `sha256:2013e027f1f73d61ea1ee1649b8fc8a4e262b39afc83302cfbc8142a0842bbf8`, test
  `sha256:a390fe249cfb2f7c4c5f8f06346f215c69cf957d033d29b02a6306e47dddbe67`, outils
  `sha256:d7eedec9381d259fac3656dc6549603bd10a683e200cc482450f22338e8e0ee3`.

## Contrôles réussis

- `docker compose ... config --quiet` : réussi.
- Suite candidate Docker : **158 passed, 1 skipped, 8 warnings, 121,70 s**.
- `/health` et `/ready` : HTTP 200 dans l’environnement isolé.
- En-têtes observés : CSP sans `unsafe-inline`, `X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`.
- Alembic : `0008_rate_limit_buckets (head)`.
- PostgreSQL et MinIO préproduction : aucun port publié sur l’hôte ; ressources sous
  le réseau/volumes `mobile-money-corpus-f-lot-*`.
- Bandit, pip-audit et Gitleaks exécutés dans Docker ; détails dans
  [SECURITY_RELEASE_SCAN_REPORT.md](SECURITY_RELEASE_SCAN_REPORT.md).

## Contrôles impossibles à réaliser dans ce ticket

Sans autorisation d’exploitation, accès VPS, DNS, certificat et secrets de
préproduction distincts, les contrôles suivants ne sont pas déclarés réussis :

- HTTPS réel, certificat, DNS et routage Traefik ;
- TrustedHost et en-têtes proxy sur VPS ;
- cookies Secure/HttpOnly/SameSite via navigateur réel ;
- rate limiting avec plusieurs workers ;
- exposition externe PostgreSQL/MinIO, journaux et erreurs sur VPS ;
- recette manuelle ordinateur et Chrome Android ;
- backup/migration/restauration de données historiques réelles ;
- validations signées des responsables données, exploitation, sécurité et produit.

Les parcours fonctionnels automatisés ne remplacent pas la preuve navigateur demandée.
Aucune opération réelle ou destructive n’a été lancée.

## Réserves et décision

1. Bandit conserve trois alertes LOW B404/B603 liées à subprocess/FFmpeg ; acceptation
   explicite ou remédiation sécurité nécessaire.
2. Les contrôles VPS et navigateurs restent critiques et non exécutés.
3. La migration et restauration historiques restent à faire uniquement après accord
   du responsable données.

**NO-GO : une condition critique manque. Aucun déploiement, migration ou action de
production n’est déclenché automatiquement.**
