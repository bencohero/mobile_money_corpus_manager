# Nettoyage Docker et données de test — Rapport d’exécution

Date de l’audit : 2026-10-14  
Hôte : `vmi3474447`  
Statut : **PREMIÈRE VAGUE EXÉCUTÉE — G4, G5 ET G9-R3 SUPPRIMÉS**

## 1. Décision immédiate

La première vague a été exécutée après validation nominative de l’opérateur. Seules les campagnes `g4-preprod`, `g5-validation` et `g9-r3-test` ont été traitées. Aucun conteneur, volume, réseau ou image hors manifeste n’a été supprimé.

Les seuls candidats actuellement suffisamment attribuables pour une première vague sont les projets arrêtés `g4-preprod`, `g5-validation` et `g9-r3-test`. Les ressources actives, partagées, sans labels Compose ou liées au rollback restent hors périmètre.

## 2. Inventaire initial

Commandes exécutées en lecture seule :

```text
docker ps -a
docker compose ls -a
docker system df -v
docker volume ls
docker network ls
docker inspect <conteneurs>
docker network inspect <réseaux>
```

État Docker observé :

| Ressource | Total | Actives |
|---|---:|---:|
| Conteneurs | 85 | 40 |
| Images uniques | 91 | — |
| Volumes | 81 | 51 référencés par `system df` |
| Réseaux | 20 | — |

`docker system df` : images `16.28 GB`, dont `8.979 GB` reclaimable; conteneurs `35.38 MB`, dont `3.068 MB` reclaimable; volumes `2.228 GB`, dont `836.3 MB` reclaimable; build cache `15.58 GB`, dont `10.61 GB` reclaimable. Le build cache n’est pas inclus dans ce manifeste, car il n’est pas attribuable à un projet de test précis.

État hôte avant intervention : `free -h` indique 11 GiB RAM, 6.1 GiB disponibles et aucun swap; `df -h /` indique 193 GB, 109 GB utilisés et 85 GB disponibles (57 %). Le répertoire protégé `/home/sangouman/mobile-money-corpus-backups/` existe et occupe environ 28 MB.

Contrôles applicatifs avant intervention :

```text
https://corpus-moore.bencoherolab.com/health  -> HTTP 200
https://corpus-moore.bencoherolab.com/ready   -> HTTP 200
production app/db/minio                       -> healthy
development app/db/minio                     -> healthy
```

## 3. Classification des campagnes

### Campagnes validées et exécutées

- `g4-preprod` : conteneurs arrêtés depuis environ 34 h, réseau vide, volumes étiquetés `com.docker.compose.project=g4-preprod`.
- `g5-validation` : conteneurs arrêtés depuis environ 33–34 h, réseau vide, volumes étiquetés `com.docker.compose.project=g5-validation`.
- `g9-r3-test` : conteneurs arrêtés depuis environ 18 h, réseau vide, volumes étiquetés `com.docker.compose.project=g9-r3-test`.

Les trois groupes n’ont aucun port hôte publié et ne sont pas attachés au réseau `frontend` de production.

### Exclus du nettoyage

- Production `mobile_money_corpus_manager_v0_1` et ses trois volumes.
- Développement `mobile_money_corpus_manager_dev` et ses volumes.
- `mobile_money_corpus_manager_g8_5_r-app`, release de rollback conservée. Elle utilise encore `mobile_money_corpus_manager_v0_1_tmpaudio` et le réseau backend de production : elle ne doit pas être supprimée.
- Traefik, CrowdSec, Beszel, Vaultwarden, Superset, pgAdmin, PostgreSQL global et toutes les autres applications.
- G2 (`g2-clean`, `g2-migration`) : plusieurs conteneurs sont actifs et les bases possèdent des connexions; aucune suppression proposée.
- P0A2 et remédiations D/D1/D2/D3 : conteneurs actifs ou créés et réseaux/volumes partagés; aucune suppression proposée.
- G8.8 (`g88-a-source-*`, `g88-a-restore-*`) : quatre conteneurs actifs sans labels Compose, deux sources et deux restaurations; attribution probable à une campagne mais non prouvée. Ils sont explicitement conservés.
- F5A2/F5A3 et autres conteneurs sans labels Compose : attribution historique plausible mais absence de propriétaire Compose; exclus par la règle d’ambiguïté.
- Build cache : non attribuable; non supprimé.
- `/home/sangouman/mobile-money-corpus-backups/` : conservé.

## 4. Manifeste nominatif exécuté

### 4.1 Conteneurs candidats — G4

