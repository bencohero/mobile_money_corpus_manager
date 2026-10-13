# G8.6-S2 — Précheck de rotation ciblée

## Périmètre autorisé

La rotation préparée cible exclusivement l'utilisateur `benco`, qui doit rester
un compte `ADMIN` actif. Les deux autres comptes `ADMIN` doivent rester
strictement inchangés.

## Garde-fous de la commande

- `--apply` est obligatoire pour écrire ; sans lui, la commande est un dry-run.
- `--confirm-target benco` est obligatoire avec `--apply`.
- `APP_ENV=production` est exigé.
- Le mot de passe est lu sans affichage, depuis une invite ou stdin ; il n'est
  jamais placé dans les arguments ni écrit dans les logs.
- La commande refuse si `benco` est absent, inactif ou si le nombre de comptes
  `ADMIN` n'est pas exactement trois.
- Le hash est généré par `app.auth.hash_password`, donc par le mécanisme bcrypt
  existant.
- Les identités, rôles, états et relations des trois comptes sont contrôlés
  avant commit ; les hashes des deux autres comptes sont comparés avant commit.

## Préconditions opératoires

Avant toute exécution autorisée, vérifier release, Alembic, `/ready`, `/health`,
accès public fermé, manifeste PostgreSQL/MinIO, sauvegarde et gel des écritures
métier. Capturer aussi l'identifiant de version de l'image et l'état du
middleware. Ne pas exécuter si une condition échoue.

