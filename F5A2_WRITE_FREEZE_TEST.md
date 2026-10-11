# F.5A.2 — Test du gel d’écriture

## Mécanisme préparé

`app/write_freeze.py` fournit un état partagé et sans donnée métier : `OPEN → DRAINING → FROZEN → OPEN`.

Le middleware compte les requêtes HTTP mutantes (`POST`, `PUT`, `PATCH`, `DELETE`) avant leur entrée dans l’application. En `DRAINING`, les nouvelles écritures reçoivent `503` avec `Retry-After`; les requêtes déjà comptées peuvent terminer. Le contrôleur attend `active_writes=0`, passe à `FROZEN`, puis maintient cet état pendant les deux captures. Le fichier d’état est verrouillé par `flock` et écrit atomiquement.

```bash
docker exec APP python -m app.write_freeze status
docker exec APP python -m app.write_freeze freeze --timeout 120
# PostgreSQL puis MinIO sont capturés pendant FROZEN.
docker exec APP python -m app.write_freeze unfreeze
```

Le délai de drain doit expirer si un upload reste bloqué ; il ne faut jamais forcer `FROZEN` dans ce cas.

## Tests exécutés

- Requête concurrente active : `active_writes=1`, passage en `DRAINING`, attente de sa fin, puis `FROZEN`.
- Nouvelle écriture pendant `FROZEN` : refusée.
- Reprise : `unfreeze` revient à `OPEN` avec compteur nul.
- Upload interrompu simulé par une requête active maintenue : `freeze --timeout .2` échoue, laisse l’état `DRAINING`, puis un second gel réussit après libération de la requête.

## Limite déterminante

Ces tests valident le composant préparé dans le dépôt, pas l’image actuellement déployée. Contrôle effectué : `/app/app/write_freeze.py` est absent du conteneur de production. Le gel réel reste donc **BLOQUÉ** jusqu’à ce que l’image active embarque le middleware et que tous les chemins d’écriture passent par lui.

## Chemins concernés

Le code réellement observé dans l’image expose l’inscription participant, création administrative, upload audio, soumission idempotente, transcription, vérification, suppression, codes d’atelier et audit. Aucun worker asynchrone séparé n’a été observé. Le garde doit rester au niveau du middleware pour couvrir ces routes sans dépendre d’une liste partielle.

## Impact utilisateur attendu après déploiement

- pendant le drain : les requêtes déjà engagées terminent ; les nouvelles écritures reçoivent temporairement `503` ;
- pendant les captures : lecture et liveness peuvent rester accessibles, mais toutes les écritures sont refusées ;
- reprise : retour à `OPEN` après contrôles SHA-256, comptages et réconciliation ;
- une fenêtre cible de 2 à 5 minutes est plausible pour l’empreinte observée, mais la valeur autorisée doit être mesurée avec `pg_dump`, miroir MinIO et marge de drain.
