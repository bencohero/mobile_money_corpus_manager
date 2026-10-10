# Rapport de remédiation A — stabilisation et sécurisation du socle

Date : 2026-10-10  
Branche : `remediation-a-stabilisation-securite`  
Mode : corrections ciblées, sans migration ni accès à une base de production.

## 1. Résumé

Le lot A est terminé sur l’environnement de test isolé. Les défauts confirmés ont été corrigés sans assouplir les règles métier :

- les valeurs MinIO et mot de passe administrateur de démonstration sont refusées en production ;
- `POST /verify/{recording_id}` rejette toute décision hors de `VERIFIED`, `NEEDS_REVIEW` et `REJECTED` avant toute lecture ou mutation métier ;
- `/health` reste un endpoint de liveness indépendant ; `/ready` vérifie PostgreSQL et MinIO avec des timeouts bornés et retourne 503 si nécessaire ;
- les fixtures ont été alignées sur l’obligation de langue, la génération serveur des identifiants et les contraintes FK ;
- les tests d’export et les tests de preuve utilisent le contrat courant ;
- l’image de test contient désormais les fichiers nécessaires aux tests d’environnement.

Aucune migration, modification de schéma, modification d’interface ou modification de donnée de production n’a été effectuée.

## 2. État avant / après

Résultat initial documenté par l’audit, dans la suite Docker isolée : `108 passed, 25 failed, 2146 warnings` en 90,69 s.

Après corrections :

| Exécution | Résultat | Durée |
|---|---:|---:|
| Suite Docker complète 1 | 145 passed, 1 skipped, 2308 warnings | 127,77 s |
| Suite Docker complète 2 | 145 passed, 1 skipped, 2308 warnings | 133,53 s |
| Tests Node frontend (`tests/*.cjs`) | tous les scripts exécutés passent, 0 échec | succès |
| Compose prod/dev/test `config --quiet` | succès | succès |
| `git diff --check` | succès | succès |

Le skip est explicite et reproductible : le CLI Docker n’est pas installé dans l’image `test`; la validation Compose est exécutée avec le CLI hôte et a réussi. Aucun test n’a été supprimé, ignoré ou neutralisé pour obtenir ce résultat.

## 3. Traçabilité individuelle des 25 échecs initiaux

| ID | Test initial | Classification et cause démontrée | Correction / état |
|---|---|---|---|
| RA-TEST-01 | `test_production_rejects_default_minio_credentials` | Défaut applicatif : la configuration production acceptait `minioadmin/minioadmin`. | Liste de valeurs interdites renforcée dans `app/config.py`; vert. |
| RA-TEST-02 | `test_real_http_export_work_and_benchmark_mixed_statuses` | Fixture obsolète : le test envoyait un code participant alors que l’identifiant est généré côté serveur. | Le test relit l’identifiant généré après inscription; vert. |
| RA-TEST-03 | `test_real_http_export_permissions_and_csrf` | Fixture obsolète : le login participant utilisait un nom fourni au client, non le login serveur attribué. | Le test utilise le participant généré; vert. |
| RA-TEST-04 | `test_dev_compose_is_valid_and_isolated` | Défaut d’environnement : le CLI Docker n’est pas présent dans l’image de test. | Skip conditionnel documenté; validation Compose hôte réussie. |
| RA-TEST-05 | `test_dev_env_example_is_fake_and_ignored` | Image de test incomplète : `.env.dev.example` et fichiers de contexte absents. | Copie des fichiers nécessaires dans la cible test du `Dockerfile`; vert. |
| RA-TEST-06 | `test_alembic_head_and_runtime_files_exist` | Image de test incomplète : fichiers de déploiement/runtime absents du contexte exécuté. | Même correction de contexte Docker; vert. |
| RA-TEST-07 | `test_concurrent_registrations_are_unique_and_complete[10]` | Fixture obsolète : atelier créé sans `language_code`, contrairement au contrat courant. | Fixture corrigée avec langue explicite; nettoyage FK corrigé; vert. |
| RA-TEST-08 | `test_concurrent_registrations_are_unique_and_complete[30]` | Même cause que RA-TEST-07. | Corrigé; vert. |
| RA-TEST-09 | `test_concurrent_registrations_are_unique_and_complete[50]` | Même cause que RA-TEST-07. | Corrigé; vert. |
| RA-TEST-10 | `test_last_workshop_place_cannot_be_oversubscribed` | Fixture obsolète : atelier sans langue et nettoyage incompatible avec la FK des demandes d’inscription. | Langue ajoutée et demandes supprimées avant l’utilisateur; vert. |
| RA-TEST-11 | `test_public_registration_api_permissions_csrf_and_login` | Contrat de test obsolète : création d’un code d’atelier sans `language_code`; nettoyage FK incomplet. | Langue envoyée et `ParticipantRegistrationRequest` nettoyé avant suppression utilisateur; vert. |
| RA-TEST-12 | `test_real_minio_unavailable_before_upload_has_controlled_rollback` | Fixture obsolète : le contexte retournait six valeurs, le test en déstructurait cinq. | Déstructuration alignée; vert. |
| RA-TEST-13 | `test_second_object_failure_compensates_real_raw_object` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-14 | `test_commit_failure_compensates_both_real_objects_and_session_recovers` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-15 | `test_partial_compensation_leaves_real_orphan_detected_by_reconcile` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-16 | `test_partial_delete_is_not_silent_and_retry_succeeds` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-17 | `test_duration_boundaries_cross_upload_route[0.249]` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-18 | `test_duration_boundaries_cross_upload_route[0.25]` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-19 | `test_duration_boundaries_cross_upload_route[0.8]` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-20 | `test_duration_boundaries_cross_upload_route[120.0]` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-21 | `test_duration_boundaries_cross_upload_route[120.001]` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-22 | `test_audio_failures_cross_upload_route_without_ready[ffmpeg_timeout]` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-23 | `test_audio_failures_cross_upload_route_without_ready[ffprobe_timeout]` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-24 | `test_audio_failures_cross_upload_route_without_ready[wav_empty]` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |
| RA-TEST-25 | `test_real_checksum_and_wav_properties` | Même mismatch de fixture six/cinq valeurs. | Corrigé; vert. |

