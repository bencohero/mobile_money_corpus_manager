# G8.8-A — Revue sécurité

## Contrôles passants

- `CONFIRM_RESTORE=YES` obligatoire ;
- mode limité à `synthetic` ou `isolated` ;
- identifiant de cible production refusé ;
- hostname PostgreSQL production refusé ;
- endpoint MinIO production/public refusé ;
- alias MinIO vérifié par export et comparaison à l’endpoint isolé ;
- schéma, statut, chemins, liens symboliques et arborescence contrôlés ;
- couverture exacte des fichiers par les sommes SHA-256 ;
- bucket demandé comparé au bucket du manifest ;
- bucket cible créé seulement dans la cible MinIO explicitement isolée.

## Réserves opératoires

- l’image `Dockerfile.tools` historique ne contient pas `python3` et son URL de
  téléchargement `mc` est obsolète (`410`) ; l’image d’exécution de restauration
  doit donc être reconstruite et validée avant usage opérationnel ;
- aucune restauration de production n’a été tentée ;
- les services synthétiques doivent être supprimés selon la procédure de test,
  jamais par confusion avec les volumes de production.
