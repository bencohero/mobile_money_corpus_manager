# G10.4 — Final Cleanup Report

**Serveur :** `vmi3474447`  
**Date :** 2026-10-14  
**Références :** G10.2, G10.3, G10.2 final deletion manifest  
**Statut :** **PASS — PÉRIMÈTRE AUTORISÉ FINALISÉ**

Le nettoyage des campagnes autorisées est terminé. Les ressources ambiguës, les campagnes non autorisées, les images partagées et les sauvegardes ont été conservées.

Aucune commande `docker system prune`, `docker volume prune`, `docker compose down -v`, suppression forcée, suppression par préfixe ou redémarrage Docker n’a été utilisée.

## 1. Cause et résolution du blocage G2

Les sorties `exit 137` observées sur D1/D3 et les tools G2 ne résultaient pas d’un manque mémoire :

- `OOMKilled=false` ;
- aucune limite mémoire Docker ;
- processus PID 1 enveloppé par un shell ou un entrypoint ;
- serveur Uvicorn ou `sleep infinity` en processus fils ;
- signal d’arrêt non transmis correctement ;
- SIGKILL envoyé après expiration du délai gracieux.

La procédure corrigée a été appliquée :

1. arrêt du processus fils applicatif ;
2. attente de la sortie du shell ;
3. arrêt séquentiel PostgreSQL puis MinIO ;
4. vérification des codes de sortie et références ;
5. suppression nominative des conteneurs ;
6. suppression des volumes uniquement après disparition de tous les consommateurs ;
7. suppression des réseaux vides.

Pour D2, Uvicorn a terminé avec exit 143 et PostgreSQL/MinIO avec exit 0. Les services G2/D base/P0A2 ont ensuite été arrêtés et supprimés après revalidation. Les deux volumes anonymes PostgreSQL G2 ont été identifiés après suppression des tools et supprimés séparément.

## 2. Ressources supprimées

### F5A2/F5A3 — exécuté en G10.2

- 10 conteneurs : 4 F5A2 et 6 F5A3, IDs consignés dans `G10_2_DOCKER_CLEANUP_EXECUTION_REPORT.md` ;
- réseaux `f5a2-isolated` (`17b12e2f5cf4`) et `f5a3-isolated` (`b0259385a441`) ;
- image `f5a3-candidate:0005-freeze`, digest `sha256:170270493de28c7e4fffbf1cd396122680d4eb2684249edd8fd7e166be4493e2`.

### D1/D3 — exécuté en G10.3

- six conteneurs, IDs consignés dans `G10_3_DOCKER_CLEANUP_RECOVERY_REPORT.md` ;
- volumes :
  - `mobile-money-corpus-remediation-d1_c1-test-pgdata`
  - `mobile-money-corpus-remediation-d1_c1-test-miniodata`
  - `mobile-money-corpus-remediation-d3_c1-test-pgdata`
  - `mobile-money-corpus-remediation-d3_c1-test-miniodata`
- réseau `mobile-money-corpus-c1-test`, ID `90088f2fbfd8`.

### D2 — exécuté en G10.3/G10.4

Conteneurs :

- `mobile-money-corpus-remediation-d2-app-test-1` — `8ae38970ef0e950cd2c94aa7eea4f91fb2a047d40ced28c5cf0aee66a74e036f`
- `mobile-money-corpus-remediation-d2-db-test-1` — `2110a0104b713b53ac5fb7af08808471793c7f1c0cb22a8c06f6c7334ae8cbd0`
- `mobile-money-corpus-remediation-d2-minio-test-1` — `41dbb7d7d84d55c9e250f05144641b4f2f7fe2b242f90aa6ef880ab7fdb2435c`

Volumes :

- `mobile-money-corpus-remediation-d2_c1b-test-pgdata`
- `mobile-money-corpus-remediation-d2_c1b-test-miniodata`

Réseau :

- `mobile-money-corpus-c1b-test`, ID `1b476a25a823`.

### G2 clean, G2 migration, D base et P0A2

Les 19 conteneurs suivants ont été supprimés après arrêt et revalidation :

