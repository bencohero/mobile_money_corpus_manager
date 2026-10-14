# G9-R4 — Décision finale

Date : 2026-10-13  
Décision : **PUBLIC_OPEN_NO_GO**

## Motif

Le critère `PUBLIC_OPEN_GO` n’est pas satisfait. Le dashboard/API Traefik est
encore accessible publiquement sur TCP `8090` avec HTTP 200. La règle réseau
proposée n’a pas été appliquée, car le compte courant ne permet ni lecture
privilégiée fiable du pare-feu ni modification root, et aucune preuve de règle
Contabo n’est disponible.

## Contrôles passés

- Application healthy : conteneur `app` healthy, `/health` 200, `/ready` 200.
- HTTPS : `corpus-moore.bencoherolab.com` répond sur `/health`, `/ready` et
  `/login`.
- SSH : port local `22` en écoute.
- Pas de modification de Traefik, PostgreSQL, MinIO ou de l’image applicative.

## Contrôles bloquants

- Blocage public IPv4/IPv6 de `8090` : **FAIL**, exposition confirmée.
- Pare-feu UFW/nftables/iptables effectif : **NON PROUVÉ**, privilèges root absents.
- Pare-feu Contabo : **NON PROUVÉ**.
- Vérification externe post-correction : **NON EXÉCUTÉE**.
- Connexion/déconnexion après correction : **NON EXÉCUTÉES**.

## Action de clôture

Un opérateur autorisé doit appliquer la correction documentée dans
`G9_R4_FIREWALL_CHANGE.md`, puis compléter `G9_R4_EXTERNAL_VERIFICATION.md`.
La décision pourra devenir `PUBLIC_OPEN_GO` uniquement après preuve indépendante
que `8090` est bloqué en IPv4 et IPv6, que HTTPS et SSH restent accessibles,
que `/health` et `/ready` restent sains, que les parcours requis passent et
qu’aucune anomalie bloquante nouvelle n’apparaît.
