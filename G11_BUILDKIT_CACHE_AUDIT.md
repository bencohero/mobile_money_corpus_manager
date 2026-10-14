# G11 — Audit du cache Docker BuildKit

**Serveur :** `vmi3474447`  
**Date de l’audit :** 2026-10-14  
**Statut :** `AUDIT COMPLETE / PENDING APPROVAL`  
**Portée :** lecture seule ; aucune suppression, aucun redémarrage et aucune modification de configuration.

## 1. Résumé exécutif

Un seul builder BuildKit est accessible : `default`, driver `docker`, nœud `default`, état `running`, BuildKit `v0.32.0`, plateforme `linux/amd64 (+3)`. Il utilise le stockage du démon Docker sous `/var/lib/docker` avec le driver `overlayfs`.

Le cache BuildKit représente **15,58 Gio logiques** selon `docker system df`. La même commande estime **10,61 Gio récupérables**, mais cette valeur est une estimation Docker et ne constitue pas un espace disque garanti. Les couches peuvent être partagées avec des reconstructions ou des images encore nécessaires.

L’audit ne permet pas d’attribuer chaque entrée de cache à un projet : le driver `docker` expose des identifiants de cache BuildKit, mais pas un propriétaire Compose fiable pour chaque entrée. Les caches récents, partagés ou liés aux builds de production, développement, rollback ou validation sont donc conservés ou classés à investiguer.

## 2. Inventaire Docker et disque

Commandes exécutées en lecture seule :

```text
docker system df -v
docker buildx ls
docker buildx du --verbose
docker info
df -h
du -x -h -d 2 /var/lib/docker
```

État observé :

| Ressource | Total | Actif | Taille logique | Récupérable annoncé |
|---|---:|---:|---:|---:|
| Images | 56 | 15 | 16,26 Gio | 9,89 Gio |
| Conteneurs | 17 | 16 | 31,54 Mio | 393,2 Kio |
| Volumes locaux | 40 | 8 | 1,288 Gio | 836,3 Mio |
| Cache BuildKit | 894 entrées | 1 | 15,58 Gio | 10,61 Gio |

État du système de fichiers :

| Montage | Taille | Utilisé | Disponible | Utilisation |
|---|---:|---:|---:|---:|
| `/` | 193 Gio | 108 Gio | 86 Gio | 56 % |

Le `du` direct de `/var/lib/docker` a été refusé par les permissions du compte opérateur. Aucune élévation de privilèges n’a été demandée ; les mesures Docker ci-dessus sont donc la référence disponible pour cet audit.

## 3. Détail BuildKit

`docker buildx du --format '{{json .}}'` a retourné 894 entrées :

| Type | Entrées | Taille calculée à partir des entrées |
|---|---:|---:|
| `regular` | 857 | incluse dans le total |
| `source.local` | 37 | environ 9,2 Mio |
| Total | 894 | environ 14,51 Gio en conversion décimale des entrées |

La différence entre les 14,51 Gio calculés à partir des entrées JSON et les 15,58 Gio de `docker system df` provient de conventions d’agrégation et d’unités du moteur. La valeur de référence opérationnelle reste celle affichée par Docker, avec cette réserve.

Constats :

- 893 entrées sont marquées `Reclaimable=true` par Buildx, mais ce marqueur ne prouve pas qu’elles sont sans conséquence pour les prochains builds.
- 88 entrées sont marquées `Shared=true`, pour environ 4,62 Gio calculés. Elles ne doivent pas être ciblées isolément sans connaître les consommateurs.
- Les entrées `source.local` sont mutables et correspondent aux contextes locaux ou Dockerfiles ; elles sont petites mais certaines ont été utilisées récemment.
- Environ 157 entrées ont une dernière utilisation dans les dernières 24 heures ; environ 197 ont une dernière utilisation indiquée à 5 semaines, 6 semaines, 7 semaines ou 2 mois.
- Les plus grosses entrées observées comprennent environ 1,17 Gio, 708,8 Mio, 632,2 Mio, 493,5 Mio, 482,7 Mio et 400,5 Mio. Leur provenance projet n’est pas exposée par l’inventaire Buildx.
- Le calcul conservateur des entrées anciennes et non partagées atteint environ 5,65 Gio logiques. Il s’agit d’un plafond de travail, pas d’un gain garanti ni d’une autorisation de suppression.

## 4. Builders et dépendances

### Builder accessible

| Builder | Driver | Nœud | État | Version BuildKit |
|---|---|---|---|---|
| `default` | `docker` | `default` | running | v0.32.0 |

