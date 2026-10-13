# G6.1 — Tests de release

## Candidate nettoyée

- Python : `159 passed, 1 skipped, 8 warnings` en 133,37 s dans la stack Docker G5 isolée.
- JavaScript : `10 passed`.
- `bash -n scripts/*.sh` : OK.
- `git diff --check` : OK.
- Artefacts G5.1 : 72 contrôles, zéro overflow, zéro erreur navigateur inattendue ; aucun code fonctionnel ou visuel n’a changé dans G6.1, donc aucune relance Playwright supplémentaire n’était nécessaire.

## Warnings

Les 8 warnings Python sont inchangés : dépréciation `crypt` via passlib, `FastAPI on_event`, Starlette/httpx et quatre usages de `datetime.utcnow()`. Ils sont non bloquants et doivent faire l’objet d’une dette technique séparée.

## Migration et garde-fou

- `scripts/migrate.sh` reste le seul chemin explicite pour `alembic upgrade`.
- Les commandes startup test/E1 ne contiennent pas `alembic upgrade`.
- `app.main` appelle `assert_schema_current()` ; aucune migration implicite n’est introduite.
- Les migrations `0005` à `0008` et les contrôles de schéma sont couverts par la suite Python.

## Sauvegardes

`scripts/backup_local.sh` et les preuves F5A6–F5A8 sont inchangés par rapport à `main`. Aucune archive de sauvegarde n’a été modifiée.