| Conteneur | ID complet |
|---|---|
| `g2-clean-app-test-1` | `78d0110b3f58a2d0c3f768d68ff87e513895786f754244398e3ef86b6d76a716` |
| `g2-clean-tools-1` | `cf8576ad07a3c2d4cc85322b660b0d9c765fe08990e00a56e3a6851a2c83a746` |
| `g2-clean-db-test-1` | `d6cd1c0dd3c4bd05855d92fe18d37f2c28e1216e60d99b63eb21426cded531d5` |
| `g2-clean-db-restore-1` | `fac407b8989f079492865a6e615f4f08dbcd008ab284df1b1b8576085c57493d` |
| `g2-clean-minio-test-1` | `b522e4920de69ce7af6589d4b794818fe85a2ee762471b091b30ae22909fac7e` |
| `g2-clean-minio-restore-1` | `f6068da1b079805527aa29d403ba215358a74b5af6bfa995ea65526cfa2e5f54` |
| `g2-migration-tools-1` | `f3e78dba99738d096c7eb8051d8a793c73c1ac95b9be1999e38a1fc397e5d1fb` |
| `g2-migration-db-restore-1` | `9b260df4d3663a037721c02834475057872c6a207a3f0225106aa892fa7d53b2` |
| `g2-migration-db-test-1` | `d556a041e10399b2354f1f96c3058ffc12ad0fb849ffcdbce5adb100c7e1dfbf` |
| `g2-migration-minio-test-1` | `3b8f9118150a44af446c5c96abeef5dca4e8ae461b9d39a3c01aa4d9041f88e0` |
| `g2-migration-minio-restore-1` | `9cded0d102bd505e2beb9cf57584b755a109ae38592e827565474465cf1107b2` |
| `mobile-money-corpus-remediation-d-app-test-1` | `c715408a0ff2b9bbc8c42447050601cc9860eb0d690adf427efd29f768c2ed56` |
| `mobile-money-corpus-remediation-d-db-test-1` | `389bb236ee32c212e556095ae145cbf401a90f9884a2295ac6b15dd0b0428b0c` |
| `mobile-money-corpus-remediation-d-minio-test-1` | `d366d43fc0b9ecc1d2fa7ada90faef43f787aff5dd68d5b1d53d9d7718840ee5` |
| `mobile-money-corpus-p0a2-test-db-restore-1` | `fb61bacdf40ee58b07193836e48c860543c828a5cc3aaae4768ebc06145c0ced` |
| `mobile-money-corpus-p0a2-test-db-test-1` | `49c8e6f1332bd63a8821652220da4c6c22f8fb1ae8258a665da2fe320beb29e0` |
| `mobile-money-corpus-p0a2-test-minio-restore-1` | `21aa02996f87ab20fd011ed04ea7b7e3b5f4d866d2a580ba022b1874148df393` |
| `mobile-money-corpus-p0a2-test-minio-test-1` | `d16b1d14c176f0090a09f65f0b4412bb667863670cb7c1b377efa1455da37f54` |
| `mobile-money-corpus-p0a2-test-tools-1` | `cfca989de1fa587768814abc761b2cf1f3db793af6d9ac8062efb6f4ba6c64db` |

Volumes supprimés :

- `g2-migration-backup`
- `g2-migration-pgdata`
- `g2-migration-miniodata`
- `g2-migration-restore-pgdata`
- `g2-migration-restore-miniodata`
- `mobile-money-corpus-e2-migration-pgdata`
- `mobile-money-corpus-e2-migration-miniodata`
- `mobile-money-corpus-e2-migration-backup`
- `mobile-money-corpus-p0a2-test-pgdata`
- `mobile-money-corpus-p0a2-test-miniodata`
- `mobile-money-corpus-p0a2-test-backup`
- `mobile-money-corpus-p0a2-test-restore-pgdata`
- `mobile-money-corpus-p0a2-test-restore-miniodata`
- volume anonyme `08edbfabc88f22cabb08fee24a5a910c55e74c9551b4fa8a595c30c919f58a8c`
- volumes anonymes PostgreSQL tools G2 :
  - `2766c543e7ed15f0f9009a9882d93f9b474ce161ddd9c98c9bd15c2476f05cf2`
  - `8998bc867cd17f4232c553d41b824a5d3f4f295bbcc29f9ae4d783db0b2a7367`

Réseaux supprimés :

- `g2-migration-network`, ID `953a8a21aa3f`
- `mobile-money-corpus-e2-migration`, ID `a8b5e172fc20`
- `mobile-money-corpus-p0a2-test`, ID `d954651b840e`.

### G8.8

Conteneurs supprimés :

- `g88-a-source-db` — `682fba70829226fa33c1927a9cd2ff3df2b29f6d182a72caf220c6e28cd4892d`
- `g88-a-source-minio` — `714bbb39c875babe637bb87bb57b94bf35107843fbc1dfd5dd4f4253fcd2752a`
- `g88-a-restore-db` — `05eb76a2e77581820ad4f5f04102b5798f0c3bdac018124db1e13bf466ab1976`
- `g88-a-restore-minio` — `b3b9c368ba930d5b08cf2a91b3b6e5582d0f51ddfda112089a67e9b4e0216593`

Volumes anonymes supprimés :

- `ef2b0c74edb497d2c51dbef793178220ebb45f92ecb0a746f94cf169ce2cdf3e`
- `82546146f389888ec434a84b9718ead10cb1713bb7380590e2b07ad35db8e6dd`
- `ca86ceb2d54c0f91690f94f78d2b9f05bc1b84403b2cd7b9ac9fe9543009ea66`
- `b46e64620a5c1fd309142c03f418d5042485dffa8d76d4cb3d9bf4bca5e00877`

Réseau supprimé :

- `g88-a-isolated`, ID `3c25419319a0`.

## 3. Images supprimées

Images applicatives/outils supprimées après vérification d’absence de référence :

