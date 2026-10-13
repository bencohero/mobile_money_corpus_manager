# G2 — Tests applicatifs sur le schéma 0008

## Environnement

L’application candidate a démarré sur le clone restauré et migré, avec `/ready` en HTTP 200.
Le réseau était `g2-migration-network`; production utilise un réseau et des volumes distincts.
MinIO et PostgreSQL de production n’ont pas été connectés.

## Résultats

- Tests unitaires, intégration, HTTP, autorisations, CSRF et IDOR : inclus dans la suite complète.
- Transcription, vérification, historique, audio et MinIO : passés.
- Concurrence et limites de débit : passées.
- Réconciliation lecture seule : `[]`.
- `pip check` : `No broken requirements found`.
- `pip-audit -r requirements.txt` : `No known vulnerabilities found`.
- Suite complète candidate : **158 passed, 1 skipped, 8 warnings** en 144,15 s.

Le seul skip est `test_dev_environment`, qui exige le CLI Docker à l’intérieur du conteneur;
la configuration Compose a été validée séparément par `docker compose config --quiet`.
Les huit warnings sont des dépréciations Python/Starlette et ne signalent pas de perte de
données ni de vulnérabilité.

Une première passe a produit 11 échecs `401` liés aux mots de passe historiques restaurés,
avant exercice métier. Après réinitialisation du compte administrateur du clone uniquement,
la suite complète a passé sans échec.

