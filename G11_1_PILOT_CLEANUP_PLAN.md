# G11.1 — Plan de nettoyage pilote BuildKit

**Statut final :** `TARGETING NOT GUARANTEED`  
**Exécution :** aucune suppression effectuée  
**Lot pilote autorisé :** aucun

## 1. Décision

Le lot pilote de 500 Mio à 1 Gio ne peut pas être constitué de manière suffisamment ciblée avec les informations et filtres disponibles sur le builder `default`.

Les 51 entrées mécaniquement anciennes/non partagées représentent environ 3,09 Gio, mais elles sont principalement attribuables par description à Superset, Node ou Python externe. Elles sont hors périmètre du Corpus Manager et potentiellement nécessaires à d’autres applications. Les supprimer serait une expansion de portée non autorisée.

**Aucun nettoyage pilote ne doit être exécuté.**

## 2. Commandes envisagées mais non exécutées

Les commandes suivantes sont conservées à titre de planification uniquement :

```bash
# Inventaire ciblé non destructif
docker buildx du --builder default --filter type=regular --format '{{json .}}'
docker buildx du --builder default --filter type=source.local --format '{{json .}}'

# Exemple de suppression future, NON EXÉCUTÉ
docker buildx prune --builder default --filter 'type=regular' --filter 'until=1344h'

# Exemple d’identifiant, NON EXÉCUTÉ et non recommandé sans preuve de propriété
docker buildx prune --builder default --filter 'id=<ID_APPROUVE>'
```

Le filtre `until=1344h` ne doit pas être présenté comme un dry-run : `buildx du` a renvoyé les 894 entrées avec ce filtre sur ce daemon, et `buildx prune` ne fournit pas de prévisualisation non destructive dans l’interface observée.

Les sélecteurs `shared`, `private` et `inuse` documentés par Docker n’ont pas fourni ici une sélection exploitable via `buildx du`. Leur effet réel sur une future suppression ne doit pas être déduit d’un test `du`.

## 3. Risques

- Perte de cache partagé avec d’autres applications hébergées.
- Reconstruction plus longue de production, développement ou rollback.
- Téléchargement réseau de couches Python, Node, PostgreSQL ou outillage.
- Cache supprimé alors que l’image actuelle reste présente : l’image et son cache de reconstruction sont deux objets distincts.
- Absence de traçabilité fiable par campagne avec le driver `docker`.
- Risque de suppression d’une couche appartenant à Superset ou à une autre application.

## 4. Procédure future si un lot devient nécessaire

Une future demande d’exécution devra au minimum :

1. Capturer `docker version`, `docker buildx version`, `docker buildx ls`, `docker system df -v`, `docker buildx du --format '{{json .}}'` et `df -h`.
2. Vérifier qu’aucun build, déploiement, migration ou rollback n’est en cours.
3. Vérifier les digests production, développement et rollback G8.5-R.
4. Vérifier les healthchecks et `/health`/`/ready` de production.
5. Obtenir une liste nominative avec propriétaire confirmé par les applications concernées.
6. Vérifier à nouveau `Reclaimable`, `Shared`, `Mutable`, `Type`, `UsageCount` et les dates.
7. Approuver explicitement la liste exacte, le builder et le filtre.
8. Exécuter un seul lot, sans `--all`, sans suppression d’image, volume, conteneur ou réseau.
9. Contrôler les services protégés et refaire les mesures `docker system df -v` et `df -h`.
10. Arrêter immédiatement à la moindre anomalie ou divergence d’inventaire.

## 5. Critères d’arrêt

Arrêt immédiat si :

- une entrée protégée ou d’un autre propriétaire apparaît dans le lot ;
- le nombre ou l’identité des entrées diffère de la liste approuvée ;
- `InUse` ou la propriété reste indéterminée ;
- production, développement ou rollback change d’état ;
- `/health` ou `/ready` échoue ;
- le gain réel ne peut pas être mesuré ;
- BuildKit retourne une erreur ou une sortie différente du périmètre validé.

## 6. Protections et interdictions

Ne pas modifier production, développement, rollback, images, volumes, réseaux, Traefik, CrowdSec, pare-feu, démon Docker ou sauvegardes. Ne pas utiliser `docker system prune`, `docker builder prune`, `docker buildx prune`, `docker image prune`, `docker volume prune` ou `docker compose down -v` dans G11.1.

## 7. Conclusion

La sélection d’un lot pilote nominatif et sûr n’est pas démontrée. La stratégie recommandée est de conserver le cache et de demander, si nécessaire, une coordination explicite avec le propriétaire de Superset/infra avant toute réduction.

**Statut : `TARGETING NOT GUARANTEED`. G11.2 non lancé.**
