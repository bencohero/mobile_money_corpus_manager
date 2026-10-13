# G9-R2 — Sauvegarde locale

Destination: `/home/sangouman/mobile-money-corpus-backups/`.

Permissions du répertoire: `0700`. Espace disponible observé: environ 85 Go. Les archives historiques ont été conservées; aucune suppression ni écrasement.

Nouvelle archive: `/home/sangouman/mobile-money-corpus-backups/20261013T043445Z/`

- contrat: schema 2, `COMPLETE`
- PostgreSQL: `postgres/corpus.dump`, dump non vide et inventaire généré
- MinIO: bucket `mobile-money-corpus`, 36 objets capturés
- `COMPLETION.SHA256` et `manifests/SHA256SUMS`: vérifiés
- image `mc`: épinglée par digest
- cible: conteneurs PostgreSQL/MinIO du projet de production, sans port publié

La capture a été faite avec `scripts/backup_local.sh`. L’application de ce projet n’était pas active; le manifest porte donc `coherence=validated_write_freeze_required`. Aucun dégel automatique ni changement de mot de passe n’a été effectué.

Risque résiduel: `EXTERNAL_BACKUP_PENDING_MANUAL_OPERATOR_ACTION`. La copie Kubuntu/restic reste à faire manuellement par l’opérateur; restic n’a pas été installé et aucune connexion SSH entrante n’a été tentée.
