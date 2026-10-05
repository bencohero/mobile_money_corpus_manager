# Numérotation, API et exploitation des prises

## Règle métier

PostgreSQL attribue une séquence indépendante par `(participant_id, utterance_id, condition)`.
Une intention textuelle peut regrouper plusieurs utterances : elle ne participe pas à la clé.
CLEAN et NOISY sont indépendantes. Un rejet, une suppression ou un échec après réservation
ne libère jamais le numéro. Des trous sont donc normaux. La limite est 999 par combinaison.
Le compteur n'est jamais décrémenté ; ses clés étrangères RESTRICT empêchent sa disparition
par suppression en cascade d'un participant ou d'une utterance.

Un remplacement explicite doit conserver le recording et sa prise et ne doit pas appeler
l'allocateur. Aucune route de remplacement n'existait avant ce ticket et ce ticket n'en ajoute
pas : un POST de création est toujours une nouvelle capture, sauf répétition idempotente.

## Contrat API

`GET /api/recordings/next-take?utterance_id=…&condition=CLEAN&participant_id=…`
renvoie `{"next_take_number":3,"reserved":false}`. Il ne réserve rien. Pour un participant,
l'identité vient du compte ; un `participant_id` différent est refusé (403). Un admin doit
indiquer le participant. Consentement et activité du scénario sont vérifiés. Une combinaison
épuisée renvoie 409 avec une explication. Une estimation peut changer entre GET et POST.

`POST /api/recordings` reçoit un multipart : `audio`, `utterance_id`, `condition`,
`idempotency_key` (16 à 128 caractères ASCII alphanumériques, `-` ou `_`), et `participant_id`
pour un admin. Le jeton CSRF reste obligatoire. **Rupture explicite : `take_number` est refusé
avec 400, et `idempotency_key` est obligatoire (422 si absent).** Frontend et API doivent être
déployés ensemble ; recharger les anciens onglets.

Une réponse finale 200 contient `ok`, `recording_id`, `audio_id`, `take_number`, `status=READY`.
Un doublon déjà terminé retourne le même résultat. Un doublon encore en traitement retourne
202 avec les mêmes identifiants, `status=PENDING`, `Retry-After: 2` : renvoyer le même blob et
la même clé pour connaître l'issue. Ne pas interpréter tout HTTP 2xx comme un succès final.

La portée de la clé est l'utilisateur authentifié. L'empreinte inclut participant, utterance,
condition, type MIME et SHA-256 du brut. Une réutilisation avec contenu/contexte différent
renvoie 409 sans consommer un autre numéro. Deux utilisateurs peuvent employer la même clé
sans accéder au reçu de l'autre. Une capture distincte doit recevoir une nouvelle clé, même
si son contenu est identique. Le navigateur génère un UUID par capture et garde sa sélection
et sa clé pendant les retries. Les sélecteurs restent verrouillés jusqu'à succès ou annulation.

Un échec terminal après réservation renvoie le statut d'erreur (422, 429 ou 502) avec le reçu
`status=ERROR`. Ses répétitions renvoient ce même échec, sans réexécuter l'opération. Il faut
annuler et réaliser une nouvelle capture pour une nouvelle opération. Une erreur réseau
indéterminée (503) exige au contraire de conserver la même clé. Les reçus sont conservés sans
expiration, y compris après suppression : un retry d'une prise supprimée renvoie 410.

## Transactions et stockage

1. Autoriser le contexte et lire le brut par blocs bornés, calculer son empreinte.
2. Transaction courte : insérer le reçu unique `(user_id,idempotency_key)`, allouer via
   `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`, créer `Recording(PENDING)` et l'audit
   de réservation, puis commit. Une répétition n'appelle pas l'allocateur.
3. Sans transaction DB ouverte : convertir, vérifier format et durée, déposer les objets,
   puis relire leur taille et SHA-256 (lecture par blocs).
4. Transaction courte : enregistrer les checksums et passer recording + reçu à READY,
   avec l'audit de création dans le même commit.

Les chemins nouveaux sont `raw/<participant_id>/<uuid_serveur>/source.<extension>` et
`normalized/<participant_id>/<uuid_serveur>/audio.wav`. Les historiques gardent leurs chemins.
L'`audio_id` métier reste `<participant_code>_<utterance_code>_<condition>_Tnn`, utilisé pour
les fichiers exportés. Les exports CSV, JSONL et ZIP conservent leurs noms et colonnes ;
seules les lignes READY sont disponibles dans le corpus et les exports.

La compensation porte uniquement sur les deux chemins uniques de l'opération, même si le
PUT a expiré après son écriture distante. Avant toute suppression après échec de commit,
le serveur relit le reçu : READY signifie que le commit a réussi et les objets restent.
Si PostgreSQL est inaccessible, rien n'est supprimé et la réservation reste PENDING,
avec erreur contrôlée et réconciliation requise. Si ERROR est enregistré, la compensation
est tentée ; tout objet restant est détectable. Il n'y a pas de transaction distribuée.

