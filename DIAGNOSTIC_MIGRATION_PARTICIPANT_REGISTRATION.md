# Diagnostic de l’échec de l’auto-inscription participant

Date du diagnostic : 2026-10-05  
Mode : lecture seule

## 1. Résumé exécutif

La cause racine est une dérive entre l’image runtime et la base PostgreSQL :

- PostgreSQL est à la révision `0002_p0a_recording_sync`.
- Le code runtime appelle `nextval('participant_login_number_seq')`, objet créé uniquement par la migration `0004_participant_registration`.
- L’image runtime utilise la cible Docker `runtime`, qui copie `app/` mais pas `migrations/` ni `alembic.ini`.
- L’application démarre avec `APP_ENV=development` par défaut, car `APP_ENV` est absent de l’environnement observé. `startup()` exécute donc `Base.metadata.create_all(engine)`.
- `create_all()` a créé `workshop_codes` à partir du modèle ORM, mais ne peut pas créer la séquence PostgreSQL explicitement déclarée uniquement dans Alembic.

La table `workshop_codes` est donc utilisable, ce qui explique le `201 Created`, tandis que la séquence manque et provoque le `500`.

Le lancement direct de `alembic upgrade head` contre la base active n’est pas une correction sûre : après les premières opérations de `0004`, la création de `workshop_codes` rencontrerait `DuplicateTable`. PostgreSQL annulerait vraisemblablement la transaction de migration, mais l’opération échouerait et ne doit pas être utilisée comme procédure de réconciliation.

La réponse d’exception non gérée est `500 text/plain; charset=utf-8` avec le corps `Internal Server Error`. Le frontend appelle directement `response.json()` ; cette combinaison explique `JSON.parse: unexpected character at line 1 column 1`.

## 2. Chronologie observée

Les logs runtime montrent, dans cet ordre :

1. démarrage Uvicorn réussi ;
2. `GET /admin/workshop-codes` → `200` ;
3. `POST /admin/workshop-codes` → `201 Created` ;
4. `GET /participant/register` et son JavaScript → `200` ;
5. `POST /api/auth/participant-registration` → `500` ;
6. traceback `psycopg.errors.UndefinedTable` sur `SELECT nextval('participant_login_number_seq')`.

Le log ne contient pas de mot de passe, code atelier, hash ou clé secrète.

## 3. État Git

Commandes exécutées au début :

```text
pwd
git status --short
git log -5 --oneline
```

Le worktree contenait déjà les changements du ticket d’auto-inscription : `.env.example`, `README.md`, `app/config.py`, `app/main.py`, `app/models.py`, templates, tests et les nouveaux services/migration. Le dernier commit observé était `99d81b7 Fix utter counter`.

Le diagnostic n’a modifié aucun de ces fichiers. Le seul fichier ajouté par cette intervention est le présent rapport, conformément au livrable demandé. Aucun commit ni push n’a été effectué.

## 4. Configuration Alembic sur l’hôte

Fichiers présents :

```text
./alembic.ini
./migrations/env.py
./migrations/versions/0001_initial.py
./migrations/versions/0002_p0a_recording_sync.py
./migrations/versions/0003_take_sequences.py
./migrations/versions/0004_participant_self_registration.py
```

`alembic.ini` contient :

```ini
[alembic]
script_location = migrations
sqlalchemy.url =
```

L’URL est volontairement vide ; `migrations/env.py` la remplace à partir de la configuration applicative. Cette configuration fonctionne depuis la racine du dépôt, si le fichier est présent.

## 5. Contenu de l’image runtime

Preuves observées :

- `WORKDIR /app` dans `Dockerfile`.
- La cible `runtime` copie uniquement `app/`.
- `migrations/`, `alembic.ini`, `scripts/` et `tests/` sont copiés uniquement dans la cible `test`.
- `docker-compose.yml` construit `target: runtime` et démarre directement Uvicorn.
- Aucun volume ne monte le dépôt ou `/app`; seul `/tmp/audio` est monté.
- Dans le conteneur runtime, `/app` contient `app/` et `requirements.txt`, mais aucun `alembic.ini`, aucun `migrations/` et aucune migration `0004`.
- `docker compose exec -T app alembic current` retourne exactement :

```text
FAILED: No 'script_location' key found in configuration.
```

Dans l’image de test, en revanche, `alembic -c /app/alembic.ini current` fonctionne et retourne :

```text
0004_participant_registration (head)
```

## 6. Révisions Alembic

La base PostgreSQL runtime retourne :

```text
0002_p0a_recording_sync
```

