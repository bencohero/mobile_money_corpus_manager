# G10 — Docker Cleanup Wave 2 Manifest

**Serveur :** `vmi3474447`  
**Projet :** Mobile Money Corpus Manager  
**Date de l’audit :** 2026-10-14  
**Statut :** **AUDIT COMPLET — EN ATTENTE D’APPROBATION**  
**Exécution destructive :** aucune. Aucun conteneur, volume, réseau ou image n’a été arrêté ou supprimé pendant cet audit.

## 1. Périmètre et méthode

Inventaire reproductible réalisé en lecture seule avec :

- `docker ps -a`
- `docker compose ls -a`
- `docker system df -v`
- `docker volume ls`
- `docker network ls`
- `docker inspect`, `docker stats --no-stream`, `docker top`
- inspection des labels Compose, montages, réseaux, commandes et politiques de redémarrage
- contrôle interne des endpoints `/health` et `/ready` des applications de test actives
- inspection read-only des processus PostgreSQL et des buckets MinIO, sans exposer de secret

État global observé : **59 conteneurs**, **40 actifs**, **66 volumes**, **17 réseaux**, **76 images**. Ces chiffres constituent le point de référence de l’audit G10.

Mesures VPS observées :

| Mesure | Valeur audit |
|---|---:|
| Mémoire totale | 11 GiB |
| Mémoire disponible | environ 6,1 GiB |
| Swap | aucune |
| Disque racine | 193 GiB |
| Disque utilisé / libre | 108 GiB / 85 GiB |
| Disque utilisé | 57 % |
| Images Docker | 16,27 GiB logiques, dont environ 8,98 GiB signalés reclaimable |
| Volumes Docker | 1,866 GiB logiques, dont environ 836 MiB signalés reclaimable |
| Build cache | 15,58 GiB, dont environ 10,61 GiB signalés reclaimable |

Les valeurs « reclaimable » de Docker ne sont **pas** une autorisation de suppression et ne constituent pas une estimation de gain acquis.

## 2. Ressources protégées

Les ressources suivantes sont exclues sans exception :

- projet Compose `mobile_money_corpus_manager_v0_1`, son application, PostgreSQL, MinIO et volumes ;
- projet `mobile_money_corpus_manager_dev`, son application, PostgreSQL, MinIO et volumes ;
- conteneur et image de rollback G8.5-R :
  `mobile_money_corpus_manager_g8_5_r-app` (`f2eb5a50ac00...`) ;
- volumes de production : `mobile_money_corpus_manager_v0_1_pgdata`, `mobile_money_corpus_manager_v0_1_miniodata`, `mobile_money_corpus_manager_v0_1_tmpaudio` ;
- volumes de développement : `mobile_money_corpus_dev_postgres_data`, `mobile_money_corpus_dev_minio_data` ;
- sauvegardes sous `/home/sangouman/mobile-money-corpus-backups/` ;
- Traefik, CrowdSec, Beszel, Vaultwarden, Superset, pgAdmin, PostgreSQL global, BentoPDF et IT Tools ;
- réseaux `frontend`, backend de production, réseau interne de développement, `infra-network`, `superset_default` et tout réseau partagé ;
- configuration Compose de production, configuration Traefik, règles de pare-feu et démon Docker.

Aucun de ces éléments n’a été modifié.

## 3. Classification synthétique

| Campagne / ressource | État | Classification | Motif principal |
|---|---|---|---|
| G2 clean | 6 actifs | À INVESTIGUER | traitements actifs, connexions PostgreSQL, données MinIO, propriétaire Compose connu mais usage actuel non clôturé |
| G2 migration | 4 actifs, 1 arrêté | À INVESTIGUER | outils et services actifs, volumes de migration, dépendances avec P0A2 |
| remediation-d | 1 actif, 1 arrêté, 1 créé | À INVESTIGUER | réseau et volumes P0A2 partagés avec d’autres campagnes |
| remediation-d1 | 3 actifs | À INVESTIGUER | traitements actifs et réseau partagé avec D3 |
| remediation-d2 | 3 actifs | À INVESTIGUER | traitements actifs, données MinIO et réseau dédié encore actif |
| remediation-d3 | 3 actifs | À INVESTIGUER | traitements actifs et réseau partagé avec D1 |
| G8.8 source/restore | 4 actifs, sans labels Compose | À INVESTIGUER | propriétaire absent, restauration G8.8/G9-R2 possible, données source et restore présentes |
| P0A2 | arrêté/créé | À INVESTIGUER | volumes, réseau et backup montés par d’autres campagnes |
| F5A2 | arrêté, sans labels | À INVESTIGUER | campagne historique, propriétaire et politique de conservation non prouvés |
| F5A3 | arrêté, sans labels | À INVESTIGUER | image candidate et artefacts de validation/rollback à distinguer |
| volumes/images historiques isolés | variables | À INVESTIGUER | absence de preuve nominative suffisante ou besoin de rétention à confirmer |

