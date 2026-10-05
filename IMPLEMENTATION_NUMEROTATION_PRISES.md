# Implémentation de la numérotation des prises audio

## 1. Cause racine rappelée

Le défaut venait d’un compteur global maintenu dans le navigateur (`#take`). Le client l’incrémentait après chaque envoi et l’API acceptait directement `take_number`, sans allocation serveur. Un changement d’utterance, de condition ou de participant ne recalculait donc pas la séquence métier. PostgreSQL vérifiait certaines contraintes mais n’était pas l’autorité d’attribution.

## 2. Décisions d’architecture appliquées

- Clé de séquence : `(participant_id, utterance_id, condition)`.
- Table dédiée `recording_take_counters`, avec allocation PostgreSQL atomique par `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`.
- Limite métier `1..999`; dépassement explicite par erreur métier.
- Les prises rejetées, supprimées ou interrompues après réservation consomment leur numéro; les trous ne sont pas réutilisés.
- Une prise en remplacement conserve son numéro.
- Le navigateur ne peut plus imposer le numéro définitif.
- Une prévisualisation `GET /api/recordings/next-take` est informative uniquement; le `POST` réalloue toujours côté serveur.
- Les soumissions sont idempotentes via `recording_submissions` et une clé d’idempotence liée à l’utilisateur.
- Les objets MinIO utilisent l’identité unique de l’opération/du recording, indépendamment de l’`audio_id` lisible.

## 3. Fichiers modifiés ou ajoutés

Fichiers du ticket :

- `app/models.py` : compteur, reçu d’idempotence, contraintes et états.
- `app/take_sequence.py` : allocation atomique et estimation.
- `app/recording_submission.py` : réservation, finalisation, erreurs et idempotence.
- `app/main.py` : API POST, endpoint de prévisualisation, filtrage READY, suppression et permissions.
- `app/storage.py` : vérification taille/SHA-256 après téléversement.
- `app/templates/record.html` et `app/static/record_capture.js` : prévisualisation, verrouillage de la sélection, retry idempotent et anti-double soumission.
- `scripts/reconcile.py` : états PENDING/ERROR et compensation limitée aux objets de l’opération.
- `migrations/versions/0003_take_sequences.py` : migration et correction de dérive de contrainte.
- `tests/test_take_sequence.py`, `tests/test_take_migration.py`, `tests/record_capture.test.cjs` et adaptations des tests existants.
- `docs/TAKE_SEQUENCES.md`, `docs/INCIDENT_RUNBOOK.md`, `README.md` : exploitation, migration et comportement métier.

Les changements préexistants du worktree (`app/corpus_export.py`, `app/templates/export.html`, `docs/CORPUS_EXPORT.md`, modifications d’export dans `app/main.py`/`base.html`, ainsi que `graphify-out/`) ont été conservés et ne sont pas attribués à ce ticket.

## 4. Migration créée

La migration `0003_take_sequences` (parent `0002_p0a_recording_sync`) :

1. verrouille les enregistrements pendant les contrôles;
2. refuse les doublons incompatibles, numéros nuls ou hors limites;
3. crée `recording_take_counters` et l’initialise avec le `MAX(take_number)` historique;
4. remplace explicitement l’ancienne contrainte `(participant_id, utterance_id, take_number)` par `(participant_id, utterance_id, condition, take_number)`;
5. ajoute `CHECK(take_number BETWEEN 1 AND 999)`;
6. crée le ledger `recording_submissions` et son unicité `(user_id, idempotency_key)`.

Aucune migration déjà appliquée n’a été réécrite et aucune donnée historique n’est renumérotée. Le downgrade est volontairement bloqué afin de ne pas perdre l’historique d’allocation.

## 5. Comportement avant / après

Avant, deux intentions successives pouvaient produire `1, 2, 3` dans un compteur global côté navigateur. Après, chaque combinaison participant–utterance–condition dispose de sa propre séquence : changer de combinaison affiche une estimation indépendante, revenir à une combinaison reprend son prochain numéro, et la réponse POST contient le numéro effectivement attribué.

Le champ client `take_number` est rejeté explicitement. Une estimation obsolète dans un autre onglet n’influence jamais l’allocation autoritative.

## 6. Schéma d’allocation

```text
POST + idempotency_key
  → validation participant/utterance/condition/consent/audio
  → INSERT/UPDATE atomique recording_take_counters
  → Recording PENDING + reçu d’opération
  → conversion et PUT sous clés MinIO uniques
  → vérification taille + SHA-256
  → Recording READY et réponse avec take_number définitif
```