La chaîne de migrations disponible sur l’hôte et dans l’image de test est :

```text
0001_initial
0002_p0a_recording_sync
0003_take_sequences
0004_participant_registration (head)
```

La migration `0004` déclare `down_revision = "0003_take_sequences"`, crée la séquence à la ligne 58, initialise son maximum historique aux lignes 59–70 et crée `workshop_codes` aux lignes 72–91. Son downgrade est explicitement bloqué aux lignes 94–97.

## 7. Schéma PostgreSQL observé

Requêtes de métadonnées exécutées sans modification : `alembic_version`, `to_regclass`, `pg_class`, `information_schema.columns`, `pg_constraint` et `pg_indexes`.

Résultats importants :

| Objet | Attendu par `0004` | Observé dans PostgreSQL | État |
|---|---|---|---|
| `participant_login_number_seq` | Présent | Absent | Dérive confirmée |
| `workshop_codes` | Créé par `0004` | Présent | Création prématurée |
| `users.participant_id` unique | `uq_users_participant_id` | FK seulement, aucune unicité | Dérive confirmée |
| Index de fenêtre atelier | `ix_workshop_codes_active_window` | Absent | Dérive confirmée |
| Index `code_hash` | Index unique | Présent (`ix_workshop_codes_code_hash`) | Partiellement cohérent |
| Révision Alembic | `0004` | `0002` | Dérive confirmée |

`workshop_codes` contient une ligne, la base contient zéro participant et un utilisateur initial. Les empreintes de codes, mots de passe et secrets n’ont pas été sélectionnés.

Colonnes observées de `workshop_codes` : `id`, `label`, `code_hash`, `is_active`, `starts_at`, `expires_at`, `max_registrations`, `use_count`, `created_by_user_id`, `created_at`, `disabled_at`.

Les contraintes présentes sont les trois checks de capacité, la PK et la FK vers `users`. La contrainte nommée `uq_workshop_codes_code_hash` prévue par la migration n’est pas présente ; seul l’index unique ORM `ix_workshop_codes_code_hash` existe.

Les colonnes `created_at`, `is_active` et `use_count` n’ont pas de `column_default` en base. La migration `0004` leur donne respectivement `CURRENT_TIMESTAMP`, `true` et `0`. Cette différence est une preuve supplémentaire d’une création par `create_all()` plutôt que par `0004`.

## 8. Analyse de `create_all()`

`app/main.py:62-63` contient :

```python
if settings.app_env == "development":
    Base.metadata.create_all(engine)
```

Le conteneur runtime expose `app_env=development`. La variable `APP_ENV` est absente de `.env`, donc Pydantic utilise la valeur par défaut `development` de `app/config.py`.

Le modèle ORM contient `WorkshopCode` (`app/models.py:46-64`), ce qui explique sa création automatique. Le modèle ne déclare aucune `Sequence` SQLAlchemy pour `participant_login_number_seq`; cet objet n’existe donc pas après `create_all()`.

Verdict : **Hypothèse B confirmée**. Le démarrage applicatif a créé un schéma partiel hors Alembic.

## 9. Comparaison modèle–migration–base

| Objet | Modèle ORM | Migration `0004` | Base active | Diagnostic |
|---|---|---|---|---|
| `participant_login_number_seq` | Référencé indirectement par le service | `CREATE SEQUENCE` | Absent | Rupture directe de l’inscription |
| `workshop_codes` | Oui | `create_table` + contraintes/index | Oui, forme ORM | Table prématurée |
| `users.participant_id` | `unique=True` (`models.py:27`) | `uq_users_participant_id` | Non unique | Schéma antérieur |
| Checks atelier | Oui | Oui | Oui | Partiellement présent |
| `code_hash` | unique + index | contrainte unique + index unique | index unique seulement | Différence de nom/topologie |
| Index fenêtre | Non dans le modèle | Oui | Absent | Migration non appliquée |
| Révision | N/A | `0004` | `0002` | Code et base désalignés |

## 10. Analyse de la réponse JSON

Le frontend exécute `response.json()` sans vérifier le statut ni le `Content-Type` (`app/static/participant_registration.js:31-38`).

La route ne capture que `RegistrationError` (`app/main.py:158-161`). L’exception SQLAlchemy `ProgrammingError` remonte à Starlette/Uvicorn. Un test ASGI en mémoire, avec une exception simulée et sans accès à la base, retourne :

```text
status= 500
content_type= text/plain; charset=utf-8
body= 'Internal Server Error'
```

Verdict : **Hypothèse E confirmée**. `JSON.parse` est une cause secondaire d’interface ; la cause primaire reste l’absence de séquence.