**Conclusion de classification : aucune ressource n’est déclarée SUPPRIMABLE dans ce manifeste.**  
Les éléments ci-dessous sont des **candidats conditionnels** soumis à une validation ultérieure, jamais des suppressions autorisées par le présent document.

## 4. Inventaire nominatif des campagnes

### 4.1 G2 clean

**Propriétaire identifié :** `docker-compose.test.yml`, `docker-compose.e2-migration.yml`, `G2_DOCKER_OVERRIDE.yml`.  
**Projet Compose :** `g2-clean`.  
**Réseau :** `g2-migration-network`, ID court `953a8a21aa3f`.  
**État :** 6 conteneurs actifs.

| Conteneur | ID complet | Image | Montages / dépendances |
|---|---|---|---|
| `g2-clean-app-test-1` | `78d0110b3f58a2d0c3f768d68ff87e513895786f754244398e3ef86b6d76a716` | `g2-clean-app-test` | aucun volume ; réseau G2 |
| `g2-clean-tools-1` | `cf8576ad07a3c2d4cc85322b660b0d9c765fe08990e00a56e3a6851a2c83a746` | `g2-clean-tools` | `g2-migration-backup` → `/backup`; volume anonyme → PostgreSQL |
| `g2-clean-db-test-1` | `d6cd1c0dd3c4bd05855d92fe18d37f2c28e1216e60d99b63eb21426cded531d5` | `postgres:16-alpine` | `g2-migration-pgdata` |
| `g2-clean-db-restore-1` | `fac407b8989f079492865a6e615f4f08dbcd008ab284df1b1b8576085c57493d` | `postgres:16-alpine` | `g2-migration-restore-pgdata` |
| `g2-clean-minio-test-1` | `b522e4920de69ce7af6589d4b794818fe85a2ee762471b091b30ae22909fac7e` | `minio` | `g2-migration-miniodata` |
| `g2-clean-minio-restore-1` | `f6068da1b079805527aa29d403ba215358a74b5af6bfa995ea65526cfa2e5f54` | `minio` | `g2-migration-restore-miniodata` |

Données observées : bucket `p0a2-test-bucket` côté MinIO de test. Deux connexions PostgreSQL idle provenaient de l’application. Mémoire instantanée observée : environ **626 MiB** pour le groupe. Les volumes G2 connus représentent environ **174 MiB** logiques, hors données anonymes et éléments partagés.

**Risque :** arrêter ce groupe interromprait un service de test actif et pourrait invalider une migration/restauration G2 encore utilisée.

### 4.2 G2 migration

**Propriétaire identifié :** mêmes fichiers Compose G2 et scripts/docs de migration.  
**Projet Compose :** `g2-migration`.  
**Réseau :** `mobile-money-corpus-e2-migration`, ID court `a8b5e172fc20`.  
**État :** 4 actifs, 1 arrêté.

