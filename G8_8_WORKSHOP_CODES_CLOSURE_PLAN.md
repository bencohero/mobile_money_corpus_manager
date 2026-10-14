# G8.8 — Plan de fermeture des codes recette

## État contrôlé

- ids 7–11 : actifs, zéro utilisation chacun, limite 1 ;
- id 12 : actif, une utilisation sur une limite de 1 ;
- aucune date d’expiration ; aucun code déjà révoqué ;
- aucune inscription en attente ; participant `MOS_018` et compte associé
  présents.

## Actions proposées, non exécutées

1. Capturer l’inventaire et l’audit avant action.
2. Révoquer par interface admin les codes 7–11, un par un, avec contrôle de
   réponse et audit.
3. Fermer le code 12 par interface admin après décision de conservation du
   participant recette ; ne pas supprimer ses données.
4. Capturer l’inventaire après action et vérifier `is_active=false` pour 7–12.
5. Vérifier qu’un lookup public de chaque code échoue sans révéler le secret.
6. Comparer les audits avant/après ; toute autre différence est un STOP.

L’exécution nécessite une autorisation distincte de révocation/fermeture.
