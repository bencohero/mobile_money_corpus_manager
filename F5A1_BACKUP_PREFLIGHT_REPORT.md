# F.5A.1 — Rapport de prévol de sauvegarde locale temporaire

Date du contrôle : 2026-10-11 (Europe/Berlin). Contrôle strictement en lecture seule.

## Décision

**BLOQUÉ — pas encore prêt pour autorisation de sauvegarde coordonnée PostgreSQL + MinIO.**

La cible est identifiée sans ambiguïté, les services sont sains et l’espace disque est probablement suffisant, mais aucun mécanisme applicatif de gel et de drain des écritures n’est présent. `docker compose stop app` évite de nouvelles requêtes après arrêt, mais ne prouve pas que les requêtes en vol sont terminées avant le dump PostgreSQL et la copie MinIO. Le script existant qui arrête l’application ne vérifie pas ce drain.

Correction minimale requise avant autorisation : ajouter ou valider une procédure de maintenance qui empêche les nouvelles écritures, attend la fin des requêtes en vol, vérifie zéro opération d’écriture active, puis seulement autorise la capture PostgreSQL et MinIO. Aucun changement de Traefik ni aucun gel n’a été effectué dans ce ticket.

## Cibles de production observées

| Élément | Preuve observée |
|---|---|
| Projet Compose | `mobile_money_corpus_manager_v0_1`, fichier `/home/sangouman/apps/mobile_money_corpus_manager_v0_1/docker-compose.yml` |
| PostgreSQL | conteneur `mobile_money_corpus_manager_v0_1-db-1`, image `postgres:16-alpine`, digest `sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685` |
| Base | `corpus`, connexion interne au service `db`/alias `mobile-money-corpus-db`, port non publié |
| Révision | `0005_workshop_attribution` (`alembic current` dans le conteneur applicatif) |
| MinIO | conteneur `mobile_money_corpus_manager_v0_1-minio-1`, image `minio/minio:RELEASE.2025-04-22T22-12-26Z`, digest `sha256:a1ea29fa28355559ef137d71fc570e508a214ec84ff8083e39bc5428980b015e` |
| Bucket | `mobile-money-corpus` |
| Volumes | `..._pgdata` → PostgreSQL, `..._miniodata` → `/data`, `..._tmpaudio` → `/tmp/audio` |
| PostgreSQL 18 indépendant | conteneur `postgres`, image `postgres:18`, port hôte `5432`; exclu de la cible |

L’image applicative observée est `sha256:c2e3e50e3e74d2901cbe5308b77ac9c4d0dab660668b836f6bda4b23a49f2467`.

## État système et Docker

- Cible production : `app` actif depuis 4 jours ; `db` et `minio` actifs depuis 5 jours, tous deux `healthy`.
- Réseau backend cible : `mobile_money_corpus_manager_v0_1_backend`, `internal=true`, sous-réseau `172.23.0.0/16`, uniquement les trois conteneurs de la stack.
- Application également attachée au réseau externe `frontend` et publiée via les labels Traefik ; Traefik n’a pas été modifié.
- Images/digests et labels `com.docker.compose.project`, `service`, `working_dir`, `config_files` relevés par `docker inspect`.
- Disque `/` : 193G, 98G utilisés, 96G disponibles (51%).
- Mémoire : 11Gi total, 3.7Gi disponibles, swap absente. Charge : `7.76 / 4.33 / 3.19`.
- Aucun `backup.sh`, `backup_mobile_money_corpus.sh`, `pg_dump`, `pg_restore`, `mc mirror`, `rclone`, `restic` ou `borg` actif au moment du contrôle.
- `/var/backups/mobile_money/` existe déjà et contient un dossier antérieur inaccessible en lecture à l’utilisateur courant ; ce n’est pas la destination proposée. La destination proposée ci-dessous est `/var/backups/mobile-money-corpus/`, non créée.

## Santé et inventaire sans données personnelles