| Conteneur | ID complet | État | Montages / dépendances |
|---|---|---|---|
| `g2-migration-tools-1` | `f3e78dba99738d096c7eb8051d8a793c73c1ac95b9be1999e38a1fc397e5d1fb` | actif | `mobile-money-corpus-p0a2-test-backup` → `/backup`; volume anonyme PostgreSQL |
| `g2-migration-db-restore-1` | `9b260df4d3663a037721c02834475057872c6a207a3f0225106aa892fa7d53b2` | arrêté | `mobile-money-corpus-p0a2-test-restore-pgdata` |
| `g2-migration-db-test-1` | `d556a041e10399b2354f1f96c3058ffc12ad0fb849ffcdbce5adb100c7e1dfbf` | actif | `mobile-money-corpus-e2-migration-pgdata` |
| `g2-migration-minio-test-1` | `3b8f9118150a44af446c5c96abeef5dca4e8ae461b9d39a3c01aa4d9041f88e0` | actif | `mobile-money-corpus-e2-migration-miniodata` |
| `g2-migration-minio-restore-1` | `9cded0d102bd505e2beb9cf57584b755a109ae38592e827565474465cf1107b2` | actif | `mobile-money-corpus-p0a2-test-restore-miniodata` |

Mémoire instantanée observée : environ **477 MiB**. Aucun client PostgreSQL applicatif n’a été observé lors du contrôle ponctuel, mais les processus PostgreSQL/MinIO et l’outil de migration étaient actifs. Cela ne prouve pas l’inutilité.

### 4.3 Remédiation D, D1, D2 et D3

**Propriétaires Compose :**

- D : `docker-compose.d.test.yml`
- D1 : `docker-compose.test.yml` + `docker-compose.c1.test.yml`
- D2 : `docker-compose.test.yml` + `docker-compose.c1b.test.yml`
- D3 : `docker-compose.test.yml` + `docker-compose.c1.test.yml`

#### D base

| Conteneur | ID complet | État | Ressource |
|---|---|---|---|
| `mobile-money-corpus-remediation-d-app-test-1` | `c715408a0ff2b9bbc8c42447050601cc9860eb0d690adf427efd29f768c2ed56` | créé | réseau `mobile-money-corpus-p0a2-test` |
| `mobile-money-corpus-remediation-d-db-test-1` | `389bb236ee32c212e556095ae145cbf401a90f9884a2295ac6b15dd0b0428b0c` | arrêté | volume `mobile-money-corpus-p0a2-test-pgdata` |
| `mobile-money-corpus-remediation-d-minio-test-1` | `d366d43fc0b9ecc1d2fa7ada90faef43f787aff5dd68d5b1d53d9d7718840ee5` | actif/healthy | volume `mobile-money-corpus-p0a2-test-miniodata` |

Le réseau `mobile-money-corpus-p0a2-test` (ID `d954651b840e`) et les volumes `...-pgdata` / `...-miniodata` sont également utilisés ou référencés par P0A2. Ils sont donc partagés et exclus.

#### D1

| Conteneur | ID complet | État | Volume |
|---|---|---|---|
| `mobile-money-corpus-remediation-d1-app-test-1` | `27567e11f3fd93dfce1fee94b0f601215b1f8ebe27c2b4709f13fafcaeef01bc` | actif/healthy | aucun |
| `mobile-money-corpus-remediation-d1-db-test-1` | `6ce057ce3a22f4a7e1fe2531b07c591166f58260488dff6b1ed880a68494d9c8` | actif/healthy | `mobile-money-corpus-remediation-d1_c1-test-pgdata` |
| `mobile-money-corpus-remediation-d1-minio-test-1` | `69c1fa41c30f44c5e09fab5df0140f29b0d77d1427d63644bc0e81823064eda5` | actif/healthy | `mobile-money-corpus-remediation-d1_c1-test-miniodata` |

Réseau partagé avec D3 : `mobile-money-corpus-c1-test`, ID `90088f2fbfd8`. Bucket observé : `c1-test-bucket`. Une activité de connexions PostgreSQL idle a été observée. Mémoire instantanée : environ **369 MiB**.

#### D2

| Conteneur | ID complet | État | Volume |
|---|---|---|---|
| `mobile-money-corpus-remediation-d2-app-test-1` | `8ae38970ef0e950cd2c94aa7eea4f91fb2a047d40ced28c5cf0aee66a74e036f` | actif/healthy | aucun |
| `mobile-money-corpus-remediation-d2-db-test-1` | `2110a0104b713b53ac5fb7af08808471793c7f1c0cb22a8c06f6c7334ae8cbd0` | actif/healthy | `mobile-money-corpus-remediation-d2_c1b-test-pgdata` |
| `mobile-money-corpus-remediation-d2-minio-test-1` | `41dbb7d7d84d55c9e250f05144641b4f2f7fe2b242f90aa6ef880ab7fdb2435c` | actif/healthy | `mobile-money-corpus-remediation-d2_c1b-test-miniodata` |

