# G8.6-R — Tests de sécurité limités

| Contrôle | Résultat | Preuve |
|---|---|---|
| CSRF inscription | PASS | requête sans jeton valide refusée HTTP 403 |
| CSRF parcours admin | PASS | requêtes réalisées avec cookie + jeton réel |
| IDOR participant vers audio historique | PASS | `MOS_018` vers audio 15 : HTTP 403 |
| Rôle VALIDATOR | PASS | validation autorisée ; écriture de transcription non utilisée |
| Rôle TRANSCRIBER | PASS | transcription/correction autorisées |
| Session admin | PASS | `benco` login 303, `/users` 200, logout 303 |
| Rate limiting | PARTIEL | buckets contrôlés, aucun test de charge ; limites agressives non rejouées |
| Accès public | PASS | conteneur backend-only, aucun port applicatif publié, Host non approuvé HTTP 400 |

Aucun test de charge n’a été exécuté. Aucun secret, cookie, jeton ou hash n’est
présent dans les rapports.
