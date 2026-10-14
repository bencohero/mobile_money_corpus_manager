# G10.1 — Clôture des campagnes historiques et plan de nettoyage

**Serveur :** `vmi3474447`  
**Projet :** Mobile Money Corpus Manager  
**Date :** 2026-10-14  
**Statut :** **PLAN PRÊT POUR DÉCISION OPÉRATEUR — AUCUNE OPÉRATION DESTRUCTIVE**

Ce document complète [G10_DOCKER_CLEANUP_WAVE2_MANIFEST.md](G10_DOCKER_CLEANUP_WAVE2_MANIFEST.md). Aucun conteneur n’a été arrêté, aucun volume, réseau ou image n’a été supprimé. Traefik, le pare-feu, Docker, la production, le développement, les sauvegardes et le rollback n’ont pas été modifiés.

## 1. Méthode et périmètre

Sources recoupées :

- inventaire Docker en lecture seule : conteneurs, projets Compose, labels, images, montages, réseaux, volumes, processus et mémoire ;
- fichiers Compose `docker-compose.test.yml`, `docker-compose.e2-migration.yml`, `G2_DOCKER_OVERRIDE.yml`, `docker-compose.c1.test.yml`, `docker-compose.c1b.test.yml`, `docker-compose.d.test.yml` ;
- rapports G2, Remédiation C/C.1, P0-A.2, G8.8-A/B, G9-R2 et F5A2/F5A3 ;
- scripts et références de création/restauration trouvés dans le dépôt ;
- contrôles ponctuels PostgreSQL, MinIO, journaux applicatifs et états `/health`/`/ready`.

Les secrets, mots de passe et valeurs d’environnement sensibles ne sont pas reproduits.

## 2. Ressources protégées

À conserver sans modification :

- projet `mobile_money_corpus_manager_v0_1` et ses volumes PostgreSQL, MinIO et audio ;
- projet `mobile_money_corpus_manager_dev` et ses volumes ;
- conteneur et image de rollback G8.5-R ;
- Traefik, CrowdSec, Beszel, Vaultwarden, Superset, pgAdmin, PostgreSQL global, BentoPDF et IT Tools ;
- réseaux `frontend`, backend de production, développement et réseaux partagés ;
- sauvegardes sous `/home/sangouman/mobile-money-corpus-backups/` ;
- règles UFW/iptables/ip6tables, configuration Traefik et démon Docker.

Les contrôles précédents identifient notamment la production `mobile_money_corpus_manager_v0_1-app-1`, `...-db-1`, `...-minio-1`, le développement `mobile_money_corpus_manager_dev-*` et le rollback `mobile_money_corpus_manager_g8_5_r-app`. Ils restent hors périmètre.

## 3. Historique et clôture par campagne

### G2 / E.2 migration

**Propriétaires et preuves :**

