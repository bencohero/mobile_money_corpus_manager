# F.4 — État de préparation de l’implémentation sauvegarde

Date : 2026-10-11  
Statut : **BLOQUÉ POUR DONNÉES RÉELLES — PRÊT POUR TEST SYNTHÉTIQUE**

## 1. Contrôles ajoutés

`scripts/backup.sh` exige maintenant :

- `BACKUP_MODE` (`synthetic` ou `production`) ;
- `BACKUP_TARGET_ID` (`synthetic` ou `mobile_money_corpus_manager_v0_1`) ;
- une confirmation explicite `BACKUP_CONFIRM=PRODUCTION_BACKUP_AUTHORIZED` pour
  la production ;
- un chemin absolu hors du dépôt courant ;
- un manifeste JSON, un inventaire MinIO, `SHA256SUMS` et `MANIFEST.SHA256` ;
- une vérification des empreintes avant succès.

`scripts/restore.sh` refuse le mode production, refuse l’identifiant de production,
exige un identifiant isolé, vérifie les deux manifestes avant `pg_restore` et garde
la confirmation `CONFIRM_RESTORE=YES`.

Ces contrôles empêchent une confusion simple entre développement, synthétique,
restauration isolée et production ; ils ne remplacent pas une revue humaine de la
cible réseau et des identifiants.

## 2. Cohérence et contenu du manifeste

Le script doit être lancé pendant le gel décrit dans `WRITE_FREEZE_DESIGN.md`.
Le manifeste contient le mode, l’identifiant cible, l’horodatage UTC, l’hôte/base
PostgreSQL, le bucket MinIO, le nombre de fichiers et l’exigence de fenêtre
contrôlée. Le dump PostgreSQL et chaque fichier MinIO sont empreintés en SHA-256.
Les métadonnées MinIO sont capturées dans `minio_inventory.jsonl`; les politiques,
service accounts et paramètres nécessaires doivent être exportés par une étape
d’exploitation autorisée, sans secrets en clair.

## 3. Destination et chiffrement

La destination locale doit être un chemin absolu hors volumes applicatifs et hors
dépôt. La destination hors VPS doit être fournie par l’exploitation, avec stockage
versionné/immuable si disponible. Le chiffrement est à réaliser avant transfert avec
une clé publique `age` ou KMS fournie par le responsable sécurité ; la clé privée ne
doit jamais être présente sur le VPS. La commande de transfert exacte et la politique
de rétention restent des paramètres à renseigner avant production.

## 4. Test synthétique

Le harnais `scripts/validate_backup_synthetic.sh` utilise des commandes factices et
des fichiers temporaires : aucun socket Docker, PostgreSQL, MinIO ou bucket réel
n’est utilisé. Il vérifie la création de l’archive, du manifeste, des empreintes,
puis le chemin de restauration isolé et les garde-fous de cible.

Commande :

```bash
bash scripts/validate_backup_synthetic.sh
```

Résultat attendu : `synthetic backup/restore passed`. Le test ne constitue pas une
preuve de restauration PostgreSQL/MinIO réelle ; cette preuve nécessite un Compose
isolé et une autorisation distincte.

## 5. Autorisations restantes

Avant toute donnée réelle : responsable données pour la fenêtre et les écarts,
exploitation pour la destination et la rotation, sécurité pour la clé publique et
le stockage hors VPS, propriétaire Corpus pour le test de restauration. Aucune
commande de sauvegarde réelle ou de transfert ne doit être ajoutée à un cron/timer
avant ces signatures.
