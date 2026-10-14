# Rapport — langues d’ateliers et identifiants participants

## Implémentation

- `languages` est le référentiel central initialisé avec `FR`, `MOS`, `DYU` et `FUL`.
- `workshops.language_code` est nullable pour préserver les ateliers historiques dont la langue n’est pas connue. La création administrative exige toutefois une langue valide.
- `participant_language_sequences` conserve un compteur indépendant par langue. L’attribution verrouille la ligne du compteur côté serveur et l’identifiant public reste protégé par l’unicité existante de `participants.participant_code`.
- Les identifiants sont formés comme `<CODE>_<N>` avec au moins trois chiffres et continuent au-delà de 999.
- `participant_registration_requests` conserve une empreinte et le résultat d’une clé d’idempotence afin qu’une répétition retourne le même identifiant.
- Les clés techniques et les relations internes restent fondées sur les identifiants numériques existants.

## Migration historique

La migration `0006_multilingual_participant_identity` ne renomme aucun participant et n’attribue pas de langue aux ateliers historiques. Elle initialise les compteurs à partir des identifiants publics déjà présents (`FR_NNN`, `MOS_NNN`, `DYU_NNN`, `FUL_NNN`).

Un administrateur doit attribuer explicitement `language_code` aux ateliers dont la valeur est nulle avant toute nouvelle inscription. Après la première inscription, l’interface refuse toute modification directe de langue.

La migration est volontairement non réversible automatiquement : supprimer les compteurs ou les reçus pourrait permettre la réutilisation d’identifiants. Une restauration doit se faire depuis une sauvegarde, écritures arrêtées.

## Compatibilité

Les exports existants utilisent toujours `participant_code` et les clés techniques originales; aucun champ d’enregistrement ou de transcription n’a été modifié. Les créations administratives et l’auto-inscription utilisent le même compteur par langue.

## Déploiement d’une base existante

Après sauvegarde et arrêt des écritures applicatives, appliquer la migration dans le réseau Docker :

```bash
docker compose stop app
docker compose run --rm --no-deps --entrypoint python app \
  -m alembic -c /app/alembic.ini upgrade head
docker compose run --rm --no-deps --entrypoint python app \
  -m alembic -c /app/alembic.ini current
docker compose up -d app
```

La dernière commande `current` doit afficher `0006_multilingual_participant_identity (head)`. Ne pas utiliser `alembic stamp` pour contourner la migration.