## Migration et déploiement

Révision nouvelle : `0003_take_sequences`, après `0002_p0a_recording_sync`.
Les migrations précédentes ne changent pas. La nouvelle prend un verrou sur `recordings`,
refuse les numéros nuls/hors 1..999 et les doublons de la clé complète, crée les compteurs,
les initialise par MAX historique, répare `uq_recording_take` même sur une base estampillée
avec l'ancienne contrainte, ajoute `ck_recordings_take_range` et le registre d'idempotence.
Aucun historique, numéro ou objet n'est renommé ni supprimé.

Les suppressions antérieures à cette migration ne sont pas toutes reconstructibles à partir
de `MAX(recordings.take_number)`. Avant déploiement, rapprocher les anciens journaux/audits
si l'on exige de préserver aussi un maximum déjà supprimé avant l'introduction du compteur.
Ne jamais abaisser une valeur du compteur après sa mise en service.

Procédure :

1. Sauvegarder PostgreSQL et MinIO suivant `BACKUP_RESTORE.md`, vérifier la restauration isolée.
2. Passer l'application en maintenance et arrêter les producteurs d'uploads, y compris les
   anciennes instances. Attendre la fin des requêtes en cours.
3. Sur une copie, vérifier les doublons/plages et exécuter la migration avec le runtime ayant
   `migrations/`, Alembic et les paramètres habituels. La cible Docker `test` contient déjà
   ces éléments ; la cible `runtime` ne les embarque pas. Ne pas exposer le runner de migration.
4. Exécuter `alembic upgrade head` dans le runner configuré pour la base choisie ; vérifier
   `alembic current` et les contraintes via `pg_constraint`. La migration a un verrou exclusif :
   ne pas la lancer sous trafic.
5. Déployer frontend et API ensemble, recharger les onglets, vérifier première capture,
   changement de scénario/condition et retry idempotent, puis lancer la réconciliation.
6. Conserver les volumes et les sauvegardes ; ne jamais employer `down -v`.

## Réconciliation et incidents

`python scripts/reconcile.py --json` est en lecture seule. Un retour non nul indique un
constat : absence d'objet READY, checksum/taille divergent, objet orphelin, réservation
intermédiaire ou objet résiduel d'une opération ERROR. Les absences après compensation d'une
opération ERROR sont attendues ; ERROR reste signalé comme `intermediate_recording`.
Les résidus sont signalés `failed_recording_object`. Une panne de lecture reste une panne,
elle n'est jamais traitée comme une absence.

Pour un PENDING ancien : arrêter/identifier le worker propriétaire et vérifier qu'il est
bien terminé avant toute intervention. Inspecter le reçu et les objets ; valider les deux
objets et la transaction si leur origine est prouvée, ou marquer ERROR puis traiter les
résidus par une procédure administrateur revue. Ne pas relancer aveuglément un PUT avec
l'ancien UUID. Le compteur reste consommé. Aucune récupération automatique après crash
n'est introduite par ce ticket.

Les quatre orphelins historiques recensés par l'audit ne sont pas nettoyés automatiquement.
Traitement manuel séparé : inventorier dans un espace restreint, sauvegarder, rapprocher les
anciens exports/journaux, attribuer un propriétaire ou documenter l'absence de référence,
puis faire approuver chaque action nominative. Aucun script de suppression en masse n'est
fourni. Les chemins peuvent identifier des participants : ne pas publier la sortie brute.

## Retour arrière

Le downgrade Alembic est volontairement refusé : supprimer compteurs/reçus autoriserait une
réutilisation silencieuse de numéros. En incident, mettre en maintenance, conserver le schéma,
les compteurs, reçus et objets, et corriger en avant. On peut restaurer l'ancienne application
pour consultation uniquement, avec POST de création bloqué au proxy. Ne pas rouvrir l'ancien
allocateur frontend. Une restauration complète depuis sauvegarde nécessite un plan de
rapprochement des prises/numéros créés depuis la sauvegarde et une décision explicite.

## Tests reproductibles dans la pile dédiée

Ne pas utiliser `scripts/validate_p0a2.sh` pour ce ticket : son nettoyage supprime les volumes.

```sh
docker compose -f docker-compose.test.yml build app-test test
docker compose -f docker-compose.test.yml up -d db-test minio-test app-test
docker compose -f docker-compose.test.yml run --no-deps test pytest -q --disable-warnings
node --test tests/record_capture.test.cjs
docker compose -f docker-compose.test.yml run --no-deps test python scripts/reconcile.py --json
```

Les tests nouveaux refusent les écritures hors `db-test/p0a2_test`. Les répétitions de tests
historiques maintiennent leurs données synthétiques dans cette pile. Les répétitions de la
suite ne réinitialisent jamais les volumes. Les tests de migration créent un schéma isolé
dans une transaction puis annulent cette transaction.
