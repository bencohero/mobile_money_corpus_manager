# G8.1 — Nouvelle sauvegarde

## Statut

`BLOCKED` — aucune nouvelle archive de production n’a été publiée dans cette session.

## Préconditions restantes

1. Fournir une preuve opérateur courante que les écritures de production sont `FROZEN` et que `active_writes=0`.
2. Fournir une destination hors dépôt, explicitement approuvée, sans écraser d’archive existante.
3. Exécuter le script versionné corrigé avec l’identifiant UTC unique.
4. Vérifier `pg_restore --list`, le comptage des objets MinIO, `MANIFEST.json`, `manifests/SHA256SUMS`, `COMPLETE` et `COMPLETION.SHA256`.
5. Communiquer le chemin exact à l’opérateur, puis s’arrêter pour le transfert Kubuntu.

Identifiant d’archive : **NON PRODUIT**  
Chemin d’archive : **NON PRODUIT**

Le prévol a observé PostgreSQL et MinIO de production actifs, mais cette observation ne constitue pas un gel applicatif. Restic n’a pas été demandé ni installé sur le VPS.
