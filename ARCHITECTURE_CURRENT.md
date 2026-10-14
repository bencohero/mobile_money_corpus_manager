# Architecture actuelle

## Périmètre

Cette cartographie correspond à la branche `remediation-a-stabilisation-securite` au
10 octobre 2026. Aucun volume ni aucune donnée de production n’a été ouvert ou modifié.

## Avant / après Lot E

Avant, `app/main.py` regroupait l’initialisation FastAPI, les probes, l’authentification,
les routes d’atelier/participant, les uploads et conversions FFmpeg, les transcriptions,
les exports, l’audit et les contrôles CSRF.

Après la première extraction incrémentale :

- `app/main.py` reste le composition root et le module de routes HTTP, avec les chemins,
  paramètres, permissions et réponses inchangés.
- `app/audio_processing.py` possède l’exécution bornée de FFmpeg/ffprobe, les erreurs
  corrélées et la compensation MinIO.
- `app/audit.py` possède l’écriture des événements d’audit et les helpers CSRF.
- `app/storage.py` isole MinIO ; `app/corpus_export.py` isole la construction des ZIP/CSV.
- `app/participant_registration.py`, `app/recording_submission.py`, `app/take_sequence.py`,
  `app/workshops.py` portent déjà des services métier spécialisés.
- `app/models.py` et `app/db.py` portent le modèle et PostgreSQL ; Alembic porte le schéma.

Les fonctions extraites restent importées dans `app.main` pour compatibilité des tests et
pour éviter tout changement de contrat Python pendant cette étape.

## Routes

| Domaine | Routes principales | Autorisation |
|---|---|---|
| Santé | `/health`, `/ready` | publique |
| Authentification | `/login`, `/logout` | publique + CSRF |
| Inscription | `/participant/register`, `/api/auth/workshop-language`, `/api/auth/participant-registration` | publique + rate limit/CSRF |
| Ateliers | `/admin/workshop-codes*`, `/admin/workshops/*/status` | ADMIN + CSRF |
| Participants | `/participants*`, `/help` | ADMIN ou PARTICIPANT selon route |
| Capture | `/record`, `/api/recordings`, `/api/recordings/next-take` | PARTICIPANT/ADMIN |
| Audio | `/audio/{recording_id}` | utilisateur autorisé, Range supporté |
| Transcription | `/recordings`, `/transcribe*`, `/api/transcriptions/*/history` | rôles métier |
| Validation | `/verify/{recording_id}` | ADMIN/VALIDATOR + CSRF |
| Exploitation | `/admin/export*`, `/export/recordings.csv`, suppression audio | ADMIN + CSRF pour mutations |

## Dépendances et flux

```text
Navigateur -> FastAPI/Jinja2 -> services métier -> SQLAlchemy/PostgreSQL
                                      \-> MinIO (brut + WAV)
                                      \-> FFmpeg/ffprobe (normalisation)
Alembic 0001..0008 -> PostgreSQL
```

Les tests Python couvrent les contrats et les tests Node couvrent les comportements
navigateur de capture, inscription et transcription. Le graphe Graphify persistant est
conservé dans `graphify-out/` comme aide de navigation, pas comme source de vérité métier.
