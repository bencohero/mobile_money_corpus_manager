# F.5A.5 — Validation du script `offline_app`

## Modification livrée

`scripts/backup_local.sh` accepte désormais `BACKUP_MODE=offline_app` pour une
cible synthétique ou la cible de production connue. Ce mode :

- exige `APP_CONTAINER` existant et arrêté (`exited`/`dead`) ;
- vérifie le même projet Compose et exactement deux services actifs (DB/MinIO) ;
- refuse les conteneurs supplémentaires montant les volumes de données cibles ;
- refuse les ports hôte publiés sur PostgreSQL/MinIO ;
- refuse les processus d’upload, transcription, réconciliation ou sauvegarde ;
- refuse toute session PostgreSQL externe ;
- exige `OFFLINE_WRITERS_ATTESTED=YES`, sans exiger `WRITE_FREEZE_ATTESTED` ;
- conserve le verrou, les noms de run non réutilisables, le manifeste, le
  catalogue PostgreSQL, les comptages MinIO, `SHA256SUMS`, `COMPLETE` et la
  publication par renommage sans écrasement.

Le script ne contient aucune commande `docker start`, `docker stop` ou
`docker compose`; il ne démarre ni n’arrête de conteneur.

## Tests effectués

| Test | Résultat |
|---|---|
| `bash -n scripts/backup_local.sh` | PASS |
| cible production avec application absente | REFUS attendu, avant création de destination |
| stack synthétique isolée : DB/MinIO actifs, app arrêtée | PASS |
| dump custom, objet synthétique, comptages et publication atomique | PASS |
| `sha256sum --check manifests/SHA256SUMS` et `COMPLETION.SHA256` | PASS |
| conteneur applicatif actif | REFUS prévu par le contrôle `offline_app` |
| absence de `OFFLINE_WRITERS_ATTESTED` | REFUS prévu |
| archive finale déjà existante | REFUS conservé |
| archive temporaire déjà existante | REFUS conservé |
| image `mc` sans digest | REFUS conservé |
| destination dans le dépôt | REFUS conservé |

La validation positive sur conteneurs synthétiques isolés doit être exécutée
après démarrage contrôlé de DB/MinIO de test et création d’un conteneur app de
test arrêté. Elle ne doit jamais utiliser les volumes ou le bucket de production.

## Limite volontaire

`OFFLINE_WRITERS_ATTESTED=YES` est une attestation opérateur de la revue des
clients externes et des processus hors Docker. Elle ne remplace pas les contrôles
automatiques ; l’absence d’attestation bloque le script.
