# G9.1-R — Preuve de sauvegarde

Aucune sauvegarde réelle n’a été produite. Ce document décrit la preuve à
collecter après autorisation; les champs restent à compléter par l’opérateur.

Le précontrôle a toutefois établi deux écarts bloquants avant gel : le chemin
`/var/backups/mobile-money-corpus` n’existe pas sur l’hôte courant et la
destination de rapatriement Kubuntu n’est pas identifiée. Aucun répertoire de
backup n’a été créé pour contourner ces écarts.

## Procédure

1. Capturer inventaire PostgreSQL/MinIO et release/Alembic.
2. Vérifier app.write_freeze status, puis freeze avec timeout contrôlé.
3. Prouver FROZEN et active_writes=0.
4. Exécuter scripts/backup_local.sh avec les conteneurs exacts, le bucket exact
   et l’image mc épinglée.
5. Vérifier COMPLETE, MANIFEST.json schema 2, COMPLETION.SHA256,
   manifests/SHA256SUMS, pg_restore --list et les comptages MinIO.
6. Conserver sans écrasement le répertoire final et ses journaux.

Commande après autorisation, avec les variables déjà vérifiées par le
précontrôle :

~~~bash
BACKUP_ROOT="$BACKUP_ROOT" BACKUP_MODE=production \
BACKUP_TARGET_ID=mobile_money_corpus_manager_v0_1 \
PG_CONTAINER="$DB" MINIO_CONTAINER="$MINIO" MINIO_BUCKET=mobile-money-corpus \
MINIO_MC_IMAGE='quay.io/minio/aistor/mc@sha256:23511e340cbabf07e6a8b53f9c434975708f22f3c047d6beeddc17bf1a5aed88' \
BACKUP_CONFIRM=PRODUCTION_BACKUP_AUTHORIZED \
EXPECTED_PG_IMAGE_ID='sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685' \
EXPECTED_PG_SERVICE=db EXPECTED_MINIO_SERVICE=minio scripts/backup_local.sh
~~~

La commande ne doit jamais appeler un dégel automatique. Le dégel est une
décision séparée après preuve externe et reste hors de ce run non autorisé.

## Valeurs à enregistrer

- backup_id :
- chemin absolu :
- release et Alembic :
- phase et active_writes :
- objets source/copie :
- SHA-256 externe :
- résultat pg_restore --list :
- résultats sha256sum :
- opérateur, heure UTC et autorisation :
