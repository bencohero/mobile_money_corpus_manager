# G9-R3 — Smoke tests publics

Domaine: `https://corpus-moore.bencoherolab.com`.

Après déploiement: HTTPS/TLS joignable, HSTS et `nosniff` présents, `/` redirige vers `/login` (303), `/health` 200, `/ready` 200, `/login` 200, `/participant/register` 200. La route Host Traefik est active.

Les écritures publiques n’ont pas été exécutées contre la production; elles sont couvertes par les tests Compose synthétiques complets, notamment inscription, audio, prises multiples, transcription, validation, rôles, CSRF et rate limits.

Blocage critique confirmé séparément depuis l’IP publique: `http://169.58.99.71:8090/dashboard/` répond 200 et `/api/http/routers` répond 200. Le dashboard Traefik reste donc accessible publiquement. PostgreSQL et MinIO cibles n’ont aucun port publié.