- `docker-compose.test.yml` fournit le socle P0-A.2 ;
- `docker-compose.e2-migration.yml` définit les volumes `mobile-money-corpus-e2-migration-*` ;
- `G2_DOCKER_OVERRIDE.yml` définit `g2-migration-*` et le réseau `g2-migration-network` ;
- `G2_MIGRATION_EXECUTION.md` et `G2_FINAL_DECISION.md` documentent une migration isolée réussie de `0005` vers `0008), 30 objets MinIO vérifiés, snapshots PostgreSQL et 158 tests réussis.

**Nature des données :** l’exécution G2 restaure une archive historique dans un clone isolé. Les données ne sont donc pas assimilables à de simples fixtures synthétiques. Les secrets historiques ont été réinitialisés uniquement dans le clone applicatif, pas dans l’archive.

**État de clôture documentaire :** fonctionnellement clôturé avec avertissements.  
**État Docker :** non clôturé opérationnellement : G2 clean et G2 migration ont encore des processus actifs et des connexions/volumes de migration.  
**Décision :** **VALIDATION OPÉRATEUR REQUISE** pour la conservation ou l’archivage de l’archive historique et des snapshots avant suppression.

Ressources concernées :

- conteneurs `g2-clean-*` et `g2-migration-*` listés nominativement dans le manifeste G10 ;
- réseaux `g2-migration-network` et `mobile-money-corpus-e2-migration` ;
- volumes `g2-migration-pgdata`, `g2-migration-miniodata`, `g2-migration-restore-pgdata`, `g2-migration-restore-miniodata`, `g2-migration-backup`, `mobile-money-corpus-e2-migration-pgdata`, `...-miniodata`, `...-backup` ;
- images G2 listées par digest dans le manifeste G10.

### P0A2

**Propriétaire :** `docker-compose.test.yml), projet `mobile-money-corpus-p0a2-test).  
**Preuves :** `docs/P0A2_INTEGRATION_RECOVERY.md`, `RAPPORT_VALIDATION_P0A4.md`, script `scripts/validate_p0a2.sh`.

La documentation décrit un projet dédié avec PostgreSQL/MinIO source et restore, sans port publié, et une procédure de nettoyage bornée au projet. Toutefois, l’état actuel révèle des références croisées :

- réseau `mobile-money-corpus-p0a2-test` utilisé par D base ;
- volumes `mobile-money-corpus-p0a2-test-pgdata` et `...-miniodata` avec plusieurs références ;
- volume backup/restauration référencé par les outils G2.

**Nature des données :** les rapports P0-A décrivent des tests et fixtures, mais la présence d’un volume partagé avec G2/D empêche de conclure à l’exclusivité actuelle.

**État de clôture documentaire :** P0-A.2 reste décrit avec des blockers historiques dans le document d’intégration ; C.1 est documenté comme validé sur des overlays séparés.  
**Décision :** **VALIDATION OPÉRATEUR REQUISE**. Aucun volume P0A2 ne peut être supprimé isolément.

### Remédiation D

**Propriétaire attendu :** `docker-compose.d.test.yml).  
**Preuve de conception :** ce Compose prévoit `mobile-money-corpus-d-test`, `d-test-pgdata` et `d-test-miniodata`, explicitement distincts.

**Écart observé :** les conteneurs actuellement présents utilisent le réseau et les volumes P0A2, et non exclusivement les noms `d-test-*` prévus par le Compose. Cette dérive de déploiement est une preuve de dépendance ou de recréation historique non résolue.

**Nature des données :** bucket configuré `d-test-bucket`, mais le nom du bucket ne prouve pas la provenance des objets. Une vérification de manifestes et de propriétaire est requise.

**État :** partiellement arrêté, avec MinIO actif et un conteneur applicatif créé.  
**Décision :** **VALIDATION OPÉRATEUR REQUISE** ; le groupe ne peut pas être traité avant séparation ou clôture prouvée de P0A2.

### D1

**Propriétaire attendu :** `docker-compose.test.yml` + `docker-compose.c1.test.yml).  
**Preuves :** `REMEDIATION_C_REPORT.md` indique que C.1 utilise des volumes, buckets et réseaux dédiés ; la révision PostgreSQL vérifiée est `0007_integrity_and_transcription_versions), avec tests HTTP et benchmarks validés.

**État :** trois conteneurs actifs/healthy.  
**Données :** bucket configuré `c1-test-bucket), PostgreSQL de test. La documentation C.1 indique des données synthétiques de validation, mais la conservation des volumes actuels et l’absence d’archive nécessaire doivent encore être confirmées par l’opérateur.

**Ressource partagée :** réseau `mobile-money-corpus-c1-test`, également attaché à D3.  
**Décision :** **VALIDATION OPÉRATEUR REQUISE**. D1 et D3 doivent être clôturés ensemble pour le réseau, ou le réseau doit être conservé jusqu’à migration/arrêt séparé.

### D2

**Propriétaire attendu :** `docker-compose.test.yml` + `docker-compose.c1b.test.yml).  
**Preuves :** overlay C.1b, volumes `c1b-*`, réseau `mobile-money-corpus-c1b-test`, bucket configuré `c1b-test-bucket`.

**État :** trois conteneurs actifs/healthy, avec une connexion PostgreSQL idle observée.  
**Nature des données :** la documentation établit une campagne de validation isolée, mais aucune attestation de conservation ou de purge des artefacts n’a été trouvée.

