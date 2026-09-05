# P0-A.1 - Validation technique
La validation utilise docker-compose.test.yml avec le projet explicite mobile-money-corpus-p0a1-test, le reseau bridge mobile-money-corpus-p0a1-test et deux volumes dedies. Aucun port n'est publie.
Commande principale: docker compose -f docker-compose.test.yml build puis docker compose -f docker-compose.test.yml run --rm test pytest -q -ra.
La cible production reste runtime et ne copie pas tests, migrations ou scripts. La cible test les copie.
La revision 0001 cree le schema avec des operations Alembic explicites; 0002 ajoute les colonnes P0-A. Pour une base existante, sauvegarder, inspecter les colonnes et contraintes, appliquer une migration corrective si necessaire, puis seulement stamp la revision compatible. Ne jamais stamp sans rapport de compatibilite.
Le nettoyage cible uniquement le projet explicite: docker compose -p mobile-money-corpus-p0a1-test down --volumes --remove-orphans. Verifier les noms avant execution et ne pas utiliser cette commande sur la composition principale.
La sauvegarde/restauration complete depend de pg_dump, pg_restore et mc. Elle doit utiliser les conteneurs de test et des cibles PostgreSQL/MinIO distinctes; aucun resultat n'est declare ici sans execution effective.

## Suite
P0-A.2: voir docs/P0A2_INTEGRATION_RECOVERY.md et RAPPORT_VALIDATION_P0A2.md.