| Nom | ID court | État |
|---|---|---|
| `g4-preprod-app-test-1` | `c2ec79a28aaa` | exited (137) |
| `g4-preprod-app-test-run-0c82fb171a94` | `d86b8ec9bc87` | exited (0) |
| `g4-preprod-app-test-run-d125d10d6944` | `1d3ff04c6ee6` | exited (1) |
| `g4-preprod-db-restore-1` | `de1ae3b63f46` | exited (0) |
| `g4-preprod-db-test-1` | `9ab1451a4642` | exited (0) |
| `g4-preprod-minio-restore-1` | `6ece59273b76` | exited (0) |
| `g4-preprod-minio-test-1` | `ad39825a9112` | exited (0) |
| `g4-preprod-test-run-36a90d59ac6b` | `113f4d43a10e` | exited (1) |
| `g4-preprod-test-run-4c2027e9e100` | `d0b2c37e68e5` | exited (0) |
| `g4-preprod-test-run-71521468a7d5` | `79aa82cf7f1a` | exited (1) |
| `g4-preprod-tools-1` | `474a57cf8301` | exited (137) |

Justification : labels Compose `g4-preprod`, réseau `g4-preprod_default` vide, conteneurs arrêtés, montages limités aux volumes du lot F (`f-lot`).

### 4.2 Conteneurs candidats — G5

| Nom | ID court | État |
|---|---|---|
| `g5-validation-app-test-1` | `635af93acee5` | exited (0) |
| `g5-validation-db-restore-1` | `2fba025888ab` | exited (0) |
| `g5-validation-db-test-1` | `9a38b1e49227` | exited (0) |
| `g5-validation-minio-restore-1` | `b9a482d21751` | exited (0) |
| `g5-validation-minio-test-1` | `fae72edd99e5` | exited (0) |
| `g5-validation-test-run-77da58de7de4` | `98f904ae77dc` | exited (0) |
| `g5-validation-test-run-d21f476cd440` | `d41b3d899e40` | exited (1) |
| `g5-validation-tools-1` | `6c4c3e398e72` | exited (137) |

Justification : labels Compose `g5-validation`, réseau `g5-validation_default` vide, conteneurs arrêtés, volumes `g5-validation` exclusivement étiquetés.

### 4.3 Conteneurs candidats — G9-R3

| Nom | ID court | État |
|---|---|---|
| `g9-r3-test-app-test-1` | `6b06dc6c9ce8` | exited (0) |
| `g9-r3-test-db-restore-1` | `27d0def8c0fd` | exited (0) |
| `g9-r3-test-db-test-1` | `35c62a3ed9cc` | exited (0) |
| `g9-r3-test-minio-restore-1` | `9b9e8a3dc785` | exited (0) |
| `g9-r3-test-minio-test-1` | `0fbe78672f71` | exited (0) |
| `g9-r3-test-test-1` | `8b44040aaf50` | exited (0) |
| `g9-r3-test-tools-1` | `a26a0f047352` | exited (137) |

Justification : labels Compose `g9-r3-test`, réseau `g9r3-test-network` vide, volumes `g9r3-test-*` exclusivement étiquetés. L’image `mobile-money-corpus-test:g9-r3-healthcheck` est incluse ci-dessous comme image historique G9-R3 sans conteneur actif.

### 4.4 Volumes candidats

Volumes PostgreSQL/MinIO et sauvegarde exclusivement liés aux trois projets :

```text
mobile-money-corpus-f-lot-backup
mobile-money-corpus-f-lot-miniodata
mobile-money-corpus-f-lot-pgdata
mobile-money-corpus-f-lot-restore-miniodata
mobile-money-corpus-f-lot-restore-pgdata
mobile-money-corpus-g5-validation-backup
mobile-money-corpus-g5-validation-miniodata
mobile-money-corpus-g5-validation-pgdata
mobile-money-corpus-g5-validation-restore-miniodata
mobile-money-corpus-g5-validation-restore-pgdata
g9r3-test-backup
g9r3-test-miniodata
g9r3-test-pgdata
g9r3-test-restore-miniodata
g9r3-test-restore-pgdata
```

Taille observée par `docker system df -v` : environ 126.6 MB pour G4, 135.5 MB pour G5 et 100.4 MB pour G9-R3, soit environ **362.5 MB** de données de volumes. La valeur finale doit être recalculée après arrêt et suppression des conteneurs; aucun volume n’est partagé dans le manifeste proposé.

### 4.5 Réseaux candidats

```text
g4-preprod_default       ID 8f9685a9bb19   0 conteneur attaché
g5-validation_default    ID 95ed1c0200d7   0 conteneur attaché
g9r3-test-network        ID ff078e30f4c2   0 conteneur attaché
```

Ils portent des labels Compose propres à leur projet et ne sont pas `frontend`, `backend`, `mobile_money_corpus_dev_internal`, `infra-network` ou un autre réseau protégé.

### 4.6 Images candidates

Images de test sans conteneur actif après suppression des conteneurs nominés :