## 4. Modifications effectuées

### Application et infrastructure

- `app/config.py` : refus des valeurs de démonstration MinIO et du mot de passe administrateur par défaut en production, sans changement des configurations development/test.
- `app/storage.py` : client HTTP MinIO avec timeouts connect/read de 3 secondes et `check_ready()` basé sur `bucket_exists`.
- `app/main.py` : séparation liveness/readiness et validation précoce des décisions de vérification.
- `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.test.yml` : healthcheck applicatif orienté readiness avec paramètres bornés.
- `Dockerfile` : ajout des fichiers de contexte requis par les tests d’environnement.

### Tests et fixtures

- `tests/test_config.py` : cas négatifs MinIO et mot de passe administrateur de démonstration.
- `tests/test_remediation_a.py` : tests unitaires liveness/readiness et décisions valides/invalides avec vérification d’absence de mutation.
- `tests/test_corpus_export.py` : alignement sur les identifiants générés côté serveur et ajout d’ateliers avec langue.
- `tests/test_dev_environment.py` : distinction entre absence du CLI Docker dans l’image et validation hôte.
- `tests/test_participant_registration.py` et `tests/test_participant_registration_http.py` : langue obligatoire et nettoyage FK correct.
- `tests/test_remediation_evidence.py` : déstructuration du contexte à six valeurs.

## 5. Vérifications fonctionnelles ajoutées

- Chaque décision valide (`VERIFIED`, `NEEDS_REVIEW`, `REJECTED`) est testée.
- Plusieurs décisions invalides, dont variantes de casse, espaces et chaîne vide, retournent 400.
- Pour une décision invalide, le test vérifie qu’aucun `get`, commit, changement de statut, changement de transcription ou historique n’est réalisé.
- Liveness est testé sans dépendance.
- Readiness est testé avec PostgreSQL disponible/indisponible et MinIO disponible/indisponible.
- La validation production couvre les deux credentials MinIO et le mot de passe administrateur de démonstration.

## 6. Risques résiduels et limites

- La suite produit encore 2308 avertissements, principalement des dépréciations `datetime.utcnow`, FastAPI `on_event` et API de template. Ils ne bloquent pas ce lot mais constituent une dette technique.
- La readiness vérifie l’existence du bucket MinIO ; elle ne réalise pas d’écriture destructive ni de test complet de téléversement.
- Le skip Docker dans l’image de test reste dépendant de l’environnement ; le contrôle Compose hôte est la vérification de référence.
- Les tests ont utilisé la stack Docker de test et ses volumes de test uniquement. Aucun test de production n’a été lancé.
- Aucune mesure de couverture de code n’a été produite : aucun outil de couverture n’a été exécuté, donc aucune couverture chiffrée n’est déclarée.

## 7. Blocage et référence de livraison

Aucun échec de test ne subsiste dans les deux exécutions complètes. Il reste un skip d’environnement documenté, sans impact sur le code applicatif.

Les corrections sont présentes sur la branche `remediation-a-stabilisation-securite`. Aucun commit de remédiation n’a été créé dans ce lot ; le commit de référence avant intervention était `5457b1e`.

Le lot ne doit pas être étendu à des corrections supplémentaires sans validation explicite des conclusions et des risques résiduels.
