# G8 — Décision finale

Date : 2026-10-13

## Décision

**`BLOCKED`**

## Justification

Le déploiement contrôlé est arrêté avant migration conformément au point d’arrêt obligatoire :

1. la sauvegarde immédiate locale est cohérente et vérifiée ;
2. aucune copie indépendante sur Kubuntu n’est disponible ou attestée ;
3. `restic` n’est pas disponible pour prouver la récupérabilité externe ;
4. le script versionné de sauvegarde a révélé un défaut de quoting, corrigé seulement dans une copie temporaire hors dépôt ;
5. la migration, le démarrage applicatif et la recette production n’ont donc pas été exécutés.

## État de production

- Release Git : inchangée à `889fd5b018f038d6166d8ef0afa976426392fa79`.
- PostgreSQL : `0005_workshop_attribution`.
- PostgreSQL et MinIO : conteneurs sains, inchangés.
- Application : arrêtée/absente.
- Volumes et données historiques : non modifiés.
- Aucun push, déploiement public, migration, redémarrage applicatif ou ouverture publique.

## Conditions de reprise

Corriger et revalider le script de sauvegarde versionné, produire une nouvelle sauvegarde immédiate avec le mécanisme corrigé, la transférer sur Kubuntu, vérifier ses manifestes et sa restauration via restic, puis reprendre la migration explicite `0005 → 0008`. Tant que ces preuves ne sont pas jointes, la décision reste `BLOCKED`.
