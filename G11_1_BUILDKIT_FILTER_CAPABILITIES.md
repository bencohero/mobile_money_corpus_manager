# G11.1 — Capacités de filtrage BuildKit

**Serveur :** `vmi3474447`  
**Date :** 2026-10-14  
**Statut :** `TARGETING NOT GUARANTEED`  
**Suppression exécutée :** aucune

## 1. Versions et périmètre vérifiés

| Composant | Version / état |
|---|---|
| Docker Engine | 29.7.0 |
| API Docker | 1.55 |
| Buildx | v0.36.0 (`df28b0a0b6a44453a87bd53c438432f4120962c`) |
| Builder | `default` |
| Driver | `docker` |
| BuildKit | v0.32.0 |
| Nœud | `default`, running |
| Plateforme | `linux/amd64 (+3)` |

Commandes de contrôle exécutées uniquement en lecture :

```text
docker version
docker buildx version
docker buildx ls
docker buildx du --help
docker buildx prune --help
docker system df -v
docker buildx du --format '{{json .}}'
```

Conformément au ticket, `docker buildx prune`, `docker builder prune`, `docker system prune`, `docker image prune` et `docker volume prune` n’ont pas été exécutés.

## 2. Filtres documentés

La documentation Docker actuelle décrit pour `buildx prune` des sélecteurs `until`, `id`, `parents`, `description`, `inuse`, `mutable`, `immutable`, `shared`, `private` et `type`, avec des sélecteurs combinés par AND. Les types documentés incluent `regular`, `source.local`, `source.git.checkout`, `exec.cachemount`, `internal` et `frontend`.

Références :

- [Docker buildx prune](https://docs.docker.com/reference/cli/docker/buildx/prune/)
- [Docker buildx du](https://docs.docker.com/reference/cli/docker/buildx/du/)

La documentation indique que `until=24h` conserve les entrées utilisées pendant les dernières 24 heures et cible les entrées plus anciennes. Elle décrit également `RECLAIMABLE=false` comme une entrée que le prune ne supprimera pas, même avec `--all`.

Ces garanties documentaires n’ont pas été testées par une suppression et ne valent pas comme preuve de sélection nominative sur ce daemon précis.

## 3. Résultat local des filtres `buildx du`

`docker buildx du --format '{{json .}}'` expose les champs :

```text
CreatedAt, Description, ID, LastUsedAt, Mutable, Parents,
Reclaimable, Shared, Size, Type, UsageCount
```

Le champ `InUse` n’est pas présent dans les 894 objets JSON observés. `UsageCount` est un compteur historique et ne prouve pas qu’une entrée est actuellement inutilisée.

Tests non destructifs effectués :

| Filtre testé avec `buildx du` | Résultat local |
|---|---|
| `type=regular` | 857 entrées ; filtre effectivement discriminant |
| `type=source.local` | 37 entrées ; filtre effectivement discriminant |
| `until=1344h` | 894 entrées ; aucune réduction observée |
| `shared=true` | 0 entrée, malgré 88 objets marqués `Shared=true` dans l’inventaire complet |
| `shared=false` | 0 entrée |
| `inuse=true` | erreur de format : le client local exige `name=value` |
| `inuse=false` | 0 entrée |
| `inuse!=true` | 894 entrées ; aucune sélection utile |
| `mutable=true` / `mutable=false` | 0 entrée |
| `private` | erreur de format : le client local exige `name=value` |

Le filtre `type=regular` fonctionne. Les filtres booléens et temporels ne fournissent pas ici un aperçu fiable de l’ensemble correspondant à la suppression. Le fait qu’un filtre soit accepté syntaxiquement ne démontre pas qu’il soit appliqué par le daemon comme attendu.

## 4. Différences de sémantique

- `Reclaimable=true` signifie que BuildKit considère l’objet récupérable ; cela ne fournit pas son propriétaire applicatif.
- `Shared=true` indique un partage avec une autre ressource, souvent une image ou une autre référence. Un objet partagé ne doit pas être ciblé sans analyse de tous les consommateurs.
- `Reclaimable=false` a été observé sur une entrée `source.local` de 823,3 kB, avec `UsageCount=0` et sans `LastUsedAt`. Elle est protégée.
- `InUse` n’est pas exposé par le JSON local ; l’absence de ce champ interdit de prouver le critère « pas utilisée ».
- Les dates `LastUsedAt` sont renvoyées sous forme relative (`19 hours ago`, `7 weeks ago`, `2 months ago`), non comme horodatage exact. La frontière « au moins huit semaines » ne peut donc pas être prouvée pour chaque entrée à partir de ce champ.
- `docker buildx du` n’est pas un mécanisme de prévisualisation de la suppression : le client local n’a pas fourni de dry-run pour `buildx prune`, et aucun prune n’a été lancé.
- Il n’existe pas de commande autorisée ici permettant de supprimer une entrée précise par ID. La documentation mentionne un sélecteur `id` pour prune, mais son comportement n’a pas été testé et ne peut pas être utilisé comme autorisation.

## 5. Conclusion de précision

La sélection catégorie B exige simultanément `regular`, `Reclaimable=true`, non partagé, non utilisé et dernière utilisation d’au moins huit semaines. Localement :

1. le statut `InUse` manque ;
2. les filtres `shared`/`inuse` ne produisent pas de sélection fiable avec `du` ;
3. le filtre `until=1344h` renvoie l’ensemble complet avec `du` ;
4. les entrées anciennes visibles sont attribuées à plusieurs applications, notamment Superset ;
5. aucune prévisualisation non destructive de `prune` n’est disponible.

La correspondance exacte entre les candidats et une future suppression ne peut donc pas être démontrée.

**Décision G11.1 : `TARGETING NOT GUARANTEED`.**