La transaction PostgreSQL n’est pas conservée pendant FFmpeg ou MinIO. Un échec laisse un état explicite réconciliable; le numéro reste consommé.

## 7. Idempotence

Le frontend génère une clé pour chaque nouvelle capture et la conserve lors des retries du même blob. Le serveur compare utilisateur, participant et empreinte audio. Une même clé avec la même empreinte retourne le même reçu; une réutilisation avec une autre empreinte ou un autre participant est rejetée.

## 8. Stratégie PostgreSQL–MinIO

Chaque opération possède ses propres chemins `raw/<participant>/<operation>/source.*` et `normalized/<participant>/<operation>/audio.wav`; aucune requête concurrente ne partage donc une clé physique. La compensation ne supprime que les objets créés par l’opération courante. Si la finalisation PostgreSQL est incertaine, les objets sont conservés pour réconciliation au lieu d’être supprimés à tort. Les quatre objets orphelins historiques ne sont pas supprimés automatiquement.

## 9. Tests ajoutés et résultats

- Suite pytest isolée : **88 passed**, avec avertissements de dépréciation uniquement.
- Tests Node du contrôleur de capture : **4 passed**.
- Tests ciblés séquence/migration/réconciliation : **23 passed**.
- Intégration HTTP : **2 passed**.
- Scénarios P0A négatifs : **6 passed**.
- Remédiation/preuves : **14 passed**.
- Export : **14 passed**.
- Compose production et test validés par `docker compose ... config --quiet`.
- Compilation Python et `git diff --check` validés.
- Schéma du conteneur de test vérifié : révision `0003_take_sequences`, contrainte unique avec `condition` et `ck_recordings_take_range`.

Les tests de concurrence vérifient les numéros distincts, les deux objets MinIO, leurs tailles/SHA-256 et l’absence de suppression croisée. Les tests couvrent également rejet, suppression, limite 999, migration d’un ancien schéma, idempotence et erreurs partielles.

## 10. Données historiques vérifiées

La migration ne renumérote pas les 78 enregistrements historiques audités. Elle initialise les compteurs à partir de leur maximum par clé et refuse les anomalies incompatibles. Les contrôles de diagnostic de l’audit ont trouvé des séquences globales partagées et quatre objets MinIO orphelins; ceux-ci restent à traiter manuellement selon la procédure documentée.

## 11. Risques résiduels

- Le déploiement de `0003` doit être réalisé en fenêtre de maintenance à cause du verrou de migration.
- Les avertissements Python de dépréciation (`datetime.utcnow`) restent sans impact fonctionnel immédiat.
- Les objets orphelins antérieurs nécessitent une décision opérateur et une procédure manuelle.
- Une panne prolongée entre MinIO et PostgreSQL peut laisser un état PENDING/ERROR qui doit être traité par réconciliation.

## 12. Vérifications manuelles nécessaires

En environnement de recette, vérifier l’enregistrement depuis deux onglets, le changement participant/utterance/condition pendant la capture, les retries après erreur réseau, la reprise de réconciliation et les exports ZIP/CSV/JSONL. Ne pas exécuter ces scénarios sur les données de production sans fenêtre et sauvegarde approuvées.

## 13. Déploiement et retour arrière

Déploiement : appliquer `alembic upgrade head`, déployer API et frontend ensemble, puis exécuter les tests de fumée et la réconciliation en lecture seule. Retour arrière applicatif : redéployer la version précédente sans rétrograder la base; les nouveaux états restent lisibles par les scripts de réconciliation. La migration n’a pas de downgrade automatique afin d’éviter la perte de compteurs et de reçus.

## 14. État final du worktree

Aucun commit ni push n’a été effectué. `git diff --check` est propre. Les modifications suivies concernent `README.md`, `app/main.py`, `app/models.py`, `app/storage.py`, `app/templates/base.html`, `app/templates/record.html`, `docs/INCIDENT_RUNBOOK.md` et les tests adaptés. Les nouveaux fichiers du ticket sont `IMPLEMENTATION_NUMEROTATION_PRISES.md`, `app/recording_submission.py`, `app/static/record_capture.js`, `app/take_sequence.py`, `migrations/versions/0003_take_sequences.py`, `tests/record_capture.test.cjs`, `tests/test_take_migration.py`, `tests/test_take_sequence.py` et `docs/TAKE_SEQUENCES.md`. Les fichiers d’export et `graphify-out/` restent des artefacts préexistants conservés volontairement.