**Décision :** **VALIDATION OPÉRATEUR REQUISE**. Le réseau paraît dédié à D2 mais reste actif ; il ne doit être supprimé qu’après preuve d’arrêt et d’exclusivité.

### D3

**Propriétaire attendu :** `docker-compose.test.yml` + `docker-compose.c1.test.yml).  
**Preuves :** mêmes overlays C.1, bucket configuré `c1-test-bucket`, révision de schéma documentée dans C.1.

**État :** trois conteneurs actifs/healthy.  
**Ressource partagée :** réseau `mobile-money-corpus-c1-test` partagé avec D1.  
**Décision :** **VALIDATION OPÉRATEUR REQUISE**. D3 ne peut pas être supprimé comme projet indépendant si le réseau commun doit rester à D1.

### G8.8 source/restore

**Propriétaire Compose :** non trouvé. Les conteneurs `g88-a-source-*` et `g88-a-restore-*` ont été créés sans labels Compose.

**Preuves de création et d’usage :**

- `G8_8_A_TEST_RESULTS.md` identifie explicitement ces cibles et le réseau `g88-a-isolated` ;
- `G8_8_B_TEST_RESULTS.md` confirme huit tests de contrat, restauration synthétique schema 1/2 et restauration d’une archive historique schema 2 ;
- `G9_R2_ISOLATED_RESTORE.md` confirme la restauration schema 2 sur `g88-a-restore-db` et `g88-a-restore-minio` ;
- `G9_R2_RELEASE_MANIFEST.json` référence `g88-a-isolated` comme réseau de restauration isolée ;
- aucune commande versionnée de création directe des noms `g88-a-*` n’a été retrouvée dans le dépôt ; la création semble provenir d’une procédure opérateur ou d’un script hors dépôt.

**Nature des données :** mélange démontré de fixtures synthétiques et d’une archive historique schema 2. Les volumes source/restore ne sont donc pas supprimables par simple lecture du nom.

**État documentaire :** G8.8-A validé, G8.8-B bloqué pour usage opérationnel faute de destination externe et de restic ; G8.8 global reste `NOT_READY_FOR_G8_8_EXECUTION_APPROVAL`.  
**Décision :** **VALIDATION OPÉRATEUR REQUISE** pour archiver ou supprimer les volumes source/restore, même si les connexions PostgreSQL sont actuellement absentes.

Ressources :

- quatre conteneurs `g88-a-source-db`, `g88-a-source-minio`, `g88-a-restore-db`, `g88-a-restore-minio` ;
- réseau `g88-a-isolated` ;
- volumes anonymes listés dans le manifeste G10 ;
- images officielles PostgreSQL/MinIO, à ne pas supprimer globalement.

### F5A2

**Preuves :** `F5A2_BACKUP_VALIDATION.md` et `F5A2_EXECUTION_RUNBOOK.md`.

La campagne a utilisé des conteneurs neufs, réseau dédié `f5a2-isolated`, PostgreSQL/MinIO et `tmpfs` uniquement, avec deux lignes et deux objets synthétiques. La validation synthétique est réussie, mais la décision est **BLOQUÉE pour autorisation réelle** car le garde d’écriture n’était pas présent dans l’image de production observée.

**État Docker :** conteneurs arrêtés, réseau vide, pas de volume Docker persistant candidat identifié.  
**Décision :** conteneurs et réseau sont **CANDIDATS À SUPPRESSION APRÈS VALIDATION OPÉRATEUR**, sous réserve de confirmer qu’aucun log/preuve de validation ne doit être conservé. La suppression ne procurerait pratiquement aucun gain de volume persistant ; le réseau et les conteneurs sont le gain principal.

### F5A3

**Preuves :** `F5A3_GO_NO_GO.md`, `F5A3_PRODUCTION_COMPATIBILITY.md`, `F5A3_WRITE_FREEZE_VALIDATION.md`, `F5A4_ROLLBACK_VALIDATION.md`.

La candidate `f5a3-candidate:0005-freeze`, digest `sha256:170270493de28c7e4fffbf1cd396122680d4eb2684249edd8fd7e166be4493e2`, a validé le correctif de gel sur des données synthétiques et des restaurations isolées. La décision est prête pour autorisation du correctif, pas pour déploiement automatique.

**Distinction rollback :** le rollback G8.5-R est une autre ressource protégée et doit être conservé. L’image F5A3 est une candidate de validation, pas la release de rollback, mais sa conservation peut être nécessaire pour reproduire ou auditer le correctif.

**État Docker :** conteneurs arrêtés, réseau `f5a3-isolated` vide, image candidate présente.  
**Décision :** conteneurs et réseau sont **CANDIDATS À SUPPRESSION APRÈS VALIDATION OPÉRATEUR** ; l’image candidate est **À CONSERVER** jusqu’à décision explicite sur la rétention du correctif/rollback de test. Ne pas confondre cette image avec l’image de production ou G8.5-R.

## 4. Graphe de dépendances

Vue logique reconstruite :

```text
G2 clean
  ├─ g2-migration-network
  ├─ g2-migration-pgdata / miniodata
  ├─ g2-migration-restore-pgdata / restore-miniodata
  └─ g2-migration-backup
       └─ archive historique + snapshots de migration

