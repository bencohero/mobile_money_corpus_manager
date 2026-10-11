# Plan de remédiation sécurité VPS — F.3

Date : 2026-10-11  
Statut : **PRÊT POUR AUTORISATION**  
Périmètre : préparation uniquement. Aucun port, pare-feu, conteneur, volume ou
configuration de production n’a été modifié.

## 1. Constats vérifiés

### PostgreSQL publié

La publication publique de PostgreSQL provient du projet Compose `postgres`, et
non du Compose applicatif de production :

| Élément | Valeur observée |
|---|---|
| Fichier | `/home/sangouman/apps/postgres/docker-compose.yml` |
| Projet | `postgres` |
| Conteneur | `postgres` (`postgres:18`) |
| Publication | `0.0.0.0:5432->5432/tcp` et `[::]:5432->5432/tcp` |
| Réseau | `infra-network` |
| Dépendant | `pgadmin`, même fichier et même réseau |
| Production applicative | `mobile_money_corpus_manager_v0_1-db-1`, pas de `ports`, réseau backend interne |

Le service de production utilise PostgreSQL interne via l’alias Docker
`mobile-money-corpus-db` et le port 5432 du réseau Docker. Il ne dépend pas du
conteneur hôte `postgres`. Les tests, le développement et Superset ont aussi des
bases séparées. Cette séparation doit être confirmée par inspection des chaînes de
connexion avant toute modification.

### Traefik

| Élément | Valeur observée |
|---|---|
| Compose | `/home/sangouman/docker-compose/traefik/docker-compose.yml` |
| Configuration dynamique/statique | `/home/sangouman/docker-compose/traefik/traefik.yml` |
| Conteneur | `traefik` (`traefik:v3.7`) |
| Configuration | `api: insecure: true`, `dashboard: true` |
| Publication | `0.0.0.0:8090->8080/tcp` et IPv6, en plus de 80/443 |
| Dépendances | réseau externe `frontend`, socket Docker en lecture seule, ACME, fichier `config.yml`, CrowdSec plugin |
| Routes corpus | labels sur `app` de `docker-compose.yml`, hôte `corpus-moore.bencoherolab.com`, backend port 8000 |

La dépendance au dashboard n’est pas démontrée comme nécessaire au trafic
applicatif. Elle doit être recherchée dans les procédures, sondes, scripts et
utilisateurs avant désactivation. Aucun accès administratif de remplacement ne doit
être ouvert automatiquement.

## 2. Configuration cible proposée

### PostgreSQL

Cible préférée : supprimer la publication de `postgres` et conserver l’accès
administratif par un tunnel SSH approuvé vers une adresse d’écoute privée, ou par un
réseau privé/VPN explicitement autorisé. Si une publication temporaire est
indispensable, la limiter à une adresse de management privée approuvée, jamais à
`0.0.0.0` ou `::`.

Avant décision : cartographier les clients de `postgres` et `pgadmin`, vérifier les
règles `pg_hba.conf`, les interfaces d’écoute et l’absence de secret partagé avec la
production. Le conteneur de production ne doit pas être reconfiguré dans cette
étape.

### Traefik

Cible proposée : `api.insecure: false` ou suppression explicite de l’option, puis
suppression de la publication `8090:8080`. Le dashboard, s’il est requis, doit être
servi par une configuration sécurisée dédiée : route HTTPS interne, authentification
forte, middleware de restriction réseau et journalisation. Un tunnel SSH vers une
interface locale est préférable à une nouvelle exposition publique.

Les routes 80/443, ACME, le provider Docker, le réseau `frontend` et les labels de
l’application doivent rester inchangés fonctionnellement. La configuration cible
doit être testée avec `docker compose config` et avec une validation Traefik hors
production avant approbation.

## 3. Tests avant/après et retour arrière

Capturer avant changement, sans secret ni contenu métier : liste des projets,
conteneurs, ports, réseaux, volumes, `curl`/sondes `/health` et `/ready`, route HTTPS
du corpus, état ACME et logs Traefik. Tester aussi l’accès administratif approuvé à
PostgreSQL et, si retenu, au dashboard.

Après changement autorisé : vérifier que 5432 et 8090 ne sont plus publiés comme
avant, que `80/443` et le domaine corpus répondent, que les certificats se
renouvellent, que `/health` et `/ready` restent sains et que l’application peut
accéder à sa base et à MinIO. Contrôler l’absence de nouveau montage ou réseau sur
les conteneurs applicatifs.

Retour arrière : conserver les fichiers précédents et leur empreinte, restaurer la
configuration validée précédente uniquement après constat documenté, puis relancer
les contrôles de santé et d’exposition. Le retour arrière ne doit pas toucher aux
volumes applicatifs ni aux données. Si la restauration de Traefik échoue, maintenir
les ports critiques fermés et appliquer le plan d’incident de l’exploitation plutôt
que réouvrir durablement l’exposition.

## 4. Autorisations et critères d’arrêt

Autorisation écrite requise de l’exploitation et de la sécurité pour modifier les
Compose Traefik/PostgreSQL, les ports, le pare-feu, les règles `pg_hba.conf`, les
certificats ou redémarrer un service. Le propriétaire du corpus doit valider la
continuité applicative.

Arrêt immédiat si une ressource de production change, si une route HTTPS ou la
readiness échoue, si un client non identifié est découvert, si un secret est exposé,
ou si un accès d’administration de remplacement n’est pas prouvé.

## Décision

Le plan est **PRÊT POUR AUTORISATION**. Les corrections restent interdites dans ce
ticket.
