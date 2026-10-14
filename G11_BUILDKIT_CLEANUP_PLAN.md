# G11 — Plan proposé de récupération du cache BuildKit

**Statut :** `PENDING APPROVAL`  
**Aucune commande de suppression n’a été exécutée.**

## 1. Principes

Le builder `default` est le seul builder accessible et utilise le driver `docker`. Son cache est partagé entre production, développement, rollback et environnements de validation. Le plan ne propose aucune suppression d’image, de volume, de conteneur ou de réseau.

Les commandes ci-dessous sont des commandes proposées, à exécuter uniquement après validation opérateur et après un nouveau contrôle des builds planifiés.

## 2. Ordre recommandé

### Étape 0 — Précontrôles obligatoires

Capturer l’état puis vérifier :

```bash
docker system df -v
docker buildx ls
docker buildx du --builder default --verbose
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
docker image ls --digests
df -h /
curl -fsS https://corpus-moore.bencoherolab.com/health
curl -fsS https://corpus-moore.bencoherolab.com/ready
```

Arrêter le plan si la production, le développement, le rollback ou un build de validation est en cours, si un healthcheck échoue, ou si le nombre/l’identité des images protégées diffère de l’état audité.

### Étape 1 — Observation ciblée

Répéter l’inventaire avec des filtres Buildx, sans suppression :

```bash
docker buildx du --builder default --filter type=regular --format '{{json .}}'
docker buildx du --builder default --filter type=source.local --format '{{json .}}'
```

Documenter les entrées dont `Shared=true`, `LastUsedAt` est récent, ou dont le propriétaire ne peut pas être relié à un build terminé. Cette étape doit produire une liste nominative avant toute action.

### Étape 2 — Premier lot conservateur

Après validation de la liste nominative, cibler uniquement les entrées régulières non partagées, anciennes et sans build planifié. Le filtre d’âge doit être choisi par l’opérateur après confirmation de la politique de conservation ; une valeur prudente serait au moins 8 semaines.

Commande proposée, non exécutée :

```bash
docker buildx prune --builder default --filter 'until=1344h'
```

Cette commande reste potentiellement destructive pour le cache. Elle ne doit être lancée qu’avec confirmation interactive, sans `--all`, sans `--force`, et après revue de la sortie proposée par le client. Le filtre d’âge n’exprime pas à lui seul l’absence de dépendance projet ; les entrées partagées et actives doivent être exclues par le moteur et contrôlées avant/après.

Gain logique maximal indicatif : jusqu’à environ **5,65 Gio** pour l’ensemble ancien/non partagé observé, sans garantie de récupération réelle. Le gain réel peut être inférieur à cause des couches partagées, des métadonnées et du stockage overlayfs.

### Étape 3 — Lots ultérieurs

Ne considérer un second lot qu’après un cycle complet de validation et une période d’observation. Si l’espace disque devient réellement critique, préférer un seuil de conservation explicite :

```bash
docker buildx prune --builder default --max-used-space 8GB --reserved-space 4GB
```

Cette commande est une proposition de politique, pas une recommandation immédiate. Elle ne doit pas être utilisée avant d’avoir identifié les builds attendus et vérifié que les valeurs sont compatibles avec les besoins de reconstruction production/dev/rollback. Ne pas combiner avec `--all` ou `--force` sans approbation distincte.

## 3. Conséquences attendues

| Action | Gain possible | Effet sur les builds | Risque |
|---|---:|---|---|
| Conserver le cache | 0 Gio | temps de build minimal | consommation disque inchangée |
| Supprimer un lot ancien/non partagé | jusqu’à ~5,65 Gio logiques observés | re-téléchargement et recompilation de dépendances | attribution imparfaite avec le driver `docker` |
| Réduire par seuil d’espace | variable | prochains builds plus longs | suppression de couches utiles mais non récentes |
| Suppression globale `--all` | non évaluée | pertes maximales de cache | interdite dans ce ticket |

L’espace réellement libéré ne doit être mesuré qu’avec `df -h /` avant/après. La taille logique des entrées BuildKit ne doit pas être présentée comme un gain disque.

## 4. Contrôles après chaque lot

Exécuter immédiatement :

```bash
docker system df -v
docker buildx du --builder default --verbose
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
docker inspect --format '{{.Name}} {{.State.Status}} {{.State.Health.Status}}' \
  mobile_money_corpus_manager_v0_1-app-1 \
  mobile_money_corpus_manager_v0_1-db-1 \
  mobile_money_corpus_manager_v0_1-minio-1 \
  mobile_money_corpus_manager_dev-app-1 \
  mobile_money_corpus_manager_dev-db-1 \
  mobile_money_corpus_manager_dev-minio-1
df -h /
curl -fsS https://corpus-moore.bencoherolab.com/health
curl -fsS https://corpus-moore.bencoherolab.com/ready
```

Contrôler aussi :

- l’image et le conteneur rollback G8.5-R sont toujours présents et inchangés ;
- les digests production/dev/rollback sont identiques à l’instantané préopération ;
- les conteneurs protégés n’ont pas redémarré ;
- les volumes de production et de développement sont inchangés ;
- Traefik, CrowdSec et les autres services n’ont pas d’erreur nouvelle ;
- aucun build ou déploiement n’a commencé de manière concurrente ;
- les sauvegardes de production restent présentes.

## 5. Conditions d’arrêt immédiat

Arrêter le plan, ne pas lancer de lot suivant et conserver les résultats si :

- `/health` ou `/ready` n’est pas HTTP 200 ;
- un service protégé devient unhealthy ou redémarre ;
- un digest protégé change ;
- une entrée partagée ou récente est incluse contre toute attente ;
- un build, une migration ou un rollback est détecté en cours ;
- l’écart entre `docker system df` et `docker buildx du` augmente sans explication ;
- l’espace réellement libéré ne correspond pas aux mesures attendues ;
- une erreur Docker/BuildKit apparaît.

## 6. Interdictions

Ne pas exécuter :

```text
docker system prune
docker system prune -a
docker system prune --volumes
docker builder prune --all
docker buildx prune --all
docker volume prune
docker compose down -v
```

Ne pas supprimer directement sous `/var/lib/docker`, ne pas supprimer d’image ou de volume pour récupérer l’espace du cache, ne pas redémarrer le démon Docker et ne pas modifier Traefik, le pare-feu ou les réseaux.

## 7. Décision proposée

Le nettoyage n’est pas autorisé par ce ticket. Le premier lot acceptable, sous nouvelle approbation explicite, est un lot BuildKit ciblé par builder `default`, ancienneté documentée d’au moins 8 semaines, sans partage connu et après vérification des builds planifiés. Le gain doit être annoncé comme une estimation jusqu’à la mesure `df -h` post-opération.

**Résultat : plan préparé, aucune suppression exécutée, en attente de validation opérateur.**
