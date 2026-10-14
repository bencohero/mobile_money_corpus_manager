# G10.2 — Final Deletion Manifest

**Serveur :** `vmi3474447`  
**Date de gel du manifeste :** 2026-10-14T01:19:45+02:00  
**Statut :** **VALIDÉ POUR EXÉCUTION — LISTE FERMÉE**  
**Portée :** campagnes historiques autorisées G2, D/D1/D2/D3, P0A2, G8.8, F5A2 et F5A3 uniquement.

Ce manifeste a été recapturé après l’autorisation G10.2. Les identifiants ci-dessous sont ceux observés à l’instant du gel. Toute ressource dont l’ID, le montage, l’image ou l’état diverge avant son lot sera exclue et signalée.

Aucune ressource de production, de développement, de rollback, d’infrastructure partagée ou de sauvegarde n’est incluse.

## 1. Contrôles de pré-exécution

| Contrôle | Résultat |
|---|---|
| Hôte | `vmi3474447` |
| Conteneurs totaux / actifs | 59 / 40 |
| Volumes Docker | 66 |
| Réseaux Docker | 17 |
| Mémoire | 11 GiB total, ~6,1 GiB disponible, swap 0 |
| Disque racine | 193 GiB, 108 GiB utilisés, 85 GiB libres |
| Production app/db/minio | running, healthy |
| Développement app/db/minio | running, healthy |
| Production PostgreSQL | `pg_isready` accepte les connexions |
| Production MinIO | live probe réussie |
| Production HTTPS `/health` | HTTP 200 |
| Production HTTPS `/ready` | HTTP 200 |
| Sauvegardes VPS | présentes, archives `COMPLETE` observées jusqu’au 2026-10-13 |
| Rollback G8.5-R | présent, conteneur `f2eb5a50ac00...`, non inclus |
| Traefik/pare-feu/Docker | aucune modification prévue ou effectuée |

Le contrôle interne sans en-tête Host approuvé renvoie 400, conformément au TrustedHost de l’application ; le contrôle HTTPS avec le domaine approuvé renvoie 200 pour les deux endpoints.

## 2. Protections absolues exclues du manifeste

- `mobile_money_corpus_manager_v0_1-app-1` — `f95aaa8800990262dc4db554e41330ef7632cee0b893fba0576c1b1ec074de19`
- `mobile_money_corpus_manager_v0_1-db-1` — `43a9b5c91a6f46d9a713bb74c093a8e9cfd16fbf2b7079d01f3569b508e69e3a`
- `mobile_money_corpus_manager_v0_1-minio-1` — `5748cbd5292d682a4e0c76b79962ba76fc3cfc436fa8b7343d9aa88230fd38bf`
- `mobile_money_corpus_manager_dev-app-1`, `...-db-1`, `...-minio-1`
- `mobile_money_corpus_manager_g8_5_r-app` — `f2eb5a50ac00...`
- volumes `mobile_money_corpus_manager_v0_1_*`, `mobile_money_corpus_dev_*`, `postgres_*`, `superset_db_home_light`
- Traefik, CrowdSec, Beszel, Vaultwarden, Superset, pgAdmin, PostgreSQL global, BentoPDF, IT Tools
- réseaux `frontend`, `mobile_money_corpus_manager_v0_1_backend`, `mobile_money_corpus_dev_internal`, `infra-network`, `superset_default`
- sauvegardes sous `/home/sangouman/mobile-money-corpus-backups/`
- images de production, développement, rollback et images officielles partagées `postgres:16-alpine` / MinIO.

## 3. Lot F5A2 — suppression autorisée

Preuve : `F5A2_BACKUP_VALIDATION.md` documente des tests synthétiques avec `tmpfs`, sans volume Docker persistant. Les conteneurs sont arrêtés et le réseau est vide.

| Nom | ID complet | Image | État | Montage |
|---|---|---|---|---|
| `f5a2-db` | `d168404a6b8fe2d441c69c19cd0adbf19f01f7672e5a7a821c4b9cc7ba545cae` | `postgres:16-alpine` | exited | aucun |
| `f5a2-minio` | `caf6537d3a7c7a7f2c62bb54c15fae16974475b647919fcd6631aeb138dc7bfe` | MinIO officiel | exited | aucun |
| `f5a2-restore-db` | `debbb21c4c1dbdcf794ab7f1c465743b5236c5342b5248627abeef68e44b0b7a` | `postgres:16-alpine` | exited | aucun |
| `f5a2-restore-minio` | `ec93a60ca56433255f984f4a30607fd5b96105ee7fffcfee46b5a4a83c5a4735` | MinIO officiel | exited | aucun |