Aucun builder `docker-container` distinct n’a été exposé par `docker buildx ls`. Il n’existe donc pas de cache BuildKit isolable par builder secondaire dans l’état observé.

### Production

La production construit l’image applicative depuis `Dockerfile`, cible `runtime`, avec `docker-compose.yml`. L’overlay `docker-compose.release.yml` peut désactiver le build et pinner l’image release par digest. Les images et couches de production sont protégées, notamment :

- `mobile-money-corpus:2698530f7a77a6d9222049c0d911f49fb56c36ae` ;
- image applicative utilisée par `mobile_money_corpus_manager_v0_1-app-1` ;
- `postgres:16-alpine` et MinIO daté utilisés par la production.

### Développement

Le développement utilise également `Dockerfile`, cible `runtime`, avec son projet Compose et ses volumes propres. Les caches récents peuvent être nécessaires à un prochain `docker compose build` de développement et sont protégés par principe.

### Rollback G8.5-R

Le rollback utilise l’image déjà construite `mobile_money_corpus_manager_g8_5_r:8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`, conteneur arrêté mais conservé. Son image et les couches potentiellement partagées ne doivent pas être invalidées par un nettoyage non attribué.

### Migration et validation

Les fichiers `docker-compose.test.yml`, `docker-compose.preprod.yml`, `docker-compose.c1.test.yml`, `docker-compose.c1b.test.yml`, `docker-compose.e2-migration.yml` et `Dockerfile.tools` construisent ou réutilisent des images de test, de migration, de restauration et d’outillage. Les campagnes historiques ont été nettoyées, mais plusieurs images et volumes hors périmètre G10 restent présents. Le cache ne contient pas de label fiable permettant de séparer automatiquement ces campagnes.

Les targets `runtime` et `test` partagent la base `python:3.12-slim` et les étapes d’installation de `requirements.txt`. `Dockerfile.tools` partage également des couches PostgreSQL/MinIO Client. Une suppression du cache peut donc augmenter le temps de reconstruction et les téléchargements pour plusieurs usages à la fois.

## 5. Classification

### À CONSERVER

- Les caches utilisés dans les dernières 24–72 heures, notamment ceux liés aux images production, développement, release et aux validations récentes.
- Les entrées `Shared=true` jusqu’à identification de tous les consommateurs.
- Les couches de base partagées (`python:3.12-slim`, PostgreSQL, MinIO Client) nécessaires à plusieurs Dockerfiles.
- Les entrées `source.local` récentes et les caches dont la dernière utilisation est inconnue.
- Les images, volumes et conteneurs eux-mêmes : cet audit porte uniquement sur le cache et n’autorise pas leur suppression.

### CANDIDAT À SUPPRESSION — sous réserve d’approbation ultérieure

Les entrées `regular`, non partagées, sans usage récent, dont la dernière utilisation est documentée à au moins 8 semaines et dont aucun build planifié ne dépend. L’ordre de grandeur observable est inférieur ou égal à environ 5,65 Gio logiques pour l’ensemble ancien/non partagé, mais aucune entrée nominative n’est approuvée par ce rapport.

### À INVESTIGUER

- Toute entrée partagée ou récente sans propriétaire de projet.
- Les gros caches avec dernière utilisation de 2 à 8 semaines.
- Les caches issus des validations G9/G10, des images de migration et de `Dockerfile.tools`.
- Les caches associés à des images historiques encore conservées pour rollback, validation ou décision opérateur.
- L’écart entre l’agrégation Buildx JSON et `docker system df`.

## 6. Protections vérifiées

L’inventaire confirme la présence des conteneurs et images de production, développement et rollback. Aucun conteneur n’a été arrêté, aucune image, volume, réseau ou configuration n’a été modifié. Le répertoire de sauvegardes `/home/sangouman/mobile-money-corpus-backups/` n’a pas été lu récursivement ni modifié.

Traefik, CrowdSec, les autres applications, le pare-feu et le démon Docker n’ont pas été modifiés ou redémarrés.

## 7. Conclusion d’audit

Le cache BuildKit est important mais partiellement réutilisé : **15,58 Gio logiques**, avec **10,61 Gio annoncés récupérables**, ne peuvent pas être assimilés à un gain disque certain. L’attribution par campagne est insuffisante avec le builder `docker` actuel. Toute action doit donc être progressive, filtrée par ancienneté et accompagnée d’un contrôle de santé et d’une nouvelle mesure `docker system df -v`.

**Résultat : G11 AUDIT COMPLETE / PENDING APPROVAL.**