- G2 : `g2-clean-app-test`, `g2-clean-test`, `g2-clean-tools`, `g2-migration-tools` ;
- P0A2 : `mobile-money-corpus-p0a2-test-app-test`, `mobile-money-corpus-p0a2-test-test`, `mobile-money-corpus-p0a2-test-tools` ;
- D base/D1/D2/D3 : images `mobile-money-corpus-remediation-d*` correspondantes ;
- F5A3 : `f5a3-candidate:0005-freeze`.

Les digests complets et tailles sont consignés dans le manifeste G10.2. Aucun `postgres`, MinIO, production, développement ou rollback n’a été supprimé.

Images historiques ambiguës conservées, notamment :

- `mobile-money-corpus-d-test`
- `mobile-money-corpus-d-app-test`
- `remediation-c1*`
- `remediation-c1b*`
- `g3*`, `e1*`, `p0a1*`.

## 4. Contrôles par groupe

| Groupe | Résultat |
|---|---|
| F5A2 | PASS — conteneurs/réseau supprimés |
| F5A3 | PASS — conteneurs/réseau/image candidate supprimés |
| D1/D3 | PASS — arrêt corrigé, conteneurs/volumes/réseau supprimés |
| D2 | PASS — Uvicorn exit 143, DB/MinIO exit 0, ressources supprimées |
| G2/D base/P0A2 | PASS — dépendances partagées retirées avant volumes/réseaux |
| G8.8 | PASS — quatre conteneurs/volumes/réseau supprimés |

## 5. État protégé final

- Production app/db/minio : `running/healthy`.
- Développement app/db/minio : `running/healthy`.
- Rollback G8.5-R : présent, conteneur `f2eb5a50ac00...`, image conservée.
- HTTPS `/health` : HTTP 200.
- HTTPS `/ready` : HTTP 200.
- Traefik, CrowdSec, Beszel, Vaultwarden, Superset, pgAdmin, PostgreSQL global, BentoPDF et IT Tools : présents/running.
- Réseaux `frontend`, backend production, développement, `infra-network` et `superset_default` : présents.
- Sauvegardes : marqueurs `COMPLETE` présents jusqu’au 2026-10-13.
- Pare-feu, Traefik et démon Docker : non modifiés.

## 6. Mesures avant/après

Référence avant G10.2 : 59 conteneurs, 40 actifs, 66 volumes, 17 réseaux, 76 images.

| Mesure | Avant | Après | Variation |
|---|---:|---:|---:|
| Conteneurs totaux | 59 | 17 | -42 |
| Conteneurs actifs | 40 | 16 | -24 |
| Volumes | 66 | 40 | -26 |
| Réseaux | 17 | 9 | -8 |
| Images distinctes | 76 | 56 | -20 |
| Images Docker | 16,27 GiB | 16,26 GiB | couches partagées |
| Volumes Docker | 1,866 GiB | 1,288 GiB | ~578 MiB logiques |
| Build cache | 15,58 GiB | 15,58 GiB | inchangé |
| Mémoire disponible | ~6,1 GiB | ~9,1 GiB | +~3,0 GiB |
| Disque libre | 85 GiB | 86 GiB | +~1 GiB arrondi |
| Swap | 0 | 0 | inchangé |

La taille logique Docker ne représente pas directement l’espace disque récupéré : les couches d’images sont partagées. Le gain disque réel observé sur `df -h` est arrondi à environ 1 GiB.

## 7. Résidus explicitement conservés

Les ressources suivantes n’ont pas été supprimées, car elles appartiennent à des campagnes hors périmètre ou ne sont pas réconciliées nominativement :

- volumes `mobile-money-corpus-p0a2-test_c1-*` ;
- volumes `remediation-c1_*` et `remediation-c1b_*` ;
- volumes G3, E1 et D4 ;
- volumes anonymes `715582944e...`, `cdc492569e...`, `ece5302d...` ;
- images D historiques non réconciliées, G3, E1, P0A1 et outils d’audit ;
- campagnes G2/G4/G5/G9-R3 déjà traitées selon leurs rapports antérieurs ou ressources non incluses dans G10.4.

Ces résidus sont conservés volontairement et nécessitent un ticket séparé avec manifeste nominatif.

## 8. Anomalies non bloquantes à suivre séparément

Les journaux Traefik ont montré des erreurs récurrentes préexistantes liées à :

- métriques CrowdSec refusées en HTTP 403 ;
- définitions de routeur/middleware dupliquées entre applications protégées.

Elles n’ont pas été provoquées ou modifiées par le nettoyage. Les applications protégées et les endpoints de production restent sains. Leur correction est hors périmètre G10.4.

## 9. Décision finale

**G10.4 : PASS — NETTOYAGE DU PÉRIMÈTRE AUTORISÉ FINALISÉ.**

Les campagnes F5A2, F5A3, D1, D2, D3, G2 clean, G2 migration, D base, P0A2 et G8.8 ont été nettoyées selon les listes fermées et les dépendances vérifiées. Les ressources ambiguës et hors périmètre restent conservées.