Réseau autorisé : `f5a2-isolated`, ID `17b12e2f5cf4`, vide et dédié.  
Volumes : aucun volume persistant F5A2 identifié.  
Images : conserver les images officielles.

Actions : supprimer les quatre conteneurs par ID, puis le réseau seulement après vérification qu’il reste vide.

## 4. Lot F5A3 — suppression autorisée

Preuves : validation de gel synthétique et rollback isolé dans les rapports F5A3/F5A4. La candidate est distincte de G8.5-R.

| Nom | ID complet | Image | État |
|---|---|---|---|
| `f5a3-app-a` | `89d43d197dcf3742879ef1a7d7965a840597bae8a5f6c4a8d4e82883218240de` | `f5a3-candidate:0005-freeze` | exited |
| `f5a3-app-b` | `43fa99dcba268bbca485589d009a023b2a8ee1441c980e21f5c68ee75f723215` | `f5a3-candidate:0005-freeze` | exited |
| `f5a3-db` | `23a66c59ef78647eef8f97ec2cfcff597b30a16f0da2c613326ea9f9bfc197d9` | `postgres:16-alpine` | exited |
| `f5a3-minio` | `f6d246c64fb4f0b297b2d33e417812e95a30b1c1cac9d8b481110e2678da02ce` | MinIO officiel | exited |
| `f5a3-restore-db` | `6c8e80e0bf98dd4ef56e890d68c2cbbb6358fabfa4984ad83bb2efba3f3bccd9` | `postgres:16-alpine` | exited |
| `f5a3-restore-minio` | `e41c12e35a5aef40e04fb4d886c589d60f91cabbbd1b6670c3cd2bf5438c1f4f` | MinIO officiel | exited |

Réseau : `f5a3-isolated`, ID `b0259385a441`, vide et dédié.  
Volumes : aucun volume persistant identifié.  
Image candidate à supprimer : `f5a3-candidate:0005-freeze@sha256:170270493de28c7e4fffbf1cd396122680d4eb2684249edd8fd7e166be4493e2`.  
G8.5-R n’utilise pas cette image et reste protégé.

Actions : supprimer les six conteneurs, le réseau vide, puis l’image candidate par digest après vérification de l’absence de références.

## 5. Lot D1/D3 — groupe de dépendances

Les conteneurs D1/D3 sont actifs et partagent le réseau `mobile-money-corpus-c1-test`. Les volumes PostgreSQL/MinIO sont distincts et dédiés.

### D1

| Nom | ID complet | Image | État | Volume |
|---|---|---|---|---|
| `mobile-money-corpus-remediation-d1-app-test-1` | `27567e11f3fd93dfce1fee94b0f601215b1f8ebe27c2b4709f13fafcaeef01bc` | remediation D1 app | running healthy | aucun |
| `mobile-money-corpus-remediation-d1-db-test-1` | `6ce057ce3a22f4a7e1fe2531b07c591166f58260488dff6b1ed880a68494d9c8` | `postgres:16-alpine` | running healthy | `mobile-money-corpus-remediation-d1_c1-test-pgdata` |
| `mobile-money-corpus-remediation-d1-minio-test-1` | `69c1fa41c30f44c5e09fab5df0140f29b0d77d1427d63644bc0e81823064eda5` | MinIO officiel | running healthy | `mobile-money-corpus-remediation-d1_c1-test-miniodata` |

### D3

| Nom | ID complet | Image | État | Volume |
|---|---|---|---|---|
| `mobile-money-corpus-remediation-d3-app-test-1` | `5138c3209ac5410cc094ec174b665dda241cdbd716a6f5d626766198f81bd4c2` | remediation D3 app | running healthy | aucun |
| `mobile-money-corpus-remediation-d3-db-test-1` | `1f8e2c6ab9d02c8d2a636852c5d72a8288d46e955f8e9bd72ecff62a22ad6c5` | `postgres:16-alpine` | running healthy | `mobile-money-corpus-remediation-d3_c1-test-pgdata` |
| `mobile-money-corpus-remediation-d3-minio-test-1` | `8ea38ad6f4daecc266a438d7ed9b64c0b313e02e61fd1f97ca9858e75d9e864d` | MinIO officiel | running healthy | `mobile-money-corpus-remediation-d3_c1-test-miniodata` |

