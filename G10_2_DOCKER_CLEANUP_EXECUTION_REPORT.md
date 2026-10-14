# G10.2 — Docker Cleanup Execution Report

**Serveur :** `vmi3474447`  
**Date de début :** 2026-10-14T01:19:45+02:00  
**Date d’arrêt :** 2026-10-14, après le lot D1/D3  
**Manifeste :** [G10_2_FINAL_DELETION_MANIFEST.md](G10_2_FINAL_DELETION_MANIFEST.md)  
**Statut final :** **BLOCKED / PARTIAL**

Le nettoyage a été interrompu conformément à la procédure après une anomalie d’arrêt contrôlé des applications D1/D3. Aucun lot supplémentaire n’a été exécuté.

## 1. Décisions appliquées

Autorisation G10.2 appliquée uniquement aux ressources nominativement revalidées :

- F5A2 : suppression exécutée ;
- F5A3 : suppression exécutée ;
- D1/D3 : arrêt contrôlé tenté, suppression refusée après anomalie ;
- D2, G2, D base, P0A2 et G8.8 : non traités.

Aucune suppression globale, aucun `docker system prune`, aucun `docker volume prune`, aucun redémarrage Docker et aucune modification Traefik/pare-feu n’ont été effectués.

## 2. État initial

Instantané capturé le 2026-10-14T01:19:45+02:00 :

| Mesure | Avant |
|---|---:|
| Conteneurs totaux | 59 |
| Conteneurs actifs | 40 |
| Volumes | 66 |
| Réseaux | 17 |
| Images distinctes | 76 |
| Images Docker | 16,27 GiB |
| Volumes Docker | 1,866 GiB |
| Mémoire disponible | ~6,1 GiB |
| Disque libre | 85 GiB |
| Swap | 0 |

Production et développement étaient `running/healthy`. HTTPS `/health` et `/ready` répondaient HTTP 200 avec le Host approuvé. Les sauvegardes de production existaient sous `/home/sangouman/mobile-money-corpus-backups/`.

## 3. Ressources supprimées

### Lot F5A2

Conteneurs supprimés :

- `f5a2-db` — `d168404a6b8fe2d441c69c19cd0adbf19f01f7672e5a7a821c4b9cc7ba545cae`
- `f5a2-minio` — `caf6537d3a7c7a7f2c62bb54c15fae16974475b647919fcd6631aeb138dc7bfe`
- `f5a2-restore-db` — `debbb21c4c1dbdcf794ab7f1c465743b5236c5342b5248627abeef68e44b0b7a`
- `f5a2-restore-minio` — `ec93a60ca56433255f984f4a30607fd5b96105ee7fffcfee46b5a4a83c5a4735`

Réseau supprimé :

- `f5a2-isolated` — `17b12e2f5cf4`

Aucun volume persistant F5A2 n’était attaché.

Contrôle post-lot : PASS. Production, développement, Traefik, services protégés et HTTPS sont restés opérationnels.

### Lot F5A3

Conteneurs supprimés :

- `f5a3-app-a` — `89d43d197dcf3742879ef1a7d7965a840597bae8a5f6c4a8d4e82883218240de`
- `f5a3-app-b` — `43fa99dcba268bbca485589d009a023b2a8ee1441c980e21f5c68ee75f723215`
- `f5a3-db` — `23a66c59ef78647eef8f97ec2cfcff597b30a16f0da2c613326ea9f9bfc197d9`
- `f5a3-minio` — `f6d246c64fb4f0b297b2d33e417812e95a30b1c1cac9d8b481110e2678da02ce`
- `f5a3-restore-db` — `6c8e80e0bf98dd4ef56e890d68c2cbbb6358fabfa4984ad83bb2efba3f3bccd9`
- `f5a3-restore-minio` — `e41c12e35a5aef40e04fb4d886c589d60f91cabbbd1b6670c3cd2bf5438c1f4f`

Réseau supprimé :

- `f5a3-isolated` — `b0259385a441`

Image candidate supprimée :

- `f5a3-candidate:0005-freeze`
- digest `sha256:170270493de28c7e4fffbf1cd396122680d4eb2684249edd8fd7e166be4493e2`

Les images officielles PostgreSQL/MinIO n’ont pas été supprimées. Le rollback G8.5-R a été recontrôlé et reste présent :

- conteneur `mobile_money_corpus_manager_g8_5_r-app` — ID `f2eb5a50ac00b6ff9a25985173d9aff1f0efeb6c8426abb1b33a8f6940549f50`
- statut : exited, image conservée.

Contrôle post-lot : PASS.

## 4. Anomalie et arrêt immédiat

