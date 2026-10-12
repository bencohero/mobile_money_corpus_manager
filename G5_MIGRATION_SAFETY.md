# G5 — Sécurité des migrations

## Changement appliqué

Les commandes de démarrage de `docker-compose.test.yml` et `docker-compose.e1.test.yml` lancent désormais Uvicorn directement. Elles ne contiennent plus `alembic upgrade`. La migration est opérée explicitement par `scripts/migrate.sh`, avec `ALEMBIC_TARGET` optionnel et affichage de la révision courante.

Le démarrage applicatif appelle uniquement `assert_schema_current()` via `app.main.startup()`. Une révision absente, ancienne ou divergente lève `SchemaRevisionError` et empêche le service de devenir prêt; aucune écriture Alembic n’est effectuée. La readiness ne remplace pas ce refus de démarrage.

## Preuves

- Stack G5 neuve, réseau `mobile-money-corpus-g5-validation`, volumes dédiés et aucun port publié.
- Archive F5A7.2 restaurée au schéma `0005_workshop_attribution` : 17 participants, 15 enregistrements, 1 transcription.
- `scripts/migrate.sh` a amené le clone à `0008_rate_limit_buckets` : 17 participants, 15 enregistrements, 1 transcription, 1 historique baseline, 0 bucket initial.
- Redémarrage de l’application au schéma 0008 : readiness 200, journal sans `alembic` ni `upgrade head`.
- Tests de garde et environnement : 5 pass, 1 skip; suite complète : 159 pass, 1 skip, 8 warnings.

Les états 0005 et 0008 sont vérifiés directement; les transitions 0006 et 0007 ont été exécutées par Alembic dans le trajet explicite G2/G5. Toute migration réelle devra être lancée séparément, avec autorisation et sauvegarde immédiate préalable.
