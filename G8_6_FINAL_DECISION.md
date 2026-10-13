# G8.6 — Décision finale

## `BLOCKED`

Les contrôles préalables, readiness, schéma Alembic, réseau fermé, contrôle des
hôtes, refus d'accès, isolation des rôles, IDOR audio, plages HTTP et intégrité
des données historiques sont satisfaisants.

La décision ne peut toutefois pas être `READY_FOR_PUBLIC_OPENING_REVIEW` :

1. les scénarios d'écriture métier obligatoires de la phase C n'ont pas été
   exécutés, le gel opérationnel étant maintenu ;
2. les identités et données de recette dédiées n'ont pas été approuvées ni
   préparées dans la production cible ;
3. la méthode de nettoyage de toutes les dépendances n'est donc pas démontrée ;
4. un test présenté comme lecture (`workshop-language`) a créé/incrémenté un
   bucket persistant, conservé sans suppression destructive.

## Conditions de reprise

Obtenir une approbation de recette limitée, préparer le manifeste DB/MinIO
avant-test, exécuter seulement les écritures dédiées avec identifiants de
corrélation, produire le manifeste après-test, puis nettoyer uniquement les
objets et lignes dont la propriété et les dépendances sont démontrées. Refaire
les contrôles de comptage, d'objets historiques et de rate limiting avant toute
revue d'ouverture publique.

L'accès public reste fermé et les écritures ordinaires restent gelées.