Réseau : `mobile-money-corpus-c1b-test`, ID `1b476a25a823`, actuellement dédié à D2 mais toujours actif. Bucket : `c1b-test-bucket`. Connexion PostgreSQL idle observée. Mémoire instantanée : environ **347 MiB**.

#### D3

| Conteneur | ID complet | État | Volume |
|---|---|---|---|
| `mobile-money-corpus-remediation-d3-app-test-1` | `5138c3209ac5410cc094ec174b665dda241cdbd716a6f5d626766198f81bd4c2` | actif/healthy | aucun |
| `mobile-money-corpus-remediation-d3-db-test-1` | `1f8e2c6ab9d02c8d2a636852c5d72a8288d46e955f8e9bd72ecff62a22ad6c5` | actif/healthy | `mobile-money-corpus-remediation-d3_c1-test-pgdata` |
| `mobile-money-corpus-remediation-d3-minio-test-1` | `8ea38ad6f4daecc266a438d7ed9b64c0b313e02e61fd1f97ca9858e75d9e864d` | actif/healthy | `mobile-money-corpus-remediation-d3_c1-test-miniodata` |

Réseau partagé avec D1 : `mobile-money-corpus-c1-test`, ID `90088f2fbfd8`. Bucket : `c1-test-bucket`. Mémoire instantanée : environ **344 MiB**.

**Risque commun D1/D3 :** supprimer le réseau ou le traiter par projet Compose pourrait affecter l’autre campagne. Les deux campagnes doivent être analysées et approuvées ensemble, ou le réseau doit être conservé.

### 4.4 G8.8 source/restore

**Propriétaire Compose :** non identifié. Les documents G8.8/G9-R2 mentionnent une restauration isolée et une validation source/restore.  
**Réseau :** `g88-a-isolated`, ID `3c25419319a0`.  
**Labels Compose :** absents.  
**État :** 4 conteneurs actifs, créés le 2026-10-13.

| Conteneur | ID complet | Image | Volume anonyme |
|---|---|---|---|
| `g88-a-source-db` | `682fba70829226fa33c1927a9cd2ff3df2b29f6d182a72caf220c6e28cd4892d` | `postgres:16` | `ef2b0c74edb497d2c51dbef793178220ebb45f92ecb0a746f94cf169ce2cdf3e` |
| `g88-a-source-minio` | `714bbb39c875babe637bb87bb57b94bf35107843fbc1dfd5dd4f4253fcd2752a` | `minio` | `82546146f389888ec434a84b9718ead10cb1713bb7380590e2b07ad35db8e6dd` |
| `g88-a-restore-db` | `05eb76a2e77581820ad4f5f04102b5798f0c3bdac018124db1e13bf466ab1976` | `postgres:16` | `ca86ceb2d54c0f91690f94f78d2b9f05bc1b84403b2cd7b9ac9fe9543009ea66` |
| `g88-a-restore-minio` | `b3b9c368ba930d5b08cf2a91b3b6e5582d0f51ddfda112089a67e9b4e0216593` | `minio` | `b46e64620a5c1fd309142c03f418d5042485dffa8d76d4cb3d9bf4bca5e00877` |

Buckets observés : source `synthetic-bucket`; restore `mobile-money-corpus` et `synthetic-bucket`. Aucun client PostgreSQL n’a été observé lors du contrôle ponctuel, mais les processus étaient actifs. Mémoire instantanée : environ **532 MiB**.

**Classification : À INVESTIGUER obligatoire.** L’absence de labels et de connexions actives ne prouve ni la fin de la campagne ni l’autorisation de supprimer les données.

### 4.5 P0A2

**Projet Compose :** `mobile-money-corpus-p0a2-test`, `docker-compose.test.yml`.  
**État :** conteneurs arrêtés ou créés.

