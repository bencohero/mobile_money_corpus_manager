# G8.7 — Revue rate limiting

## Seuils configurés dans la release

| Scope | Limite | Fenêtre |
|---|---:|---:|
| Login | 10 | 300 s |
| Inscription participant | 60 | 600 s |
| Lookup langue/code atelier | 20 | 600 s |

Le rate limiter est partagé PostgreSQL (`rate_limit_buckets`) avec repli mémoire
borné en cas d’indisponibilité DB. Le bucket observé est technique, expiré au
moment du contrôle ; aucune suppression manuelle n’a été exécutée.

## Tests négatifs préparés, non exécutés en charge

- login invalide : au plus 3 requêtes, vérifier 401 puis 429 au seuil documenté ;
- lookup code invalide : au plus 3 requêtes, vérifier 400 puis comportement de
  limite sans dépasser 20 requêtes/600 s ;
- inscription invalide : au plus 3 requêtes, vérifier 400/403 sans création ;
- aucun test concurrent, volumétrique ou de charge.

La décision d’exécuter ces tests nécessite une autorisation opérateur distincte
si elle doit produire des écritures de buckets ou des audits.
