# F5A3 — compatibilité production de la candidate

## Décision

**PRÊT POUR AUTORISATION DU CORRECTIF**, pas pour déploiement automatique. Aucun conteneur, volume, migration, routeur ou donnée de production n’a été modifié.

## Référence réellement déployée

- Conteneur : `mobile_money_corpus_manager_v0_1-app-1`.
- Image active : `sha256:c2e3e50e3e74d2901cbe5308b77ac9c4d0dab660668b836f6bda4b23a49f2467`.
- PostgreSQL observé : `postgres:16-alpine`, révision `0005_workshop_attribution (head)`.
- L’extraction en lecture seule de `/app` contient uniquement `0001` à `0005`.
- Dépendances conservées depuis l’image active : FastAPI `0.116.1`, Uvicorn `0.35.0`, SQLAlchemy `2.0.43`, psycopg `3.2.9`, MinIO SDK `7.2.16`, Alembic `1.16.4`, Python `3.12.15`.
- Aucun worker asynchrone ou queue n’a été trouvé dans cette image. Les écritures observées sont dans les routes HTTP : inscription, upload/réservation/finalisation audio, transcription, vérification, administration et suppression.

## Candidate

- Tag local : `f5a3-candidate:0005-freeze`.
- Digest local : `sha256:170270493de28c7e4fffbf1cd396122680d4eb2684249edd8fd7e166be4493e2`.
- Base épinglée : `python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b`.
- La candidate est reconstruite depuis l’extraction de l’image active, avec le correctif `app/write_freeze.py` et l’import/middleware dans `app/main.py`.
- Le build échoue si une migration `0006`, `0007` ou `0008` apparaît.
- Diff fonctionnel exhaustif : (1) middleware avant les routes HTTP mutantes ; (2) état partagé atomiquement avec verrou fichier ; (3) CLI `status`, `check`, `drain`, `freeze`, `unfreeze` ; (4) utilisateur runtime `appuser` UID `10001`; (5) aucun changement métier, de schéma ou de dépendance Python.

## Compatibilité et risques acceptés

Le schéma `0005` est compatible avec la candidate. Le gel ne doit être activé qu’après montage persistant partagé de `WRITE_FREEZE_STATE_FILE` pour tous les processus applicatifs. Ce montage doit être hors des volumes de données et appartenir à l’UID runtime de la candidate avec permissions restrictives. Sans ce montage, un redémarrage pourrait recréer un état `OPEN` : déploiement interdit.

L’image active tourne actuellement ; son état n’a pas été changé. Le déploiement de la candidate reste soumis à la checklist et à l’arrêt contrôlé des écritures.

