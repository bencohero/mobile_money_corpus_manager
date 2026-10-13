# G1 — Plan d’intégration

L’intégration doit se faire par lots, dans des clones isolés de la restauration F5A7.2. Chaque lot est arrêté à la première anomalie ; aucun rollback par downgrade n’est requis ou autorisé sur la production.

## Lot 0 — Baseline

- Références : `main@32edc87`, archive F5A7.2, schéma `0005`.
- Actions : figer l’inventaire, comparer le script F5 de `main` avec celui de la branche courante, créer un clone de test.
- Tests : manifestes, `pg_restore --list`, comptages, inventaire MinIO et requêtes métier en lecture.
- Acceptation : baseline reproductible, sans différence inexpliquée.
- Retour arrière : supprimer uniquement les ressources temporaires identifiées, ou recréer le clone depuis l’archive.

## Lot 1 — Langues et participant

- Révisions : `390cc74`, `5457b1e`, migration `0006`.
- Dépendances : modèles participant/workshop, interface, séquences.
- Tests : migration sur clone, création/édition participant, séquences par langue, accès et tests HTTP.
- Risques : valeurs par défaut, données existantes et contrats API.
- Acceptation : aucun orphelin, comptages conservés, tests unitaires et intégration verts.

## Lot 2 — Transcription et vérification

- Révision : `9279a2a`, migration `0007`.
- Dépendance : Lot 1 et diagnostics d’intégrité.
- Tests : historique, version optimiste, validation, suppression/liaison d’enregistrement, restauration du clone.
- Risques : perte de référence, concurrence et downgrade impossible.
- Acceptation : historique cohérent et aucune modification non attendue des données restaurées.

## Lot 3 — Audio, export, pagination et débit

- Révision : `d34e96a`, migration `0008`.
- Dépendances : MinIO de test, API audio, modèles des lots précédents.
- Tests : lecture WAV, range requests, export, pagination, rate-limit concurrent et bucket expiré.
- Risques : objets manquants, fuite inter-participant, état de quota incohérent.
- Acceptation : références et objets concordants, aucune suppression source, tests de charge bornés.

## Lot 4 — Sécurité et exploitation

- Révisions : `5377f43`, `75eb4f8`.
- Dépendances : contrats API stabilisés et schéma validé.
- Tests : authentification, autorisations, CSP/JWT, audit, scans de dépendances/secrets, health/readiness.
- Risques : blocage opérateur, changement de session et configuration divergente.
- Acceptation : scans propres, tests négatifs verts, secrets absents des logs.

## Lot 5 — Préproduction et sauvegarde

- Révisions : `cb87475`, `704f980`, puis comparaison ciblée de `b672697` avec `main@32edc87`.
- Dépendances : lots 1–4 validés ; contrôles F5 conservés.
- Tests : compose préproduction, dry-run synthétique, gel d’écriture, sauvegarde/restauration isolée.
- Risques : mélange des scripts F5, cible Docker erronée, faux gel d’écriture.
- Acceptation : validation indépendante et approbation explicite avant toute opération réelle.

## Gouvernance de chaque lot

Avant intégration : revue du diff, tests sur clone, rapport d’acceptation et décision explicite. L’intégration Git se fera ensuite par commit ou lot cohérent approuvé ; aucun merge ou cherry-pick n’est autorisé dans ce ticket. Le retour arrière se fait par restauration d’un clone/snapshot connu, jamais par modification de la base de production.

