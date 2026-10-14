# G8.6-S3 — Validation d'authentification

## Statut : `AUTH_RESTORED`

Attestations opérateur enregistrées :

```text
login=303 admin-users=200 logout=303
old_login=401
```

La valeur actuelle de `.env` est le nouveau secret configuré avant la rotation.
Son acceptation après alignement du hash est confirmée. Le contrôle séparé de
l'ancien secret a été exécuté une seule fois par l'opérateur avec saisie
masquée ; le résultat 401 est attesté.

Le hash, le mot de passe, les cookies et les jetons CSRF n'ont pas été affichés
ni enregistrés. Aucun `JWT_SECRET` n'a été modifié.

## Flux validé

1. GET `/login` avec extraction du formulaire et du cookie CSRF ;
2. POST `/login` avec le formulaire réel ;
3. GET `/users` avec session ADMIN, HTTP 200 ;
4. POST `/logout`, HTTP 303 ;
5. ancien mot de passe refusé, HTTP 401.

