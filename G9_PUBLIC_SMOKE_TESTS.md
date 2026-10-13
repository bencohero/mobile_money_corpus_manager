# G9 — Smoke tests publics

## Résultat

NON EXÉCUTÉS. L’ouverture publique n’a pas eu lieu.

La résolution DNS de corpus-moore.bencoherolab.com pointe vers 169.58.99.71
et le certificat TLS est présenté, mais la réponse HTTPS observée est HTTP 404.
Cela ne constitue pas une ouverture réussie.

Après correction approuvée de Traefik seulement, les contrôles attendus seront :

~~~bash
curl --fail --silent --show-error https://corpus-moore.bencoherolab.com/ready
curl --fail --silent --show-error https://corpus-moore.bencoherolab.com/health
curl --fail --silent --show-error -I https://corpus-moore.bencoherolab.com/
~~~

Puis effectuer les parcours de recette contrôlés : accueil, authentification,
participant, administrateur, CSRF, séparation des rôles, session et rate limit.
Ne pas effectuer de test de charge agressif.

Aucun smoke test public applicatif, dégel métier ou ouverture Traefik n’a été
effectué.