Réseau partagé autorisé : `mobile-money-corpus-c1-test`, ID `90088f2fbfd8`.  
Données : campagnes C.1/D documentées comme validations de test ; autorisation opérateur reçue pour les données synthétiques.  
Volumes autorisés : les quatre volumes D1/D3 ci-dessus, uniquement après arrêt des six conteneurs et vérification des références.

Images dédiées à vérifier puis supprimer si non référencées : D1 app/test/tools et D3 app/test/tools aux digests du manifeste G10. Les images officielles sont conservées.

## 6. Lot D2

| Nom | ID complet | Image | État | Volume |
|---|---|---|---|---|
| `mobile-money-corpus-remediation-d2-app-test-1` | `8ae38970ef0e950cd2c94aa7eea4f91fb2a047d40ced28c5cf0aee66a74e036f` | remediation D2 app | running healthy | aucun |
| `mobile-money-corpus-remediation-d2-db-test-1` | `2110a0104b713b53ac5fb7af08808471793c7f1c0cb22a8c06f6c7334ae8cbd0` | `postgres:16-alpine` | running healthy | `mobile-money-corpus-remediation-d2_c1b-test-pgdata` |
| `mobile-money-corpus-remediation-d2-minio-test-1` | `41dbb7d7d84d55c9e250f05144641b4f2f7fe2b242f90aa6ef880ab7fdb2435c` | MinIO officiel | running healthy | `mobile-money-corpus-remediation-d2_c1b-test-miniodata` |

Réseau : `mobile-money-corpus-c1b-test`, ID `1b476a25a823`, dédié à D2.  
Volumes autorisés : les deux volumes D2 ci-dessus après vérification de référence.  
Images dédiées D2 à vérifier par digest puis supprimer si inutilisées.

## 7. Lot G2 + D base + P0A2

Ce lot est traité ensemble afin de retirer les consommateurs partagés avant les volumes.

### G2 clean

| Nom | ID complet | État |
|---|---|---|
| `g2-clean-app-test-1` | `78d0110b3f58a2d0c3f768d68ff87e513895786f754244398e3ef86b6d76a716` | running healthy |
| `g2-clean-tools-1` | `cf8576ad07a3c2d4cc85322b660b0d9c765fe08990e00a56e3a6851a2c83a746` | running |
| `g2-clean-db-test-1` | `d6cd1c0dd3c4bd05855d92fe18d37f2c28e1216e60d99b63eb21426cded531d5` | running healthy |
| `g2-clean-db-restore-1` | `fac407b8989f079492865a6e615f4f08dbcd008ab284df1b1b8576085c57493d` | running healthy |
| `g2-clean-minio-test-1` | `b522e4920de69ce7af6589d4b794818fe85a2ee762471b091b30ae22909fac7e` | running healthy |
| `g2-clean-minio-restore-1` | `f6068da1b079805527aa29d403ba215358a74b5af6bfa995ea65526cfa2e5f54` | running healthy |

Réseau : `g2-migration-network`, ID `953a8a21aa3f`. Volumes : `g2-migration-backup`, `g2-migration-pgdata`, `g2-migration-miniodata`, `g2-migration-restore-pgdata`, `g2-migration-restore-miniodata`.

### G2 migration

| Nom | ID complet | État |
|---|---|---|
| `g2-migration-tools-1` | `f3e78dba99738d096c7eb8051d8a793c73c1ac95b9be1999e38a1fc397e5d1fb` | running |
| `g2-migration-db-restore-1` | `9b260df4d3663a037721c02834475057872c6a207a3f0225106aa892fa7d53b2` | exited |
| `g2-migration-db-test-1` | `d556a041e10399b2354f1f96c3058ffc12ad0fb849ffcdbce5adb100c7e1dfbf` | running healthy |
| `g2-migration-minio-test-1` | `3b8f9118150a44af446c5c96abeef5dca4e8ae461b9d39a3c01aa4d9041f88e0` | running healthy |
| `g2-migration-minio-restore-1` | `9cded0d102bd505e2beb9cf57584b755a109ae38592e827565474465cf1107b2` | running healthy |

