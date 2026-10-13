# G9-R2 — Tests publics

Domaine testé: `https://corpus-moore.bencoherolab.com`.

- TLS/DNS: terminaison HTTPS joignable; réponse observée `404 page not found`.
- Routage applicatif: non validé; la route Host n’est pas active sur l’instance observée.
- Accueil, connexion, déconnexion, inscription, audio, prises multiples, transcription et rôles: non exécutés, car l’application n’est pas routée.
- Limites de débit: non certifiables publiquement dans cet état.
- PostgreSQL/MinIO: aucun port publié dans le Compose du dépôt; contrôle local confirmé.
- Dashboard Traefik: blocage critique confirmé. `http://127.0.0.1:8090/dashboard/` répond 200 et `/api/http/routers` répond 200; le port est lié à `0.0.0.0:8090`.

Le dashboard insecure et l’absence de routage applicatif interdisent toute déclaration d’ouverture publique. Aucun changement de configuration Traefik n’a été effectué pour contourner ces défauts.
