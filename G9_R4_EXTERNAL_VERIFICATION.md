# G9-R4 — Vérification externe

Statut au 2026-10-13 : **NON EXÉCUTÉE APRÈS CORRECTION**

## Preuve disponible avant correction

Les requêtes suivantes ont été lancées depuis le VPS lui-même :

```text
http://127.0.0.1:8090/dashboard/       HTTP 200
http://127.0.0.1:8090/api/http/routers HTTP 200
http://169.58.99.71:8090/dashboard/    HTTP 200
http://169.58.99.71:8090/api/http/routers HTTP 200
https://corpus-moore.bencoherolab.com/health HTTP 200
https://corpus-moore.bencoherolab.com/ready  HTTP 200
https://corpus-moore.bencoherolab.com/login  HTTP 200
```

Le résultat sur `169.58.99.71` n’est pas une preuve indépendante : le point de
mesure est le serveur cible et peut bénéficier d’un chemin local/hairpin.

## Procédure depuis un réseau indépendant

Exécuter depuis une machine qui n’est pas le VPS, son réseau Docker ou son VPN
de management :

```sh
nc -4 -vz -w 5 169.58.99.71 8090
curl -4 -m 10 -sS -o /dev/null -w '%{http_code}\n' \
  http://169.58.99.71:8090/dashboard/
nc -6 -vz -w 5 2a02:c207:2347:4447::1 8090
curl -4 -m 10 -fsS https://corpus-moore.bencoherolab.com/health
curl -4 -m 10 -fsS https://corpus-moore.bencoherolab.com/ready
curl -4 -m 10 -I https://corpus-moore.bencoherolab.com/login
```

Attendu : `8090` ne permet ni connexion ni réponse HTTP en IPv4/IPv6; HTTPS
reste disponible. Le test SSH doit être effectué avec une session indépendante
ou une sonde approuvée, sans fermer la session de secours.

## Parcours applicatif requis

Après fermeture de `8090`, valider avec un compte de test approuvé : ouverture
de `/login`, connexion, accès à la page autorisée, déconnexion, puis refus
d’accès aux pages authentifiées. Ne pas exécuter d’écriture métier contre les
données de production sans autorisation dédiée; les parcours mutatifs restent
couverts par les tests synthétiques existants.

## Résultat actuel

La vérification externe indépendante post-correction ne peut pas être déclarée
PASS, car la correction n’a pas été appliquée et l’outil externe disponible ne
permet pas de sonder ce port TCP. Cette preuve doit être complétée par
l’opérateur réseau après application.