## 11. Verdict des hypothèses

| Hypothèse | Verdict | Preuve |
|---|---|---|
| A — base restée en `0003`/avant `0004` | CONFIRMÉE | `alembic_version = 0002_p0a_recording_sync` |
| B — `create_all()` a créé `workshop_codes` sans la séquence | CONFIRMÉE | `APP_ENV=development`, `main.py:62-63`, defaults ORM sans defaults serveur |
| C — image runtime incomplète / mauvais chemin Alembic | CONFIRMÉE | runtime sans `alembic.ini` ni `migrations/`, erreur `script_location` |
| D — `upgrade head` direct rencontrerait un objet existant | CONFIRMÉE par analyse | `0004` exécute `create_table(workshop_codes)` alors que la table existe ; la migration n’a pas été lancée |
| E — réponse 500 non JSON | CONFIRMÉE | test ASGI : `text/plain`, `Internal Server Error` |

## 12. Risque d’un `upgrade head` direct

Le premier point bloquant déterministe est `op.create_table("workshop_codes")` contre la table déjà existante. Le serveur risque donc `DuplicateTable`. Comme PostgreSQL exécute la migration dans une transaction, les opérations précédentes de `0004` devraient être annulées, mais cette propriété ne constitue pas une procédure de réparation.

Un `stamp` serait incorrect : il masquerait l’absence de séquence et de contraintes. Une création manuelle de séquence serait également insuffisante : la base resterait à `0002` et le reste de `0004` manquerait.

## 13. Scénarios de correction à préparer

### Scénario recommandé — schéma partiel et image incomplète

1. Sauvegarder PostgreSQL et vérifier la restauration hors production.
2. Geler les écritures d’inscription et d’administration.
3. Corriger l’image afin d’inclure `alembic.ini` et `migrations/`, puis définir explicitement `APP_ENV=production`.
4. Exporter/conserver la ligne de `workshop_codes` sans exposer `code_hash` dans les logs.
5. Faire valider une procédure de réconciliation de la table ORM prématurée avec `0004` (renommage temporaire et reprise contrôlée, ou migration corrective idempotente). Ne pas supprimer silencieusement la ligne existante.
6. Appliquer ensuite la chaîne Alembic complète dans une fenêtre de maintenance, avec configuration explicite.
7. Vérifier `alembic current`, `heads`, la séquence, l’unicité `users.participant_id`, les checks et les index.
8. Effectuer une inscription de fumée, puis réactiver les écritures.

Ce scénario ne doit pas être remplacé par `alembic stamp` ni par une modification rétroactive de `0004` si la migration est déjà appliquée ailleurs.

### Cas de migration simplement non appliquée

Valable uniquement sur une base où aucun objet de `0004` n’existe : sauvegarde, arrêt des écritures, `alembic upgrade head` avec `-c /app/alembic.ini`, vérification de la révision et test de fumée.

### Cas `0004` déclarée mais schéma incomplet

Non observé ici. Préparer une `0005` corrective ou une restauration pré-migration ; ne jamais réécrire une migration déjà appliquée.

## 14. Plan de tests après correction

- `alembic -c /app/alembic.ini current` fonctionne dans l’image runtime.
- `current == head` avant démarrage applicatif.
- séquence présente et première valeur correcte sur base vide ; historique `MOS_999` → `MOS_1000`.
- `workshop_codes`, contraintes, index et unicité 1–1 conformes.
- inscription HTTP avec code valide ; aucun compte/participant orphelin en cas d’échec.
- code encore valide ou recréé après réconciliation.
- erreur serveur structurée en JSON ; frontend tolérant à un `Content-Type` inattendu.
- concurrence 10/30/50, limite atelier et permissions.
- démarrage refusé ou explicitement bloqué si la base n’est pas à jour.

## 15. État final et limites

Les commandes exécutées ont été des inspections Git, fichiers, image, Compose, logs, Alembic en lecture seule, métadonnées PostgreSQL et un test ASGI en mémoire. Aucun `upgrade`, `downgrade`, `stamp`, `create_all()`, redémarrage, modification SQL, modification de variable d’environnement, suppression de conteneur/volume ou modification de donnée n’a été effectué.

Le fichier de rapport est la seule création liée à cette intervention. Les changements applicatifs visibles dans `git status --short` étaient préexistants au diagnostic et n’ont pas été modifiés. Les limites résiduelles sont l’absence de correction appliquée par construction du ticket et la nécessité d’une validation de la procédure de réconciliation par l’exploitant PostgreSQL.
