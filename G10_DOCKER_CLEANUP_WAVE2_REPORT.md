# G10 — Docker Cleanup Wave 2 Execution Report

**Serveur :** `vmi3474447`  
**Projet :** Mobile Money Corpus Manager  
**Statut :** **PENDING_APPROVAL / NOT_EXECUTED**  
**Manifeste associé :** [G10_DOCKER_CLEANUP_WAVE2_MANIFEST.md](G10_DOCKER_CLEANUP_WAVE2_MANIFEST.md)

## 1. État d’exécution

Aucune suppression, aucun arrêt de conteneur, aucune suppression de volume, réseau ou image n’a été exécuté pendant l’audit G10.

- Approbation du manifeste : en attente.
- Campagne exécutée : aucune.
- Ressources supprimées : aucune.
- Production/dev/rollback : conservés et non modifiés.
- Traefik, pare-feu et démon Docker : non modifiés.

## 2. Approbation opérateur

À compléter avant toute action :

| Élément | Valeur |
|---|---|
| Manifest version | à renseigner |
| Campagnes autorisées | à renseigner nominativement |
| Conteneurs autorisés | à renseigner avec IDs complets |
| Volumes autorisés | à renseigner avec preuve d’exclusivité |
| Réseaux autorisés | à renseigner avec preuve de réseau vide et dédié |
| Images autorisées | à renseigner avec digest complet |
| Opérateur | à renseigner |
| Date/heure | à renseigner |
| Validation | en attente |

## 3. Mesures avant/après

À renseigner au début puis après chaque campagne approuvée :

| Mesure | Avant | Après campagne | Variation |
|---|---:|---:|---:|
| Conteneurs actifs | 40 | — | — |
| Conteneurs totaux | 59 | — | — |
| Mémoire disponible | ~6,1 GiB | — | — |
| CPU | à mesurer | — | — |
| Disque libre | ~85 GiB | — | — |
| Taille images Docker | ~16,27 GiB | — | — |
| Taille volumes Docker | ~1,866 GiB | — | — |
| Build cache | ~15,58 GiB | — | — |

## 4. Ressources réellement supprimées

Aucune à ce stade.

| Campagne | Conteneurs | Volumes | Réseaux | Images | Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## 5. Ressources conservées

À conserver au minimum :

- production `mobile_money_corpus_manager_v0_1` et ses volumes ;
- développement `mobile_money_corpus_manager_dev` et ses volumes ;
- rollback G8.5-R ;
- Traefik et applications protégées ;
- réseaux partagés ;
- sauvegardes `/home/sangouman/mobile-money-corpus-backups/` ;
- toutes les ressources classées À INVESTIGUER dans le manifeste tant qu’elles ne disposent pas d’une approbation nominative.

## 6. Contrôles de santé

À exécuter avant et après chaque campagne approuvée :

- production Corpus Manager : `healthy` ;
- HTTPS : endpoints `/health` et `/ready` ;
- parcours applicatifs requis, y compris connexion et déconnexion ;
- développement : conteneurs et volumes inchangés ;
- PostgreSQL et MinIO de production : inchangés ;
- rollback G8.5-R : conteneur et image toujours présents ;
- Traefik et autres applications : inchangés ;
- ports publics et règles de sécurité : inchangés ;
- journaux Traefik et applicatifs : absence de nouvelle anomalie bloquante.

## 7. Anomalies et opérations restantes

- Les campagnes G2, D, D1, D2, D3 et G8.8 ont encore des traitements actifs ou des dépendances non résolues.
- P0A2 partage actuellement des ressources avec D base et G2.
- D1 et D3 partagent un réseau.
- G8.8 n’a pas de labels Compose et son propriétaire doit être confirmé.
- F5A2/F5A3 nécessitent une confirmation de rétention et de propriété, notamment pour l’image candidate/rollback.
- Une erreur de syntaxe issue d’une requête de diagnostic mal échappée a été observée dans un journal de test ; aucun changement de données n’a été effectué.

## 8. Décision finale

**AUDIT COMPLET — EN ATTENTE D’APPROBATION**

Le rapport ne pourra passer à `EXECUTED` qu’après approbation explicite du manifeste nominatif, exécution campagne par campagne et validation de tous les contrôles ci-dessus.