Comptages PostgreSQL lus dans la base `corpus` :

| Table / objet métier | Comptage |
|---|---:|
| Participants | 17 |
| Utilisateurs | 21 |
| Ateliers | 4 |
| Codes d’atelier | 6 |
| Enregistrements | 15 |
| Soumissions idempotentes | 15 |
| Compteurs de prises | 15 |
| Transcriptions | 1 |
| Journaux d’audit | 115 |

Autres contrôles : 15 enregistrements ont raw et WAV, tailles et SHA-256 renseignés ; 15 sont `READY` ; aucun compteur n’est inférieur au maximum de prise observé ; aucune soumission ne référence un enregistrement ou utilisateur absent. Il reste 14 enregistrements sans transcription, état métier attendu et non une preuve de corruption.

La révision Alembic observée est `0005_workshop_attribution`, alors que le dépôt contient `0006`, `0007` et `0008`. Les tables `transcription_history`, `participant_language_sequences` et `rate_limit_buckets` ne sont pas présentes dans le schéma observé. Cette dérive doit être traitée et validée dans un changement séparé ; aucune migration n’a été appliquée ici.

MinIO : bucket accessible et service live ; 30 objets, environ 5,289,708 octets. La réconciliation applicative en lecture seule a retourné `[]` et code 0 : aucune divergence détectée sur les objets attendus, tailles, checksums ou objets orphelins au moment du contrôle. Cela ne prouve pas une cohérence historique entre deux captures futures.

## Risques déterminants

1. PostgreSQL et MinIO sont deux systèmes sans transaction commune. Un dump PostgreSQL et un miroir MinIO séparés ne forment une sauvegarde cohérente que dans une fenêtre sans écritures.
2. L’application réalise des écritures coordonnées mais multi-étapes : upload raw/WAV, vérification, réservation idempotente, commit d’enregistrement, transcription, validation et audit. Les compensations existent, mais elles ne remplacent pas un point de gel.
3. Aucun worker asynchrone distinct n’a été observé ; les traitements audio sont dans le chemin HTTP. Cela simplifie le périmètre, mais ne fournit pas de drain mesurable.
4. Le script principal modifié `scripts/backup.sh` crée directement la destination, écrit directement les fichiers finaux et utilise `mc alias set`; il ne vérifie pas le conteneur/digest cible ni un drain. Il ne doit pas être autorisé tel quel.
5. `backup_mobile_money_corpus.sh` est plus complet, mais arrête seulement le service applicatif et ne vérifie pas les requêtes en vol ; son `trap` redémarre l’application, ce qui est indésirable sans validation explicite de l’état de la fenêtre.
6. La dérive Alembic/code doit être résolue avant de présenter la copie comme sauvegarde opérationnelle complète ; elle peut indiquer qu’une partie des chemins récents n’est pas supportée par le schéma actuellement actif.

## Destination proposée, non créée

`/var/backups/mobile-money-corpus/`

Recommandations : propriétaire `root:backup-operators` ou compte opérateur dédié, mode `0700` pour la racine et chaque run, pas de montage Docker, pas de chemin sous le dépôt, nom UTC `YYYYMMDDTHHMMSSZ`, refus si le dossier du run existe déjà, écriture dans un répertoire temporaire `run.<id>.tmp` puis renommage atomique vers le nom final. La marge de capacité doit couvrir au minimum `taille_dump_pg + taille_objets_minio + 20%`, plus 2 GiB de marge opérationnelle ; la taille réelle devra être mesurée juste avant capture. La capacité actuelle est confortable pour l’empreinte observée, mais ne suffit pas à garantir une future croissance sans mesure préalable.

## Conclusion

Services et inventaire sont suffisamment documentés pour préparer une revue. La sauvegarde coordonnée reste **BLOQUÉE** jusqu’à preuve d’un gel/drain vérifiable et validation du runbook sécurisé. Aucun service, volume, réseau, secret, règle Traefik ou donnée de production n’a été modifié.
