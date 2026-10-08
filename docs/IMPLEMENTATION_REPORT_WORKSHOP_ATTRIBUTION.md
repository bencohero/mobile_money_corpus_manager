# Rapport d’implémentation — rattachement aux ateliers

## Décision

`Workshop` est une entité métier durable distincte de `WorkshopCode`. Les codes peuvent
être multiples pour un atelier. Les participants, enregistrements et reçus idempotents
portent un `workshop_id` persistant. Les enregistrements conservent cet instantané lors d’un
éventuel transfert futur.

Les données historiques sont rattachées à `Atelier historique — à confirmer`, conformément
à la décision métier validée. La migration bloque toute ligne restant ambiguë.

## Livrables

- modèle et relations : `app/models.py` ;
- garde serveur : `app/workshops.py` ;
- inscription et idempotence : `app/participant_registration.py`, `app/recording_submission.py` ;
- routes, filtres administratifs et désactivation : `app/main.py` ;
- exports CSV, JSONL et ZIP : `app/corpus_export.py` ;
- migration : `migrations/versions/0005_workshop_attribution.py` ;
- diagnostic lecture seule : `scripts/diagnose_workshop_migration.py` ;
- documentation d’exploitation : `docs/WORKSHOP_ATTRIBUTION.md` ;
- tests et fixtures adaptés : `tests/test_migrations.py`, `tests/test_participant_registration.py`,
  `tests/test_take_sequence.py`, `tests/test_remediation_evidence.py`.

## Vérifications exécutées

- `git status --short` avant modification ; changements préexistants conservés ;
- `docker compose config --quiet` : réussi ;
- `docker compose -f docker-compose.test.yml config --quiet` : réussi ;
- build des images `test` et `app-test` : réussi ;
- migration `0005` appliquée uniquement à `db-test` ;
- diagnostic test : 0 participant sans atelier, 0 enregistrement sans atelier,
  0 incohérence ;
- tests ciblés modèle/inscription/export/migration : `49 passed, 4 deselected` ;
- test de séquence d’enregistrement : `1 passed, 18 deselected` ;
- `python3 -m py_compile` : réussi ;
- `git diff --check` : réussi.

La base applicative Docker n’a pas été migrée : elle est restée en
`0004_participant_registration`. Aucun commit, push ou migration de production n’a été effectué.

## Retour arrière

Le downgrade `0005` est volontairement bloqué. Le retour arrière exige l’arrêt des écritures,
le déploiement de l’image précédente et la restauration d’une sauvegarde pré-migration dans
une base contrôlée.

## Risques résiduels

- la migration `0005` doit être exécutée avec sauvegarde et fenêtre d’écriture arrêtée ;
- le transfert administratif n’est pas activé, conformément à la décision de ne pas l’inventer ;
- plusieurs tests historiques volumineux de concurrence/infrastructure restent à rejouer sur
  une base de test fraîche après nettoyage des conteneurs orphelins existants.
