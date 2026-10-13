# G8.6-R — Plan de reprise après restauration d'authentification

## Statut

`READY_FOR_G8_6_R_APPROVAL` — préparation uniquement. Aucun test d'écriture
G8.6-R n'est exécuté par ce plan.

## Garde-fous maintenus

- accès public fermé ; aucun port publié et aucune modification Traefik ;
- écritures métier générales gelées ;
- pas de migration, redémarrage, rollback ou suppression de volume ;
- `JWT_SECRET` inchangé ;
- aucune suppression automatique des données de recette.

## Préparation requise avant approbation d'exécution

Créer uniquement via les parcours applicatifs autorisés, après nouveau manifeste
PostgreSQL/MinIO :

1. atelier dédié marqué `G8_6_R_<date>` avec code d'inscription limité ;
2. identités distinctes : participant, transcripteur et vérificateur ;
3. compte admin de recette uniquement si la procédure d'administration autorisée
   le permet ; sinon utiliser `benco` comme opérateur sans créer d'ADMIN ;
4. deux phrases de test isolées et un fichier audio synthétique sans donnée
   personnelle ;
5. identifiants de corrélation et clés d'idempotence documentés avant chaque
   écriture.

Les identités historiques et les ateliers existants ne doivent pas être
réutilisés comme données de recette.

## Scénarios autorisables

Après approbation distincte : inscription, session, upload synthétique, seconde
prise, `take_number`, rejeu idempotent, transcription, historisation,
vérification, IDOR/permissions, export filtré au corpus de recette et contrôle
non agressif du rate limiter. Les tests de charge restent interdits.

## Intégrité et conservation

Capturer les compteurs et l'inventaire MinIO avant/après. Les seules différences
acceptables sont les lignes, objets, audits et buckets explicitement rattachés à
la recette. Les données de recette doivent être conservées par défaut.

Tout nettoyage nécessite une autorisation distincte, un plan de dépendances
exact et une validation avant suppression. En cas de doute, ne rien supprimer.
