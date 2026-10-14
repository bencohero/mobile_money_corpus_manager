# G10.3 — Docker Cleanup Recovery Report

**Serveur :** `vmi3474447`  
**Date :** 2026-10-14  
**Références :** G10.2 manifest/report, G10.1 closure plan  
**Statut final :** **BLOCKED / PARTIAL**

Le diagnostic D1/D3 est terminé et la reprise partielle a été effectuée. L’exécution a été arrêtée après une seconde anomalie d’arrêt sur `g2-clean-tools-1`. Aucun redémarrage d’environnement de test, aucun nettoyage global et aucune modification de production n’ont été effectués.

## 1. Cause racine confirmée

### D1/D3 applications

Les deux applications ont été créées avec :

```text
Path: sh
Args: -c alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
User: appuser
RestartPolicy: no
Memory limit: 0
OOMKilled: false
ExitCode: 137
```

Le shell `sh -c` est PID 1 et Uvicorn est un processus fils. Le conteneur ne comporte pas d’init et aucune gestion de signal n’est configurée pour transmettre SIGTERM au processus fils. Lorsque Docker a arrêté les six conteneurs simultanément avec un délai de 30 secondes, les applications ont reçu le signal au niveau du shell, tandis que leur Uvicorn ne s’est pas terminé dans le délai. Docker a ensuite envoyé SIGKILL.

Preuves :

- D1 app : exit 137, `OOMKilled=false`, `Error=""` ;
- D3 app : exit 137, `OOMKilled=false`, `Error=""` ;
- aucune limite mémoire Docker ;
- les logs montrent des `/ready` 503 et des erreurs DNS PostgreSQL après l’arrêt concurrent des bases ;
- PostgreSQL et MinIO D1/D3 ont terminé avec exit 0 ;
- les timestamps montrent l’échec de readiness avant la fin des conteneurs.

La cause est donc un **timeout d’arrêt dû à la hiérarchie shell → Uvicorn et à l’ordre d’arrêt concurrent**, pas un OOM.

### g2-clean-tools

Une seconde occurrence confirme le même défaut de wrapper :

- Path : `docker-entrypoint.sh`
- Args : `sleep infinity`
- StopSignal : `SIGINT`
- exit 137, `OOMKilled=false`
- arrêt standard avec délai 30 secondes non gracieux.

Cette anomalie bloque la poursuite automatique du nettoyage G2. Le conteneur reste conservé.

## 2. Procédure d’arrêt corrigée

Pour les applications de test :

1. Ne pas arrêter simultanément application, PostgreSQL et MinIO.
2. Inspecter la hiérarchie des processus dans le conteneur.
3. Envoyer SIGTERM au processus serveur fils Uvicorn.
4. Attendre sa disparition et vérifier que le shell applicatif termine avec exit 143 ou 0.
5. Si le fils ne termine pas dans le délai recommandé de 30 secondes, arrêter le lot et conserver les ressources.
6. Arrêter PostgreSQL avec un délai gracieux de 30 secondes.
7. Arrêter MinIO avec un délai gracieux de 30 secondes.
8. Vérifier les codes de sortie, `OOMKilled`, montages et dépendances.
9. Supprimer uniquement les conteneurs nominativement autorisés.
10. Supprimer volumes puis réseau seulement après vérification d’exclusivité.

Pour les outils basés sur `sleep infinity`, la procédure doit identifier le processus fils réel et vérifier son arrêt avant de supprimer le conteneur. Aucun `docker stop` groupé ne doit être utilisé sur un groupe de dépendances.

Cette correction est procédurale uniquement. Aucun fichier Compose, image ou application n’a été modifié.

## 3. Ressources supprimées pendant G10.3

### D1/D3

Conteneurs supprimés :

- D1 app `27567e11f3fd93dfce1fee94b0f601215b1f8ebe27c2b4709f13fafcaeef01bc`
- D1 DB `6ce057ce3a22f4a7e1fe2531b07c591166f58260488dff6b1ed880a68494d9c8`
- D1 MinIO `69c1fa41c30f44c5e09fab5df0140f29b0d77d1427d63644bc0e81823064eda5`
- D3 app `5138c3209ac5410cc094ec174b665dda241cdbd716a6f5d626766198f81bd4c2`
- D3 DB `1f8e2c6ab9d02c8d2a636852c5d72a8288d46e955f8e9bd72ecff62a22ad6c5d`
- D3 MinIO `8ea38ad6f4daecc266a438d7ed9b64c0b313e02e61fd1f97ca9858e75d9e864d`

Volumes supprimés :

- `mobile-money-corpus-remediation-d1_c1-test-pgdata`
- `mobile-money-corpus-remediation-d1_c1-test-miniodata`
- `mobile-money-corpus-remediation-d3_c1-test-pgdata`
- `mobile-money-corpus-remediation-d3_c1-test-miniodata`

Réseau supprimé :

- `mobile-money-corpus-c1-test` — `90088f2fbfd8`

Les quatre volumes ne possédaient plus aucun consommateur après suppression des six conteneurs. Le réseau ne contenait plus aucun conteneur.

### D2

Conteneurs supprimés :

