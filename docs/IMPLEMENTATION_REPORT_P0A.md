# Rapport d'implementation - lot P0-A

Date: 2 septembre 2026
Depot: Mobile Money Corpus Manager v0.1

## Resume executif

Le lot P0-A a ete implemente dans le depot et l'image applicative Docker a ete reconstruite. Les dependances Alembic et pytest sont epinglees dans requirements.txt. Aucune restauration, migration sur donnees existantes, suppression de volume, commit ou push n'a ete effectue.

La validation fonctionnelle complete reste en attente: pytest n'est pas installe sur l'hote et le Dockerfile ne copie actuellement que le dossier app, donc les tests du dossier tests ne sont pas embarques dans l'image.

## Changements implementes

- Configuration: APP_ENV, controles stricts en production, COOKIE_SECURE, limites de taille et de duree audio, timeouts FFmpeg/ffprobe et limite configurable de conversions.
- Audio: arguments subprocess sous forme de liste, shell=False implicite, timeout FFmpeg/ffprobe, controle fichier vide, taille et duree, conversion WAV 16 kHz mono PCM16.
- PostgreSQL-MinIO: compensation des objets apres erreur d'upload, rollback DB, gestion du doublon par 409, suppression MinIO tolerante aux objets absents.
- Modele: sync_status, tailles, SHA-256, erreur technique et finalized_at.
- Alembic: alembic.ini, environnement de migration et revision 0001_initial.
- Exploitation: scripts/backup.sh, scripts/restore.sh et scripts/reconcile.py.
- Docker: MinIO versionne, conteneur applicatif non privilegie, tmpfs temporaire et rotation json-file.
- Documentation: README.md, docs/P0A_IMPLEMENTATION.md, docs/BACKUP_RESTORE.md et docs/INCIDENT_RUNBOOK.md.
- Tests: tests/test_p0a_smoke.py et dependances pytest/httpx.

## Strategie PostgreSQL-MinIO

Les fichiers sont uploades en deux objets. En cas d'echec du second upload ou du commit PostgreSQL, une compensation tente de supprimer les objets deja crees et la session SQLAlchemy est rollback. La contrainte unique existante est conservee et une collision retourne 409.

La reconciliation est en lecture seule par defaut et detecte les lignes DB sans objet, les objets orphelins, les divergences de taille et les etats intermediaires.

## Sauvegarde et restauration

Le backup utilise pg_dump au format custom et mc mirror pour MinIO. Un manifeste UTC et des sommes SHA-256 sont produits sous BACKUP_DIR. La restauration exige CONFIRM_RESTORE=YES et une cible explicite. Elle ne doit etre executee que sur un environnement isole.

Objectifs proposes pour le pilote: RPO de 4 a 24 heures et RTO de 4 heures. Retention indicative: 7 sauvegardes journalieres, 4 hebdomadaires et 3 mensuelles.

## Validations executees

- python3 -m compileall: succes.
- bash -n scripts/backup.sh scripts/restore.sh: succes.
- docker compose config --quiet: succes.
- git diff --check: succes.
- docker compose build: succes; Alembic 1.16.4 et pytest 8.4.1 installes dans l'image.
- docker compose run --rm app pytest -q: le conteneur s'est lance, mais aucun test n'a ete collecte car tests n'est pas copie par le Dockerfile.
- Migrations Alembic sur base temporaire: non executees, commande alembic absente de l'environnement hote.

## Risques residuels et actions recommandees

1. Modifier le Dockerfile pour copier tests, migrations et scripts dans une image de test dediee, puis executer pytest.
2. Installer Alembic/pytest sur l'hote ou utiliser l'image pour valider alembic upgrade head sur une base temporaire.
3. Ajouter une migration SQL explicite et reversible apres revue; la revision initiale actuelle s'appuie sur Base.metadata.create_all pour representer le schema existant.
4. Verifier que le semaphore de conversions est effectivement acquis/libere autour du pipeline audio.
5. Ajouter des tests MinIO/PostgreSQL isoles couvrant les pannes et compensations.
6. Tester manuellement sur VPS HTTPS, microphone, permissions, restauration, disque et rotation des secrets.

## Etat Git

Modifications suivies: .env.example, README.md, app/config.py, app/main.py, app/models.py, app/storage.py, docker-compose.yml et requirements.txt.

Nouveaux fichiers: alembic.ini, migrations/, scripts/backup.sh, scripts/reconcile.py, scripts/restore.sh, docs/ et tests/.

1prompt_POA.md reste non suivi et a ete preserve comme modification preexistante. Aucun secret reel n'a ete ajoute.