| Conteneur | ID court relevé | État |
|---|---|---|
| `mobile-money-corpus-p0a2-test-db-restore-1` | `fb61bacdf40ee58b07193836e48c860543c828a5cc3aaae4768ebc06145c0ced` | arrêté |
| `mobile-money-corpus-p0a2-test-db-test-1` | `49c8e6f1332bd63a8821652220da4c6c22f8fb1ae8258a665da2fe320beb29e0` | arrêté, code 1 |
| `mobile-money-corpus-p0a2-test-minio-restore-1` | `21aa02996f87ab20fd011ed04ea7b7e3b5f4d866d2a580ba022b1874148df393` | arrêté |
| `mobile-money-corpus-p0a2-test-minio-test-1` | `d16b1d14c176f0090a09f65f0b4412bb667863670cb7c1b377efa1455da37f54` | arrêté |
| `mobile-money-corpus-p0a2-test-tools-1` | `cfca989de1fa587768814abc761b2cf1f3db793af6d9ac8062efb6f4ba6c64db` | créé |

Ressources : réseau `mobile-money-corpus-p0a2-test` (`d954651b840e`) ; volumes `mobile-money-corpus-p0a2-test-pgdata`, `mobile-money-corpus-p0a2-test-miniodata`, `mobile-money-corpus-p0a2-test-backup`, `mobile-money-corpus-p0a2-test-restore-pgdata`, `mobile-money-corpus-p0a2-test-restore-miniodata`.

Les volumes principaux et le réseau ont des références Docker multiples et sont montés/référencés par D base et/ou G2. Classification : **À INVESTIGUER**. Le volume `...-pgdata` représentait environ 84,86 MiB logiques avec deux références ; le volume MinIO environ 1,16 MiB avec deux références.

### 4.6 F5A2 et F5A3

Ressources historiques sans labels Compose, toutes arrêtées.

- F5A2 : `f5a2-db` (`d168404a6b8fe2d441c69c19cd0adbf19f01f7672e5a7a821c4b9cc7ba545cae`), `f5a2-minio` (`caf6537d3a7c7a7f2c62bb54c15fae16974475b647919fcd6631aeb138dc7bfe`), `f5a2-restore-db` (`debbb21c4c1dbdcf794ab7f1c465743b5236c5342b5248627abeef68e44b0b7a`), `f5a2-restore-minio` (`ec93a60ca56433255f984f4a30607fd5b96105ee7fffcfee46b5a4a83c5a4735`). Réseau vide `f5a2-isolated` (`17b12e2f5cf4`).
- F5A3 : `f5a3-app-a` (`89d43d197dcf3742879ef1a7d7965a840597bae8a5f6c4a8d4e82883218240de`), `f5a3-app-b` (`43fa99dcba268bbca485589d009a023b2a8ee1441c980e21f5c68ee75f723215`), `f5a3-db` (`23a66c59ef78647eef8f97ec2cfcff597b30a16f0da2c613326ea9f9bfc197d9`), `f5a3-minio` (`f6d246c64fb4f0b297b2d33e417812e95a30b1c1cac9d8b481110e2678da02ce`), `f5a3-restore-db` (`6c8e80e0bf98dd4ef56e890d68c2cbbb6358fabfa4984ad83bb2efba3f3bccd9`), `f5a3-restore-minio` (`e41c12e35a5aef40e04fb4d886c589d60f91cabbbd1b6670c3cd2bf5438c1f4f`). Réseau vide `f5a3-isolated` (`b0259385a441`).
- Image candidate F5A3 : `f5a3-candidate:0005-freeze`, digest `sha256:170270493de28c7e4fffbf1cd396122680d4eb2684249edd8fd7e166be4493e2`, taille logique environ 1,09 GiB.

La documentation F5 indique des données synthétiques et des validations candidate/rollback, mais aucun propriétaire opérationnel actuel n’a été démontré dans Docker. Classification : **À INVESTIGUER**, notamment l’image candidate et la rétention rollback.

## 5. Images candidates

Les images associées aux familles G2, P0A2 et D ont été relevées par nom et digest lors de l’audit Docker. Elles doivent être revalidées par digest complet immédiatement avant toute suppression, car une image peut être partagée par un conteneur arrêté, une release conservée ou un rollback.

Images candidates observées :

