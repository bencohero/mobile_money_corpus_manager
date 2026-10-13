# G9.1 — Décision finale

## Décision : READY_FOR_G9_1_EXECUTION_APPROVAL

Les procédures sont prêtes pour une autorisation d’exécution : release et
schéma de référence identifiés, producteur schema 2 et consommateur schema 1/2
documentés, gel avec arrêt sûr si la gate est absente ou le drain incomplet,
transfert restic/SSH défini, restauration isolée sans migration implicite et
réconciliation déterministe.

Cette décision n’est pas une autorisation d’exécuter. Elle ne valide pas encore
la sauvegarde finale réelle, le snapshot restic, la réconciliation de production
ou l’ouverture publique.

Conditions : refaire les précontrôles live; confirmer app.write_freeze et
FROZEN avec active_writes=0; capturer et valider schema 2; vérifier empreintes
Kubuntu et snapshot restic; restaurer isolément et vérifier Alembic, readiness,
health et réconciliation à zéro; dégeler seulement après validation externe.

Si une condition échoue, passer à BLOCKED avec l’écart précis. L’accès public
reste fermé.