Pour le lot D1/D3, les six conteneurs ont été revalidés avec les IDs du manifeste et le réseau partagé `mobile-money-corpus-c1-test`.

PostgreSQL et MinIO se sont arrêtés proprement :

- D1 DB : exit 0 ;
- D1 MinIO : exit 0 ;
- D3 DB : exit 0 ;
- D3 MinIO : exit 0.

Les deux conteneurs applicatifs n’ont pas terminé dans le délai contrôlé de 30 secondes :

- D1 app — exit 137, `OOMKilled=false` ;
- D3 app — exit 137, `OOMKilled=false`.

Les journaux montrent des réponses `/ready` en 503 et des erreurs de résolution PostgreSQL après l’arrêt des services DB. Cette séquence n’est pas considérée comme une clôture propre du lot.

Conformément à la règle d’arrêt immédiat :

- aucun conteneur D1/D3 n’a été supprimé ;
- aucun volume D1/D3 n’a été supprimé ;
- le réseau partagé n’a pas été supprimé ;
- D2, G2, D base, P0A2 et G8.8 n’ont pas été traités.

Les ressources D1/D3 restent conservées pour analyse opérateur.

## 5. État après arrêt

| Mesure | Après F5A2/F5A3 et arrêt D1/D3 | Variation |
|---|---:|---:|
| Conteneurs totaux | 49 | -10 |
| Conteneurs actifs | 34 | -6 |
| Volumes | 66 | 0 |
| Réseaux | 15 | -2 |
| Images distinctes | 75 | -1 |
| Images Docker | 16,27 GiB | variation logique négligeable |
| Volumes Docker | 1,866 GiB | 0 |
| Mémoire disponible | ~6,8 GiB | environ +0,7 GiB |
| Disque libre | 85 GiB | variation non mesurable |
| Swap | 0 | inchangé |

État `docker system df` après l’arrêt :

- Images : 75, 16,27 GiB, reclaimable 9,889 GiB ;
- Conteneurs : 49, 32,82 MB ;
- Volumes : 66, 1,866 GiB ;
- Build cache : 15,58 GiB.

La mémoire libérée provient principalement de l’arrêt D1/D3 ; les ressources restent présentes et ne constituent pas encore un gain disque définitif.

## 6. Contrôles post-anomalie

| Contrôle | Résultat |
|---|---|
| Production app/db/minio | PASS — running/healthy |
| Développement app/db/minio | PASS — running/healthy |
| HTTPS `/health` | PASS — HTTP 200 |
| HTTPS `/ready` | PASS — HTTP 200 |
| Production PostgreSQL | PASS — healthy |
| Production MinIO | PASS — healthy |
| Rollback G8.5-R | PASS — présent |
| Traefik | PASS — running, non modifié |
| CrowdSec/Beszel/Vaultwarden | PASS — running |
| Superset/pgAdmin/PostgreSQL global/BentoPDF/IT Tools | PASS — running |
| Réseaux protégés | PASS — présents |
| Sauvegardes | PASS — présentes, non modifiées |
| Pare-feu / ports publics | inchangés, non modifiés |

## 7. Ressources conservées

Toutes les ressources non traitées restent présentes, notamment :

- D1/D3 : six conteneurs arrêtés, quatre volumes dédiés et réseau partagé ;
- D2 : trois conteneurs, volumes et réseau ;
- G2 clean/migration : conteneurs, volumes et réseaux ;
- D base/P0A2 : conteneurs, volumes partagés et réseau P0A2 ;
- G8.8 : quatre conteneurs actifs, quatre volumes anonymes et réseau isolé ;
- images officielles PostgreSQL/MinIO ;
- images de production, développement et rollback ;
- ressources historiques G3, E1, D4, C1/C1B non incluses ;
- toutes les sauvegardes et ressources protégées.

## 8. Reprise nécessaire

Avant toute reprise :

1. analyser pourquoi les applications D1/D3 n’ont pas répondu à SIGTERM dans 30 secondes ;
2. confirmer l’état des données et l’absence de traitement utile ;
3. décider si les conteneurs D1/D3 doivent être supprimés après cette analyse ;
4. refaire une revalidation complète des IDs et références de volumes ;
5. reprendre au maximum avec un lot D1/D3 explicitement approuvé ;
6. refaire les contrôles de santé entre chaque lot.

Aucune reprise automatique ni tentative de réparation destructive n’a été effectuée.

## 9. Décision finale

**G10.2 : BLOCKED / PARTIAL**

Les lots F5A2 et F5A3 ont été supprimés avec succès. Le nettoyage définitif ne peut pas être déclaré PASS tant que l’anomalie d’arrêt D1/D3 n’est pas analysée et tant que les lots restants n’ont pas été exécutés avec leurs contrôles.

