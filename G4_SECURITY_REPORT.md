# G4 — Rapport sécurité et contrôles techniques

## Contrôles exécutés

- Tests CSRF, IDOR, authentification et autorisations : inclus dans les 158 tests verts.
- Concurrence et rate limiting : inclus dans la suite verte.
- Streaming audio et Range HTTP : inclus dans les tests HTTP/audio.
- Erreurs MinIO : incluses dans les tests MinIO.
- Health/readiness : readiness verte avant et après redémarrage.
- `docker compose config --quiet` : réussi.
- `python -m compileall -q app migrations scripts` : réussi.
- `bash -n scripts/*.sh` : réussi.
- Rapport de dépendances et de secrets F5/G3 conservé dans `security-reports-f1/`; aucun secret n’est reproduit dans ce rapport.

## Journaux et exposition

Les services G4 n’ont publié aucun port hôte. Les journaux d’application observés ne contenaient pas de secret. Les conteneurs de production et leurs réseaux sont restés hors cible.

## Réserves

Le scanner de dépendances exhaustif n’a pas été relancé dans un conteneur d’outils minimal ne contenant pas `pip`; `pip check` n’est donc pas une preuve disponible dans cette stack. Les rapports de sécurité versionnés de G3/F5 restent la preuve de référence et doivent être complétés par le scanner CI avant promotion.

La commande de démarrage de l’application de test lance Alembic automatiquement. Ce n’est pas une faille constatée sur le clone, mais c’est un risque opérationnel pour une promotion et doit être traité par une procédure de migration explicite.