Réseau : `mobile-money-corpus-e2-migration`, ID `a8b5e172fc20`. Volumes : `mobile-money-corpus-e2-migration-pgdata`, `...-miniodata`, `...-backup`. Les outils G2 montent également `mobile-money-corpus-p0a2-test-backup` et `mobile-money-corpus-p0a2-test-restore-*`.

### D base

| Nom | ID complet | État | Ressource partagée |
|---|---|---|---|
| `mobile-money-corpus-remediation-d-app-test-1` | `c715408a0ff2b9bbc8c42447050601cc9860eb0d690adf427efd29f768c2ed56` | created | réseau P0A2 |
| `mobile-money-corpus-remediation-d-db-test-1` | `389bb236ee32c212e556095ae145cbf401a90f9884a2295ac6b15dd0b0428b0c` | exited | `mobile-money-corpus-p0a2-test-pgdata` |
| `mobile-money-corpus-remediation-d-minio-test-1` | `d366d43fc0b9ecc1d2fa7ada90faef43f787aff5dd68d5b1d53d9d7718840ee5` | running | `mobile-money-corpus-p0a2-test-miniodata` |

### P0A2

| Nom | ID complet | État | Montage principal |
|---|---|---|---|
| `mobile-money-corpus-p0a2-test-db-restore-1` | `fb61bacdf40ee58b07193836e48c860543c828a5cc3aaae4768ebc06145c0ced` | exited | `...-restore-pgdata` |
| `mobile-money-corpus-p0a2-test-db-test-1` | `49c8e6f1332bd63a8821652220da4c6c22f8fb1ae8258a665da2fe320beb29e0` | exited | `...-pgdata` |
| `mobile-money-corpus-p0a2-test-minio-restore-1` | `21aa02996f87ab20fd011ed04ea7b7e3b5f4d866d2a580ba022b1874148df393` | exited | `...-restore-miniodata` |
| `mobile-money-corpus-p0a2-test-minio-test-1` | `d16b1d14c176f0090a09f65f0b4412bb667863670cb7c1b377efa1455da37f54` | exited | `...-miniodata` |
| `mobile-money-corpus-p0a2-test-tools-1` | `cfca989de1fa587768814abc761b2cf1f3db793af6d9ac8062efb6f4ba6c64db` | created | backup + volume anonyme |

Réseau partagé à retirer en dernier : `mobile-money-corpus-p0a2-test`, ID `d954651b840e`.

Volumes de ce groupe autorisés après retrait de tous les consommateurs :

- `mobile-money-corpus-p0a2-test-pgdata`
- `mobile-money-corpus-p0a2-test-miniodata`
- `mobile-money-corpus-p0a2-test-backup`
- `mobile-money-corpus-p0a2-test-restore-pgdata`
- `mobile-money-corpus-p0a2-test-restore-miniodata`
- volume anonyme `08edbfabc88f22cabb08fee24a5a910c55e74c9551b4fa8a595c30c919f58a8c`, uniquement s’il reste exclusivement attaché à `mobile-money-corpus-p0a2-test-tools-1`.

Les volumes historiques `mobile-money-corpus-p0a2-test_c1-*`, `remediation-c1_*`, `remediation-c1b_*`, G3, E1 et D4 non montés par les conteneurs de ce manifeste sont exclus par prudence.

## 8. Lot G8.8

Preuves : G8.8-A/B et G9-R2 confirment que les cibles sont isolées ; l’opérateur autorise la suppression des copies restaurées et historiques de test. Les images PostgreSQL/MinIO officielles restent partagées et protégées.

| Nom | ID complet | État | Volume |
|---|---|---|---|
| `g88-a-source-db` | `682fba70829226fa33c1927a9cd2ff3df2b29f6d182a72caf220c6e28cd4892d` | running | `ef2b0c74edb497d2c51dbef793178220ebb45f92ecb0a746f94cf169ce2cdf3e` |
| `g88-a-source-minio` | `714bbb39c875babe637bb87bb57b94bf35107843fbc1dfd5dd4f4253fcd2752a` | running | `82546146f389888ec434a84b9718ead10cb1713bb7380590e2b07ad35db8e6dd` |
| `g88-a-restore-db` | `05eb76a2e77581820ad4f5f04102b5798f0c3bdac018124db1e13bf466ab1976` | running | `ca86ceb2d54c0f91690f94f78d2b9f05bc1b84403b2cd7b9ac9fe9543009ea66` |
| `g88-a-restore-minio` | `b3b9c368ba930d5b08cf2a91b3b6e5582d0f51ddfda112089a67e9b4e0216593` | running | `b46e64620a5c1fd309142c03f418d5042485dffa8d76d4cb3d9bf4bca5e00877` |

