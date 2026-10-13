# G8.6-S — Procédure de rotation sécurisée proposée

Cette procédure est une proposition uniquement. Elle n'a pas été exécutée.

## Garde-fous

1. Maintenir l'accès public fermé et les écritures métier gelées.
2. Obtenir une approbation distincte pour la rotation et identifier l'opérateur
   break-glass.
3. Capturer avant opération un manifeste PostgreSQL/MinIO et une sauvegarde
   vérifiée ; ne pas modifier les volumes ni appliquer de rollback partiel.
4. Générer un nouveau secret aléatoire hors du dépôt, le transmettre par le
   gestionnaire de secrets autorisé et ne jamais l'inscrire dans un rapport,
   une commande shell persistante ou les logs.

## Rotation du compte

Le simple remplacement de `ADMIN_PASSWORD` dans `.env` est insuffisant : le
code actuel n'actualise pas les utilisateurs existants.

La rotation doit donc passer par une procédure approuvée et traçable, dans cet
ordre :

1. vérifier l'identité exacte du compte opérateur à rétablir ;
2. exécuter une commande de maintenance dédiée, versionnée et à usage unique,
   qui génère le hash avec le même mécanisme bcrypt que l'application et met à
   jour uniquement ce compte dans une transaction ;
3. vérifier avant commit que le compte est bien `ADMIN`, actif, et que le nombre
   de comptes et les relations métier restent inchangés ;
4. ne pas modifier les comptes historiques `admin` ou `laurent` sans mandat
   explicite ;
5. conserver l'audit de l'opération sans enregistrer le secret ni le hash.

Si une telle commande n'est pas déjà approuvée, elle doit être ajoutée et
revue avant l'opération. Une modification SQL ad hoc depuis un shell n'est pas
la procédure recommandée.

## Mise à jour de l'environnement et vérification

Après la rotation transactionnelle :

1. remplacer la valeur `ADMIN_PASSWORD` du secret runtime par le nouveau secret
   (sans l'ajouter au Git) ;
2. redémarrer uniquement le conteneur applicatif autorisé, si nécessaire, sans
   recréer les volumes ;
3. vérifier `/ready`, `/health`, la release, Alembic et l'absence de migration
   implicite ;
4. tester une connexion interne via le chemin normal `/login`, avec le nouveau
   secret, puis vérifier qu'un ancien secret est refusé ;
5. vérifier les comptages, les objets MinIO et les journaux d'audit.

La rotation du mot de passe admin ne doit pas être confondue avec une rotation
de `JWT_SECRET`. Cette dernière invaliderait les sessions JWT existantes et
nécessite une approbation séparée.

## Reprise de G8.6-R

Après preuve de connexion valide, reprendre la recette avec les mêmes garde-fous
et identités dédiées. Le middleware peut rester techniquement `OPEN` pendant
la recette limitée, mais aucune opération hors périmètre ne doit être envoyée.
Les données de recette restent conservées jusqu'à une autorisation distincte de
nettoyage.

