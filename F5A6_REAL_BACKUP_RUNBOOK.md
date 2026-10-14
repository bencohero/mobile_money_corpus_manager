# F5A6 — runbook de première sauvegarde réelle

Ne pas exécuter avant approbation signée. Se connecter au VPS, vérifier le commit et lire `F5A6_EXECUTION_APPROVAL.md`.

1. Confirmer que l’application est toujours `APP_STOPPED` ou `APP_ABSENT`, que PostgreSQL/MinIO correspondent exactement aux noms et images audités, et qu’aucun service d’écriture n’est actif.
2. Obtenir l’attestation opérateur couvrant hôte, Docker, cron/systemd, clients MinIO externes, sessions PostgreSQL et identifiants partagés.
3. Installer le client MinIO approuvé, vérifier son SHA-256 hors logs, puis définir `MC_BIN` et `MC_SHA256`.
4. Créer, avec autorisation, `/var/backups/mobile-money-corpus/` en mode 0700. Le script ne crée pas de répertoire système implicite avant cette étape d’autorisation.
5. Lancer manuellement, sans `docker compose up/down/stop/start` :

```bash
BACKUP_MODE=offline_app \
CONFIRM_TARGET=YES \
OFFLINE_WRITERS_ATTESTED=YES \
BACKUP_APPROVED=YES \
PROJECT_DIR=/home/sangouman/apps/mobile_money_corpus_manager_v0_1 \
BACKUP_ROOT=/var/backups/mobile-money-corpus \
PG_CONTAINER=mobile_money_corpus_manager_v0_1-db-1 \
MINIO_CONTAINER=mobile_money_corpus_manager_v0_1-minio-1 \
APP_CONTAINER=mobile_money_corpus_manager_v0_1-app-1 \
PG_DATABASE=corpus MINIO_BUCKET=mobile-money-corpus \
MINIO_ENDPOINT=<endpoint-interne> MINIO_ACCESS_KEY=<identifiant> \
MINIO_SECRET_KEY=<secret> MC_BIN=<client-approuve> MC_SHA256=<sha256> \
./scripts/backup_local.sh
```

Ne pas copier les secrets dans un fichier de rapport ou une commande conservée dans l’historique. Surveiller uniquement les horodatages, le volume de sortie et l’existence de `<id>.incomplete`; ne pas afficher l’environnement.

Après succès, vérifier `sha256sum --check <archive>/manifests/SHA256SUMS`, `sha256sum -c` de `COMPLETION.SHA256`, `MANIFEST.json`, `backup_report.json`, la révision et le rapport de cohérence. En cas d’échec, conserver l’arborescence `.incomplete`, ses journaux et le code retour ; ne pas supprimer ni corriger les données source. La restauration se fait uniquement dans un PostgreSQL/MinIO isolé avec la procédure de restauration dédiée.