```text
g4-preprod-app-test:latest                         sha256:15ec13046f980c428c23aa1118404f14a304a78799e4f2473c6557ffd314dfc1  1.07GB
g4-preprod-test:latest                             sha256:d28f8b0417e83e6bcedeea5297ed75f663e11aff944077a693460492fa392e24  1.07GB
g4-preprod-tools:latest                            sha256:40cdacc83edeac912f3cd9bc1a3c51ae9243a404361649190d1815afa1efb35d  469MB
mobile-money-corpus-f-lot-app-test:latest          sha256:77a1ba8df65c9f1dc39e5fd336a65e9fe8ef99ef551b2bd8663c6989199c12d4  1.07GB
mobile-money-corpus-f-lot-test:latest              sha256:2369730d606f508853dbc03086b73419dc2793424e924357de2d57d319d740fd  1.07GB
mobile-money-corpus-f-lot-tools:latest             sha256:2acea4b54d32599e8c4ca05ac1690adc14a3da7f5ec0e7165f4212d16f2022e5  469MB
g5-validation-app-test:latest                      sha256:9f417ac161bef3404f64ed555218a90c767b5fd0795795a31bec19da3050b862  1.07GB
g5-validation-test:latest                          sha256:c7de9408a13687ea86c85a6b39c665c0f00bc566faf6ffd596d417696dfcd45d  1.07GB
g5-validation-tools:latest                         sha256:42c42ff477129f5b9ab92d076e1d724b0a6af2e2c35594e9aaecf7ccb430174c  469MB
mobile-money-corpus-g5-validation-app-test:latest sha256:ed3c2054c3bf6ff2ae15922a744106d3ebaa4364d4ebe4730e814c6a0eed7cf9  1.07GB
mobile-money-corpus-g5-validation-test:latest     sha256:18edf1e8535be1be4f913442479102fcd7b576a235a6a4852a7483f3c0b3b2c5  1.07GB
g9-r3-test-app-test:latest                          sha256:0487561528c40f4c77cef0a1fe747ca7ce818468d9b47b420a3015c8ea91543a  1.07GB
g9-r3-test-test:latest                              sha256:fd8ef937db7728f4fd77a52e517021ecb9899835f47466ae72347149e77eef43  1.07GB
g9-r3-test-tools:latest                             sha256:d503a4f62ef6f44702280319555e8ce10d1be8996bb04cbf3bb5cecbf8bfd8f1  469MB
mobile-money-corpus-test:g9-r3-healthcheck        sha256:5fba4e374c132ff510927789d16d1fd3671564f0167fcbbc07911080223e689b  1.07GB
```

La taille logique cumulée est d’environ 11.0 GB, mais la récupération réelle sera inférieure ou égale à cette valeur à cause des couches partagées. Aucun tag `mobile-money-corpus:2698530f...` (production) ni `mobile-money-corpus:8f688e8d...` (rollback G8.5-R) n’est candidat.

## 5. Dépendances et traitements actifs

- Les conteneurs G2 actifs exécutent encore l’application, PostgreSQL, MinIO et possèdent au moins une connexion PostgreSQL idle; ils sont conservés.
- Les remédiations D1/D2/D3 exécutent encore app, PostgreSQL et MinIO depuis trois jours; elles sont conservées.
- G8.8 exécute quatre processus PostgreSQL/MinIO depuis le 13 octobre et reste ambigu sans labels; il est conservé.
- Les groupes G4/G5/G9-R3 proposés sont tous arrêtés; leurs réseaux sont vides.
- Aucun candidat proposé n’est sur `frontend`, `backend` de production, `mobile_money_corpus_dev_internal` ou `infra-network`.

## 6. Ressources protégées

Conteneurs :

```text
mobile_money_corpus_manager_v0_1-app-1
mobile_money_corpus_manager_v0_1-db-1
mobile_money_corpus_manager_v0_1-minio-1
mobile_money_corpus_manager_dev-app-1
mobile_money_corpus_manager_dev-db-1
mobile_money_corpus_manager_dev-minio-1
mobile_money_corpus_manager_g8_5_r-app
traefik, crowdsec, beszel, beszel-agent, vaultwarden, superset-db-light-1,
pgadmin, postgres, bentopdf, it-tools
```

Volumes :

```text
mobile_money_corpus_manager_v0_1_pgdata
mobile_money_corpus_manager_v0_1_miniodata
mobile_money_corpus_manager_v0_1_tmpaudio
mobile_money_corpus_dev_postgres_data
mobile_money_corpus_dev_minio_data
postgres_postgres_data
postgres_pgadmin_data
superset_db_home_light
```

