# G8.7 — Contrôle sécurité préouverture

| Contrôle | Résultat | Observation |
|---|---|---|
| Release / Alembic | PASS | image cible exacte ; `0008_rate_limit_buckets` |
| Réseau applicatif | PASS | app sans ports publiés, backend uniquement |
| Route publique actuelle | PASS fermé | Traefik HTTPS Host approuvé retourne 404 ; aucune route corpus publiée |
| TLS | PASS conditionnel | certificat Let’s Encrypt valide du 31 août au 29 novembre 2026 |
| Host | PASS | Host approuvé 200 en interne ; Host invalide 400 |
| Cookies | PASS code/config | `secure=true`, `httponly` session, `samesite=strict` |
| CSRF | PASS recette | contrôles CSRF exécutés en G8.6-R |
| Sessions | PASS recette | login/logout admin et session participant exécutés |
| IDOR / rôles | PASS recette | participant vers audio hors périmètre : 403 |
| Gel écritures | RÉSERVE | état technique OPEN, `active_writes=0` ; ne pas confondre avec une autorisation de dégel |

Conclusion : la posture reste fermée. Une ouverture publique exige une
configuration Traefik explicitement autorisée et un nouveau contrôle complet.