- `g2-clean-app-test`, `g2-clean-test`, `g2-clean-tools`, `g2-migration-tools` ;
- `mobile-money-corpus-p0a2-test-app`, `mobile-money-corpus-p0a2-test-test`, `mobile-money-corpus-p0a2-test-tools` ;
- images D/D1/D2/D3 nommées `mobile-money-corpus-remediation-*` ;
- `f5a3-candidate:0005-freeze` — digest complet ci-dessus.

Aucune image ne sera supprimée au titre de ce manifeste. Les images de production et rollback sont explicitement exclues, même si elles paraissent non utilisées à l’instant du contrôle.

Digests relevés pendant l’audit :

| Image | Digest | Taille logique |
|---|---|---:|
| `g2-clean-app-test:latest` | `sha256:7d273cfe790815e4f8209c399a01aa352b1f787fd978c3ec5df4692f7fe30514` | 269,6 MB |
| `g2-clean-test:latest` | `sha256:66196c8168ed604350819c62d852f6f719220d4db226c5bfa551bb6fc6d3cf16` | 269,6 MB |
| `g2-clean-tools:latest` | `sha256:d388ace5c1c6ef1afecec9481995c32c0baf2fa62917c1a5bffb55e6edecda6c` | 129,6 MB |
| `g2-migration-tools:latest` | `sha256:cae1cd0bd8f699fa4a3f05774f22a9df2fc845ae490e4ac8067f3bf5f923b698` | 129,6 MB |
| `mobile-money-corpus-p0a2-test-app-test:latest` | `sha256:207f8ab687aa79ccfc1fbdf66fba4d52790ee5e699357f29b5c6bbf5616c1bf6` | 269,9 MB |
| `mobile-money-corpus-p0a2-test-test:latest` | `sha256:d6186e26b1325e52159e33fdb97230519af0007db4541c20be46f4b6ae2f2228` | 269,9 MB |
| `mobile-money-corpus-p0a2-test-tools:latest` | `sha256:80e75f700978db4ea1c977dcee48eb9e4fe5eb8bb546422b053af675ae6e6779` | 129,6 MB |
| `mobile-money-corpus-remediation-d-app-test:latest` | `sha256:2a1056d2b85810ae3da281cf013973b6ad5aea5beeabf840920e6cc43692a9df` | 274,9 MB |
| `mobile-money-corpus-remediation-d-test:latest` | `sha256:2473356604e8e4a3eddf84487073023019530bdcb4f5523e6f8f07bf80c86a4c` | 274,9 MB |
| `mobile-money-corpus-remediation-d-tools:latest` | `sha256:fa3facdc37d3a9adf5e6f5c1df12e5aa8227545e5dfd00794162eba7fb8468de` | 129,6 MB |
| `mobile-money-corpus-remediation-d1-app-test:latest` | `sha256:06c1c80ea4993fdc58a1974482d38d2aabc34022bfaa476fd6e4192d950f9498` | 274,9 MB |
| `mobile-money-corpus-remediation-d1-test:latest` | `sha256:33a7945f16a56a86498afbbe72a495a38cf2daac0d99851905ce9480d76288f0` | 274,9 MB |
| `mobile-money-corpus-remediation-d1-tools:latest` | `sha256:05e49863f4865e795dd4c5c0e9dc89b431404113be8b18545058f24d443647fd` | 129,6 MB |
| `mobile-money-corpus-remediation-d2-app-test:latest` | `sha256:2ec372336f6a911f0016f69b932df806bf42dcbfb8794df651ca2e389e0e8a79` | 274,9 MB |
| `mobile-money-corpus-remediation-d2-test:latest` | `sha256:099564b63f3e9949db77c25e1e84e9a66c57fe08708a22448a5dbf30f39fce9d` | 274,9 MB |
| `mobile-money-corpus-remediation-d2-tools:latest` | `sha256:720426e03e183947846e9c9eeb9afd61f7f6464e26e65e91fef6b90a06b1860d` | 129,6 MB |
| `mobile-money-corpus-remediation-d3-app-test:latest` | `sha256:58343e99e23424933e988ec6d99d854206a0a04a267a0e03980b74f24c4a677b` | 274,9 MB |
| `mobile-money-corpus-remediation-d3-test:latest` | `sha256:56275332f85fa24fe755cbfe0e5188eeae917ec87e6e1251abe3e788330d3ae1` | 274,9 MB |
| `mobile-money-corpus-remediation-d3-tools:latest` | `sha256:29f1aff5550dee5b16429d34bde458a65b0ca74279450a3bf77fb1f1215e38f5` | 129,6 MB |
| `f5a3-candidate:0005-freeze` | `sha256:170270493de28c7e4fffbf1cd396122680d4eb2684249edd8fd7e166be4493e2` | 274,9 MB |