Réseaux : `frontend`, `mobile_money_corpus_manager_v0_1_backend`, `mobile_money_corpus_dev_internal`, `infra-network`, `superset_default`, ainsi que les réseaux des applications protégées. Les fichiers Compose de production, la configuration Traefik et les sauvegardes restent inchangés.

## 7. Procédure d’exécution appliquée

Exécuter uniquement les groupes explicitement approuvés, un à la fois :

1. Capturer de nouveau `/health`, `/ready`, `docker ps`, les volumes, réseaux, `free -h` et `df -h`.
2. Arrêter/supprimer les conteneurs du groupe approuvé par leurs noms exacts.
3. Vérifier que production, développement, Traefik et les applications protégées restent inchangés.
4. Supprimer les volumes nommés de ce groupe uniquement.
5. Supprimer son réseau vide uniquement.
6. Supprimer les images candidates par ID complet, après vérification qu’aucun conteneur ne les référence.
7. Refaire les contrôles et comparer `docker system df -v`, `free -h` et `df -h`.

Interdictions : `docker system prune -a --volumes`, `docker volume prune`, suppression globale par préfixe, `docker compose down` sur production/dev ou rollback, et suppression de toute ressource sans nom/ID dans le manifeste.

## 8. Exécution et validation finale

### Ressources effectivement supprimées

| Campagne | Conteneurs | Volumes | Réseau | Images |
|---|---:|---:|---:|---:|
| `g4-preprod` | 11 | 5 | 1 | 6 |
| `g5-validation` | 8 | 5 | 1 | 5 |
| `g9-r3-test` | 7 | 5 | 1 | 4 |
| **Total** | **26** | **15** | **3** | **15** |

Les noms, IDs courts des conteneurs, noms des volumes, réseaux et IDs complets des images supprimés sont ceux du manifeste des sections 4.1 à 4.6. Les vérifications avant chaque campagne ont confirmé les labels Compose, l’état `exited`, les montages attendus, les réseaux vides et l’absence de référence protégée. Chaque campagne a été contrôlée avant passage à la suivante.

### Contrôles après chaque campagne et finaux

- Production : app, PostgreSQL et MinIO toujours `running/healthy`; IDs et image de production inchangés.
- Développement : app, PostgreSQL et MinIO toujours `running/healthy`; volumes de développement présents.
- Rollback G8.5-R : conteneur présent, toujours `exited`, image `mobile_money_corpus_manager_g8_5_r:8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6` et volume `mobile_money_corpus_manager_v0_1_tmpaudio` conservés.
- Services protégés : Traefik, CrowdSec, Beszel, Vaultwarden, Superset, pgAdmin, PostgreSQL global, BentoPDF et IT Tools toujours présents et `running`.
- Campagnes exclues : G2 (`10` conteneurs actifs), remédiations D/D1/D2/D3 (`10` conteneurs actifs) et G8.8 (`4` conteneurs actifs) conservées.
- Résidu candidat : aucun conteneur, volume, réseau ou tag d’image des trois campagnes supprimées ne subsiste.
- HTTPS : `https://corpus-moore.bencoherolab.com/health` et `/ready` HTTP 200.
- Ports : `22`, `80`, `443`, `5432` et `8090` inchangés; aucune modification de Traefik ou des règles de sécurité.

### Gains mesurés

| Mesure | Avant | Après | Variation |
|---|---:|---:|---:|
| Conteneurs Docker | 85 | 59 | -26 |
| Conteneurs actifs | 40 | 40 | 0 |
| Images uniques | 91 | 76 | -15 |
| Volumes | 81 | 66 | -15 |
| Réseaux | 20 | 17 | -3 |
| Taille logique volumes | 2.228 GB | 1.866 GB | environ -362 MB |
| Taille logique conteneurs | 35.38 MB | 33.19 MB | -2.19 MB |
| Taille logique images | 16.28 GB | 16.27 GB | environ -0.01 GB |
| Build cache | 15.58 GB | 15.58 GB | 0 |

La taille des images a peu diminué car les couches sont partagées avec d’autres images conservées. `free -h` reste à environ 6.1 GiB disponibles avant et après; aucun gain mémoire mesurable n’est revendiqué. `df -h /` reste arrondi à 85 GB disponibles; l’usage affiché passe de 109 à 108 GB.

## 9. Anomalies et opérations restantes

- Les ressources G2, remédiations, P0A2, G8.8, F5A2/F5A3 et autres campagnes restent présentes; elles nécessitent une revue séparée ou une preuve de propriétaire avant toute suppression.
- Aucune anomalie bloquante n’a été observée.
- La seconde vague éventuelle reste hors autorisation et hors périmètre.

## Statut de clôture

La première vague autorisée est **CLOSED/PASS**. Les ressources protégées et les campagnes exclues restent conservées; aucune suppression supplémentaire n’est autorisée sans un nouveau manifeste et une nouvelle approbation.

