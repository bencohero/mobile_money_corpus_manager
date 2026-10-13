# G9.1-R — Décision finale

## Décision : BLOCKED

La sauvegarde finale et la restauration coordonnée ne peuvent pas être
déclarées validées : aucune opération réelle n’a été exécutée, conformément au
garde-fou d’absence d’autorisation opérateur explicite.

## Constats favorables

- conteneurs réels identifiés par inspection ;
- release exacte identifiée ;
- volumes et réseau de production identifiés ;
- app.write_freeze présent dans l’image release ;
- outillage G8.8-B disponible et vérifiable ;
- transfert corrigé pour être tiré depuis Kubuntu ;
- aucun dégel automatique prévu.

## Blocage précis

L’autorisation est maintenant reçue, mais la phase A reste bloquée par des
prérequis d’exécution non résolus :

1. `/var/backups/mobile-money-corpus` n’existe pas et aucun chemin de destination
   approuvé n’a été fourni ;
2. aucun endpoint SSH Kubuntu réel n’est configuré ou identifiable sur l’hôte ;
3. `restic` n’est pas disponible sur l’hôte courant, et le dépôt distant ne
   peut donc pas être vérifié depuis cette session.

Le gel n’a pas été engagé : l’état reste `OPEN`, `active_writes=0`, `epoch=0`.
La production n’a pas été redémarrée, modifiée ou exposée.

Pour reprendre, fournir le chemin backup local approuvé, l’alias/hostname SSH
Kubuntu, l’utilisateur, le chemin incoming et les paramètres restic hors secret.
Puis refaire la phase A sans gel; ne déclarer
`BACKUP_AND_RESTORE_VALIDATED` que si archive schema 2, copie restic, restore
isolé, Alembic, readiness, health, inventaires, empreintes et réconciliation
passent tous. L’accès public reste fermé.