G2 migration
  ├─ mobile-money-corpus-e2-migration
  ├─ e2-migration-pgdata / miniodata / backup
  └─ outils migration

P0A2 ── mobile-money-corpus-p0a2-test
  ├─ p0a2-test-pgdata / miniodata / restore-* / backup
  ├─ attaché à D base
  └─ backup/restore référencé par G2 tools

D base ── état actuel attaché à P0A2
  └─ divergence avec docker-compose.d.test.yml (qui prévoit d-test-*)

D1 ─┐
    ├─ mobile-money-corpus-c1-test
D3 ─┘
    ├─ volumes D1/D3 distincts
    └─ bucket configuré c1-test-bucket

D2 ── mobile-money-corpus-c1b-test
    └─ volumes c1b distincts, bucket configuré c1b-test-bucket

G8.8 source/restore
  ├─ g88-a-isolated
  ├─ volumes anonymes source/restore
  └─ fixtures synthétiques + archive historique schema 2

F5A2 ── f5a2-isolated + tmpfs
F5A3 ── f5a3-isolated + f5a3-candidate
G8.5-R ── production backend/tmpaudio : protégé, non candidat
```

Le graphe est volontairement conservateur : une connexion PostgreSQL inactive ne retire pas une dépendance potentielle, et un volume nommé « test » n’est pas déclaré supprimable sans preuve de provenance et d’exclusivité.

## 5. Classification nominative

### À CONSERVER

- toutes les ressources de production et de développement ;
- rollback G8.5-R et son image ;
- sauvegardes hors Docker ;
- réseau et volumes partagés tant que leurs propriétaires ne sont pas clôturés ;
- archive historique G2 et snapshots tant qu’une politique de conservation opérateur n’est pas décidée ;
- volumes source/restore G8.8 tant que leur archive historique n’est pas archivée ou explicitement abandonnée ;
- image `f5a3-candidate:0005-freeze` tant que la rétention du correctif n’est pas décidée.

### CANDIDATS CONDITIONNELS — VALIDATION OPÉRATEUR REQUISE

Les ressources suivantes pourront être supprimées uniquement après décision nominative, archivage éventuel et nouvelle vérification des dépendances :

- conteneurs et réseau F5A2 ;
- conteneurs et réseau F5A3, hors image candidate tant qu’elle est conservée ;
- conteneurs G2 après décision sur l’archive historique, snapshots et volumes de migration ;
- conteneurs D1/D3 ensemble, puis leur réseau uniquement s’il est vide ;
- conteneurs D2 et réseau `mobile-money-corpus-c1b-test` ;
- conteneur D base et ressources `d-test-*` uniquement si l’état réel est réaligné et les références P0A2 levées ;
- conteneurs P0A2 et volumes exclusivement dédiés, après retrait prouvé des attaches G2/D ;
- G8.8 uniquement après archivage/abandon explicite des fixtures et de l’archive historique.

### SUPPRIMABLE MAINTENANT

**Aucune ressource.**

Cette absence est intentionnelle : les campagnes actives, les réseaux partagés, les données historiques et les propriétaires non démontrés imposent une décision humaine préalable.

## 6. Estimation des gains

Observations instantanées, à ne pas présenter comme gains acquis :

| Groupe | RAM observée | Disque logique connu | Limitation |
|---|---:|---:|---|
| G2 clean + migration | ~1,10 GiB | environ 174 MiB de volumes G2 connus, hors anonymes/partagés | archive historique et outils actifs |
| D/D1/D2/D3 | ~1,30 GiB | au moins ~0,15 GiB de volumes D actifs ; P0A2 exclu | réseau D1/D3 partagé |
| G8.8 | ~532 MiB | volumes anonymes à mesurer séparément | source/restore mixte |
| F5A2 | négligeable à l’arrêt | tmpfs, pas de volume persistant confirmé | logs/preuves à conserver éventuellement |
| F5A3 | négligeable à l’arrêt | image candidate affichée ~1,09 GB par Docker | conservation de la candidate à décider |

Le gain réel devra être mesuré par groupe avec `docker system df -v`, `free -h` et `df -h`. La taille logique d’une image, sa taille de couches et l’espace réellement libéré ne sont pas équivalents.

## 7. Stratégie et ordre recommandé après décision

1. Décider séparément de la conservation des archives historiques G2 et G8.8, avec emplacement, empreinte et durée de rétention.
2. Décider de la conservation de l’image candidate F5A3, sans toucher à G8.5-R.
3. Traiter F5A2, puis vérifier production/dev/services protégés ; c’est le groupe le moins dépendant sous réserve de validation des preuves.
4. Traiter F5A3 ; supprimer les conteneurs et le réseau seulement si la candidate est conservée ou archivée.
5. Clôturer D1 et D3 ensemble ; supprimer leurs conteneurs, puis le réseau partagé seulement lorsqu’il est vide et qu’aucune autre campagne ne l’utilise.
6. Clôturer D2 et son réseau dédié après contrôle de la base, du bucket et de l’archivage.
7. Résoudre la divergence D base/P0A2 avant tout arrêt ; ne pas utiliser `docker compose down -v` sur le projet historique sans inventaire des références.
8. Clôturer G2 et P0A2 en dernier, après séparation des volumes backup/restore et archivage des preuves de migration.
9. Traiter G8.8 en dernier parmi les restaurations, après décision sur l’archive historique et preuve qu’aucune validation G9-R2 ne reste nécessaire.
10. Après chaque groupe : vérifier production, développement, rollback, Traefik et les autres applications ; mesurer les ressources ; arrêter immédiatement au premier échec.

Aucune commande de nettoyage global n’est autorisée. Les suppressions futures devront employer une liste fermée de noms/IDs validés, sans suppression par préfixe.

## 8. Décisions humaines requises

1. L’archive historique G2 et ses snapshots doivent-ils être conservés, transférés ou détruits ?
2. L’archive historique restaurée dans G8.8 doit-elle être conservée comme preuve G9-R2 ?
3. Les fixtures et données D1/D2/D3 sont-elles formellement autorisées à la suppression par le responsable données ?
4. Qui est le propriétaire des conteneurs G8.8 créés sans Compose et où se trouve le script/procès-verbal de création ?
5. La candidate F5A3 doit-elle être conservée pour audit/rollback de test ?
6. Quelle politique de conservation s’applique aux logs, manifestes, dumps et objets MinIO des campagnes ?
7. La divergence entre `docker-compose.d.test.yml` et les attaches réelles P0A2 doit-elle être corrigée par une recréation contrôlée, ou les ressources doivent-elles être abandonnées après archivage ?
8. Une fenêtre d’arrêt et un responsable de validation santé doivent-ils être nommés par groupe ?

## 9. Décision du plan

**G10.1 : PLAN PRÊT POUR DÉCISION OPÉRATEUR — AUCUN NETTOYAGE EXÉCUTÉ.**

Aucune campagne ne peut être déclarée définitivement supprimable sur la seule base de son nom, d’un état arrêté, d’une connexion PostgreSQL inactive ou d’un bucket marqué « test ».