- `mobile-money-corpus-remediation-d2-app-test-1` — `8ae38970ef0e950cd2c94aa7eea4f91fb2a047d40ced28c5cf0aee66a74e036f`
- `mobile-money-corpus-remediation-d2-db-test-1` — `2110a0104b713b53ac5fb7af08808471793c7f1c0cb22a8c06f6c7334ae8cbd0`
- `mobile-money-corpus-remediation-d2-minio-test-1` — `41dbb7d7d84d55c9e250f05144641b4f2f7fe2b242f90aa6ef880ab7fdb2435c`

Volumes supprimés :

- `mobile-money-corpus-remediation-d2_c1b-test-pgdata`
- `mobile-money-corpus-remediation-d2_c1b-test-miniodata`

Réseau supprimé :

- `mobile-money-corpus-c1b-test` — `1b476a25a823`

D2 a été arrêté séquentiellement : Uvicorn exit 143 sans OOM, PostgreSQL et MinIO exit 0. Contrôles post-lot : PASS.

## 4. Ressources conservées après blocage

Non supprimés :

- G2 clean : application, outils, PostgreSQL/MinIO déjà arrêtés ou conservés ;
- G2 migration : outils, PostgreSQL et MinIO encore actifs ou arrêtés selon l’état ci-dessous ;
- D base : conteneur MinIO encore actif, DB arrêtée, application créée ;
- P0A2 : conteneurs arrêtés/créé ;
- G8.8 : quatre conteneurs actifs et volumes anonymes ;
- volumes G2/P0A2 partagés ;
- réseaux G2, E2, P0A2 et G8.8 ;
- toutes les ressources G3, E1, D4, C1/C1B historiques non incluses ;
- production, développement, rollback G8.5-R, images officielles et sauvegardes.

État résiduel notable :

- `g2-migration-tools-1` actif ;
- `g2-migration-db-test-1` actif ;
- `g2-migration-minio-test-1` actif ;
- `g2-migration-minio-restore-1` actif ;
- `mobile-money-corpus-remediation-d-minio-test-1` actif ;
- `g2-clean-tools-1` arrêté avec exit 137 ;
- les services G2 clean restants sont arrêtés mais non supprimés.

Aucun volume G2/P0A2 n’a été supprimé.

## 5. Contrôles de sécurité et santé

Après D1/D3 et D2 :

- production app/db/minio : `running/healthy` ;
- développement app/db/minio : `running/healthy` ;
- HTTPS `/health` : HTTP 200 ;
- HTTPS `/ready` : HTTP 200 ;
- Traefik, CrowdSec, Beszel, Vaultwarden, Superset, pgAdmin, PostgreSQL global, BentoPDF et IT Tools : présents/running ;
- rollback G8.5-R : présent ;
- réseaux production, développement et infrastructure : présents ;
- sauvegardes de production : non modifiées ;
- pare-feu, ports publics, Traefik et démon Docker : non modifiés.

## 6. Mesures

Référence G10.2 avant nettoyage : 59 conteneurs, 40 actifs, 66 volumes, 17 réseaux, 76 images.

État après F5A2/F5A3, D1/D3 et D2 :

| Mesure | État actuel | Écart |
|---|---:|---:|
| Conteneurs totaux | 40 | -19 |
| Conteneurs actifs | 25 | -15 |
| Volumes | 60 | -6 |
| Réseaux | 13 | -4 |
| Images distinctes | 75 | -1 |
| Images Docker | 16,27 GiB | couches partagées |
| Volumes Docker | 1,718 GiB | -148 MiB logiques environ |
| Mémoire disponible | ~7,8 GiB | amélioration observée |
| Disque libre | 85 GiB | variation non mesurable |
| Swap | 0 | inchangé |

Le gain disque réel ne peut pas être assimilé à la somme des tailles logiques. Le gain RAM inclut l’arrêt de groupes qui restent partiellement conservés.

## 7. Incidents

1. D1/D3 : arrêt initial non gracieux, cause racine confirmée ; ressources ensuite supprimées après vérification.
2. D2 : arrêt gracieux obtenu avec la procédure corrigée.
3. G2 clean tools : nouvelle sortie 137 sur wrapper `docker-entrypoint.sh sleep infinity` avec StopSignal SIGINT ; exécution interrompue.
4. Aucun incident production, développement, rollback ou infrastructure protégée.

## 8. Reprise restante

Avant toute nouvelle action :

1. Ne pas supprimer le conteneur G2 tools exit 137 sans validation nominative et inspection de son volume backup.
2. Appliquer la procédure processus-fils aux outils et applications test restants.
3. Traiter G2/D base/P0A2 comme un groupe unique après revalidation des références partagées.
4. Traiter G8.8 séparément après contrôle des quatre volumes anonymes.
5. Vérifier production/dev/protégés après chaque lot.
6. Arrêter immédiatement à toute nouvelle sortie 137 ou dépendance inattendue.

## 9. Décision finale

**G10.3 : BLOCKED / PARTIAL**

Les groupes F5A2, F5A3, D1/D3 et D2 sont nettoyés. La cause D1/D3 est comprise et une procédure d’arrêt correcte est établie. Le nettoyage définitif reste bloqué par la nouvelle anomalie `g2-clean-tools-1` et par les groupes G2/D base/P0A2/G8.8 encore non traités.

