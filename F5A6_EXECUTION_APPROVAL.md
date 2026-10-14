# F5A6 — approbation d’exécution

## État

`READY_FOR_AUTHORIZATION`

Aucune sauvegarde réelle n’a été lancée. Aucun répertoire `/var/backups/mobile-money-corpus/` n’a été créé. Aucun service, volume, objet MinIO ou enregistrement PostgreSQL de production n’a été modifié.

## Conditions obligatoires avant lancement

- confirmer le commit `e4d9c905f8b7077a65cc0ef9e4e68f2236c2680a` ;
- confirmer PostgreSQL `mobile_money_corpus_manager_v0_1-db-1` en version 16 et MinIO `mobile_money_corpus_manager_v0_1-minio-1` avec l’image auditée ;
- confirmer `APP_STOPPED` ou `APP_ABSENT`, sans instance alternative ;
- vérifier et signer l’absence d’écritures hôte/Docker/PostgreSQL/MinIO/cron ;
- fournir le digest du client MinIO approuvé ;
- confirmer un chemin de sauvegarde local disponible et non existant ;
- autoriser explicitement `BACKUP_APPROVED=YES` pour une seule exécution.

## Attestation opérateur

Opérateur : ____________________  Date UTC : ____________________

J’atteste avoir vérifié les chemins d’écriture impossibles à exclure automatiquement et autorise uniquement la capture décrite dans le runbook.

Signature : ____________________
