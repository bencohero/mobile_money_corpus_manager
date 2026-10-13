# G8.8 — Plan de sauvegarde coordonnée

## Préconditions obligatoires

1. Autorisation opérateur écrite et fenêtre de gel définie.
2. Destination externe absolue, hors dépôt et hors volumes de production,
   montée et testée en écriture contrôlée.
3. Image MinIO client épinglée par digest.
4. Vérification des conteneurs exacts, volumes, ports et sessions PostgreSQL.
5. Aucun writer concurrent attesté.

## Séquence proposée, non exécutée

1. Capturer l’état release/Alembic et les inventaires PostgreSQL/MinIO.
2. Passer le mécanisme write-freeze par `drain`, attendre zéro écriture, puis
   confirmer `FROZEN`.
3. Exécuter `scripts/backup_local.sh` en mode production avec
   `BACKUP_CONFIRM=PRODUCTION_BACKUP_AUTHORIZED`, destination externe et client
   MinIO épinglé.
4. Vérifier `COMPLETE`, `COMPLETION.SHA256`, sommes PostgreSQL, nombre d’objets
   MinIO et manifestes.
5. Conserver l’attestation hors VPS.
6. Ne dégeler qu’après clôture de la fenêtre et autorisation explicite.

## Blocage de procédure à résoudre avant exécution

`backup_local.sh` produit `postgres/corpus.dump`, `MANIFEST.json` et
`manifests/SHA256SUMS`. `scripts/restore.sh` attend `postgres.dump`,
`MANIFEST.SHA256` et `SHA256SUMS` à la racine. Aucun lancement ne doit avoir
lieu avant alignement formel de ces layouts et validation de la commande.
