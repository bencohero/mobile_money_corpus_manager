# F5A3 — go/no-go

## Décision : PRÊT POUR AUTORISATION DU CORRECTIF

La candidate `sha256:170270493de28c7e4fffbf1cd396122680d4eb2684249edd8fd7e166be4493e2` a été bâtie depuis l’extraction de l’image réellement déployée, conserve le schéma Alembic `0005`, et ajoute uniquement le middleware/gate de gel et son contrôle CLI. Les tests isolés demandés sont passés, y compris concurrence, upload, idempotence, transcription, vérification, timeout, redémarrage, plusieurs processus, captures synthétiques pendant `FROZEN`, échecs partiels et restauration isolée.

## Conditions non négociables avant autorisation

- Ne pas déployer sans montage d’état partagé et persistant, propriétaire UID `10001`, permissions restrictives.
- Vérifier le digest exact de la candidate et l’absence de `0006`–`0008`.
- Ne pas modifier Traefik, les volumes de données, le pare-feu ou le schéma.
- Faire approuver séparément la destination locale et la fenêtre d’interruption.
- Activer le gel uniquement après contrôle des processus et requêtes en cours.
- Reprendre uniquement après manifestes et marqueur `COMPLETE` validés.

## Hors périmètre de cette décision

Aucune sauvegarde réelle, aucun déploiement, aucune migration, restauration ou modification de production n’a été effectué. La décision ne vaut pas autorisation de sauvegarde réelle ; elle autorise seulement la revue du correctif candidat et de son déploiement contrôlé.

