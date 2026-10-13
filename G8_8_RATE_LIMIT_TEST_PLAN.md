# G8.8 — Plan de tests rate limiting

Les tests d’atteinte de seuil sont interdits sur la production actuelle et
doivent être exécutés uniquement sur une restauration isolée ou une cible de
test dédiée.

| Scénario isolé | Limite d’essais | Résultat attendu |
|---|---:|---|
| Login invalide | 3 puis seuil contrôlé | 401, puis 429 avec Retry-After |
| Lookup code invalide | 3 puis seuil contrôlé | 400, puis 429 |
| Inscription invalide | 3 puis seuil contrôlé | 400/403, aucune ligne créée |
| Rejeu idempotent valide | 2 | même résultat, aucun doublon |

Seuils release : login `10/300 s`, inscription `60/600 s`, lookup
`20/600 s`. Les tests doivent utiliser des identités et clés synthétiques,
réinitialiser la cible isolée entre scénarios et relever les buckets avant/après.
Pas de concurrence, de boucle non bornée ni de test de charge.

Après activation future de Traefik, vérifier séparément TLS/certificat,
Host approuvé/non approuvé, route exacte, cookies Secure/HttpOnly/SameSite,
CSRF et session ; ces contrôles ne doivent pas être déduits d’une cible isolée.

Le mécanisme write-freeze doit suivre `OPEN → DRAINING → FROZEN`, confirmer
`active_writes=0`, exécuter l’opération autorisée, puis revenir à `OPEN` seulement
sur autorisation explicite. G8.8 ne change pas cet état.