## 6. Dépendances et contrôles constatés

- G2 clean et G2 migration ont des processus actifs ; les conteneurs outils utilisent des volumes de backup/restauration.
- D base partage le réseau et les volumes P0A2.
- D1 et D3 partagent le réseau `mobile-money-corpus-c1-test`.
- P0A2 présente des références de volumes multiples.
- G8.8 est sans labels Compose et reste propriétaire-incertain.
- Les données MinIO observées portent des noms de buckets de test ou de restauration ; cela ne suffit pas à établir la date de fin ni l’autorisation de suppression.
- Aucun traitement système ou job de sauvegarde externe n’a été arrêté ou modifié.
- Les services de production, développement et rollback étaient présents et n’ont pas été touchés.
- Les ports publics et les règles de sécurité n’ont pas été modifiés.
- Une tentative de requête PostgreSQL read-only mal échappée a produit une erreur de syntaxe dans un journal de test ; aucune écriture ni modification de données n’a été effectuée. Les contrôles read-only corrigés ont ensuite abouti.

## 7. Estimation non contractuelle des gains

Ces chiffres sont des observations instantanées, pas des gains garantis :

| Groupe | RAM instantanée observée | Données logiques connues | Interprétation |
|---|---:|---:|---|
| G2 clean + migration | ~1,10 GiB | ~174 MiB de volumes identifiés, plus éléments partagés/anonymes | non récupérable sans clôture et séparation des dépendances |
| Remédiation D/D1/D2/D3 | ~1,30 GiB | au moins ~0,15 GiB pour les volumes D actifs ; P0A2 partagé exclu | D1/D3 partagent un réseau |
| G8.8 | ~532 MiB | tailles des volumes anonymes à confirmer | propriétaire et usage incertains |
| F5A2/F5A3 | non pertinent à l’arrêt | pas de volume Docker candidat confirmé pour F5A2 ; image F5A3 ~1,09 GiB | conservation rollback à confirmer |

Le gain réel devra être mesuré après approbation, par campagne, avec `docker system df -v`, `free -h` et `df -h`. Aucun build cache ou nettoyage global n’est proposé.

## 8. Ordre d’exécution proposé après approbation

1. Obtenir une confirmation nominative du propriétaire pour chaque campagne classée À INVESTIGUER.
2. Capturer l’état initial VPS, production, développement, rollback et applications protégées.
3. Traiter une seule campagne à la fois.
4. Pour G2, dissocier explicitement `g2-clean` de `g2-migration` et résoudre les références P0A2 avant tout arrêt.
5. Pour D1/D3, traiter le réseau partagé ensemble ou conserver le réseau.
6. Pour chaque campagne approuvée : arrêter uniquement les conteneurs nominativement autorisés, vérifier production/dev/services protégés, puis supprimer les conteneurs.
7. Supprimer uniquement les volumes dont l’exclusivité est démontrée par `docker inspect` et les références Docker.
8. Supprimer un réseau seulement lorsqu’il est vide et exclusivement dédié.
9. Supprimer une image uniquement après vérification de son digest, de son absence de référence et de son exclusion des releases/rollback.
10. Mesurer les gains et interrompre immédiatement au premier contrôle en échec.

Interdictions maintenues : aucun `docker system prune`, `docker volume prune`, `docker compose down -v` non borné, suppression globale par préfixe, redémarrage Docker, modification Traefik ou pare-feu.

## 9. Décision

**G10 : AUDIT COMPLET — EN ATTENTE D’APPROBATION.**

Le présent manifeste ne constitue pas une autorisation de suppression. Toute vague ultérieure devra faire l’objet d’une approbation explicite des noms et identifiants exacts après résolution des éléments À INVESTIGUER.

