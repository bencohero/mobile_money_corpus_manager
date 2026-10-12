# G3 — Décision finale

## Décision : `CANDIDATE_READY_WITH_WARNINGS`

La branche candidate `g3-candidate` est prête pour une préproduction contrôlée. Elle part de
`main@32edc87`, intègre les remédiations applicatives validées de
`remediation-a-stabilisation-securite@b672697`, atteint `0008_rate_limit_buckets`, conserve les
scripts et preuves F5A6–F5A8 de `main`, et passe la validation complète sur un nouveau clone de
F5A7.2.

## Conditions et réserves

1. `test_dev_environment` reste ignoré faute de CLI Docker dans le conteneur; Compose est validé
   séparément.
2. Huit warnings de dépréciation restent non bloquants.
3. Les tests applicatifs ajoutent des données de test au clone; la preuve de conservation est
   prise avant ces tests, à 17/15/1.
4. Aucun merge vers `main`, déploiement ou migration de production n’est autorisé par ce ticket.

Une approbation distincte est requise avant toute promotion préproduction ou intégration dans
`main`.

