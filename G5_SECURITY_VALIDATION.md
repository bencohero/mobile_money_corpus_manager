# G5 — Validation sécurité

## Résultats

- `pip check` : `No broken requirements found`.
- `pip-audit` sur `requirements.txt` : `No known vulnerabilities found`.
- Bandit dans un conteneur éphémère : 4 résultats, correspondant aux contrôles déjà connus autour de subprocess; aucune nouvelle exposition critique identifiée. Le rapport détaillé n’est pas copié dans le dépôt pour éviter toute fuite de contexte inutile.
- Recherche de motifs de secrets dans le dépôt/diff : 0 fichier correspondant aux motifs de clés privées, AWS ou tokens Git.
- Dépendances JavaScript : aucun `package.json` ou `package-lock.json`; SCA JavaScript non applicable.
- Tests d’authentification, CSRF, IDOR, autorisations, concurrence et rate limiting : inclus dans 159 tests verts.
- Compose : configurations test/E1/G5 valides; réseau G5 dédié et aucun port publié.

Les scripts de sauvegarde F5A6–F5A8 n’ont pas été remplacés. Aucun secret n’est inclus dans les livrables G5.