Réseau : `g88-a-isolated`, ID `3c25419319a0`. Les quatre volumes sont anonymes et exclusivement attachés aux quatre conteneurs ci-dessus au moment du gel.

## 9. Images candidates

Images applicatives/outils incluses seulement si elles ne sont référencées par aucun conteneur conservé :

- G2 : `g2-clean-app-test`, `g2-clean-test`, `g2-clean-tools`, `g2-migration-tools`.
- P0A2 : `mobile-money-corpus-p0a2-test-app-test`, `mobile-money-corpus-p0a2-test-test`, `mobile-money-corpus-p0a2-test-tools`.
- D/D1/D2/D3 : images `mobile-money-corpus-remediation-d*` correspondantes.
- F5A3 : `f5a3-candidate:0005-freeze@sha256:170270493de28c7e4fffbf1cd396122680d4eb2684249edd8fd7e166be4493e2`.

Les digests complets des images applicatives sont ceux du manifeste G10 et doivent être comparés avec `docker image inspect` juste avant `docker rmi`. Les images officielles PostgreSQL, MinIO et toutes images utilisées par production/dev/rollback sont conservées.

## 10. Ordre d’exécution verrouillé

1. F5A2 : supprimer conteneurs, vérifier services, supprimer réseau vide.
2. F5A3 : supprimer conteneurs, vérifier services, supprimer réseau, puis image candidate.
3. D1 + D3 : arrêter/supprimer conteneurs ; vérifier santé ; supprimer les quatre volumes ; supprimer réseau C1 vide.
4. D2 : arrêter/supprimer conteneurs ; vérifier santé ; supprimer volumes D2 ; supprimer réseau C1B vide.
5. G2 + D base + P0A2 : retirer tous les conteneurs listés, vérifier les références de chaque volume, supprimer uniquement les volumes devenus exclusifs et les réseaux G2/E2/P0A2 vides.
6. G8.8 : supprimer les quatre conteneurs et leurs volumes anonymes ; supprimer le réseau isolé vide.
7. Images : supprimer seulement les images candidates non référencées, jamais par préfixe et jamais avec `--force`.
8. Après chaque lot : santé production/dev/protégés, HTTPS, logs et mesure des ressources.

Au premier échec, le lot s’arrête et les ressources restantes sont conservées.

## 11. Estimation des gains

| Groupe | RAM instantanée relevée | Volumes/logiques potentiels | Gain réel attendu |
|---|---:|---:|---|
| F5A2/F5A3 | quasi nul à l’arrêt | image F5A3 ~1,09 GB affichée Docker | dépend des couches partagées |
| D1/D3 | ~713 MiB | quatre volumes D, environ 0,10 GiB | à mesurer après suppression |
| D2 | ~346 MiB | deux volumes D2, environ 0,05 GiB | à mesurer |
| G2 | ~1,10 GiB | volumes G2 ~0,17 GiB connus | archive et couches à confirmer |
| D base/P0A2 | ~238 MiB actif pour D base | volumes P0A2 ~0,13 GiB connus | uniquement après retrait des références |
| G8.8 | ~532 MiB | volumes anonymes à mesurer | à mesurer |
| Total instantané des groupes actifs | environ 2,93 GiB | non additionnable directement | estimation, non garantie |

Les tailles Docker logiques, les couches partagées et l’espace disque réel libéré seront distingués dans le rapport final.

## 12. Résultat attendu

Suppression autorisée uniquement pour les IDs et ressources de ce manifeste, sous réserve de la revalidation immédiate de chaque lot.

Ressources ambiguës ou non réconciliées exclues :

- volumes historiques C1/C1B non montés par les conteneurs ciblés ;
- G3, E1, D4 et autres campagnes non autorisées ;
- archives originales et sauvegardes hors Docker ;
- images officielles partagées ;
- toute ressource dont l’ID ou le consommateur diverge.


