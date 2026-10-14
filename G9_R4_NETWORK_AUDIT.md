# G9-R4 — Audit réseau

Date de l’audit : 2026-10-13 12:43 CEST  
Hôte observé : `vmi3474447` — IPv4 `169.58.99.71`  
Compte : `sangouman`, membre du groupe Docker, non-root

## Résultat

Le dashboard/API Traefik est toujours publiquement exposé sur TCP `8090`.
L’exposition provient du conteneur `traefik`, publication Docker
`0.0.0.0:8090->8080/tcp` et `[::]:8090->8080/tcp`. La configuration Traefik
active contient `api.insecure: true` et `dashboard: true`.

| Contrôle | Résultat | Preuve |
|---|---|---|
| Ports écoutés | `22`, `80`, `443`, `5432`, `8090` en IPv4 et IPv6 | `ss -lntp` |
| Dashboard local | PASS de reproduction du défaut | `http://127.0.0.1:8090/dashboard/` → HTTP 200 |
| API locale | PASS de reproduction du défaut | `/api/http/routers` → HTTP 200 |
| Dashboard via IP publique depuis le VPS | PASS de reproduction du défaut | `http://169.58.99.71:8090/...` → HTTP 200 |
| Application HTTPS | PASS | `/health` 200, `/ready` 200, `/login` 200 |
| SSH | PASS local | `127.0.0.1:22` ouvert |
| App Docker | PASS | conteneur healthy, aucun port hôte publié |
| PostgreSQL Corpus | PASS d’isolement | `db-1` sans port hôte publié |

## Pare-feu et Contabo

La lecture privilégiée de `ufw status verbose`, `nft list ruleset`,
`iptables -S` et `ip6tables -S` n’a pas été possible : le compte courant ne
dispose pas d’un `sudo` non interactif et les commandes retournent
« must be root ». L’état effectif du pare-feu hôte reste donc **NON PROUVÉ**.

Aucun accès API ou console Contabo n’est connecté dans cet environnement.
L’existence d’une règle de pare-feu Contabo autorisant ou refusant `8090` est
donc **NON PROUVÉE**. Le fait que le port réponde sur l’IP publique depuis le
VPS démontre au minimum qu’aucun contrôle local observé ne le bloque sur ce
chemin.

## Docker et dépendances

- Projet Traefik : `/home/sangouman/docker-compose/traefik`.
- Conteneur : `traefik`, image `traefik:v3.7`, réseau `frontend` (`172.22.0.0/16`).
- Processus d’exposition : deux `docker-proxy`, IPv4 et IPv6, vers
  `172.22.0.6:8080`.
- L’application `mobile_money_corpus_manager_v0_1-app-1` utilise Traefik via
  les labels `websecure` et l’hôte `corpus-moore.bencoherolab.com`; elle ne
  publie pas de port hôte.
- La recherche opérationnelle ne trouve pas de sonde, script ou dépendance
  applicative au port `8090`. Le dashboard peut toutefois être utilisé par un
  opérateur humain; son accès de remplacement doit être prévu avant fermeture.

## Limites

Le test vers l’IP publique a été exécuté depuis le VPS lui-même; il ne constitue
pas une mesure depuis un réseau indépendant. Le contrôle externe indépendant,
la lecture root des pare-feu et la vérification du pare-feu Contabo restent à
faire avant décision finale.

Conclusion d’audit : **PUBLIC_OPEN_NO_GO — exposition confirmée**.
