# G8.6-R — Décision finale

## Décision : ACCEPTED_WITH_RESERVATIONS

La recette fonctionnelle limitée est acceptée avec réserves :

1. les parcours atelier, inscription, prises multiples, idempotence,
   transcription, historique, validation, contrôles CSRF/IDOR et export sont
   passants ;
2. cinq codes de recette non consommés supplémentaires ont été créés pendant
   des échecs de capture de secret à affichage unique ; ils sont inventoriés et
   conservés, sans suppression ;
3. le contrôle rate limiting reste limité et aucun test de charge n’a été fait.

État final impératif : accès public fermé, aucun dégel général des écritures,
aucune suppression de données, aucune migration, aucun redémarrage, aucun
changement de secret et aucun push Git distant.
