# REMEDIATION E1 — diagnostic des régressions et sécurisation de release

Date : 2026-10-10  
Branche : `remediation-a-stabilisation-securite`  
Révision Lot D : `d34e96a` (`remediation stabilisee c&d`)  
Révision Alembic vérifiée : `0008_rate_limit_buckets (head)`

## Décision

**BLOQUÉ** pour publication. Les régressions fonctionnelles observées dans le lot E
sont corrigées et la compatibilité historique est démontrée sur une copie synthétique.
La décision reste bloquée par deux vulnérabilités SCA sans version corrective
(`python-jose` et `ecdsa`) et deux détections Gitleaks dans un artefact Graphify qui
nécessitent une revue sécurité explicite. Aucun accès ni migration de production n’a
été effectué.

## 1. Diagnostic et causes racines

L’état initial a été sauvegardé par `git status`, `git log` et comparaison avec
`d34e96a`. L’exécution E initiale rapportait 18 échecs et 25 erreurs (43 anomalies).
La reproduction a d’abord utilisé les volumes Compose historiques ; PostgreSQL
présentait un checkpoint invalide et la base restait en `0007`. Le réseau et les
volumes nommés pouvaient également être partagés par d’autres environnements de
remédiation. Après création de `docker-compose.e1.test.yml`, avec réseau, volumes,
base, MinIO et bucket dédiés, la suite complète passe.

| Cause racine | Preuve | Conclusion |
|---|---|---|
| Volumes Docker persistants/corrompus | logs PostgreSQL : `invalid checkpoint record`, `could not locate a valid checkpoint record` | cause environnementale, non régression métier |
| Révision Alembic obsolète | `alembic current` initial en `0007`, cible attendue `0008` | environnement non remis à niveau |
| Scripts d’exploitation ignorés par Git | le worktree Lot D ne contenait pas `reconcile.py` et `reconcile_participant_registration_schema.py` | défaut de traçabilité/versionnement, corrigé par les exceptions `.gitignore` |
| Ordre de tests | le sous-ensemble négatif isolé échoue quand les données créées par `test_integration_http.py` n’existent pas | dépendance d’ordre documentée ; la suite normale passe |
| API de templates après mise à jour sécurité | Starlette 1.7 rendait les appels positionnels `TemplateResponse` incompatibles | régression avérée de dépendance, corrigée par un adaptateur keyword-only |
| Formulaires CSRF vides | FastAPI récent validait `Form(...)` avant `check_csrf`, donnant 422 au lieu de 403 attendu | régression de contrat, corrigée en laissant le contrôle CSRF produire 403 |

La comparaison isolée Lot D/Lot E donne `153 passed, 1 skipped` dans les deux cas après
restauration des scripts opérationnels manquants du worktree D. La différence initiale
était donc un défaut de reproduction/versionnement, pas une divergence métier du Lot E.

## 2. Tableau de traçabilité des 43 anomalies initiales

Les variantes paramétrées sont comptées séparément, conformément au total du rapport E.
Le résultat final ci-dessous est établi sur l’environnement E.1 isolé et propre.

| ID | Test/anomalie du rapport E | Cause initiale | Résultat E.1 | Action |
|---:|---|---|---|---|
| 01 | `test_real_minio_unavailable_before_upload_has_controlled_rollback` | MinIO/volume stale | PASS | environnement isolé |
| 02 | `test_commit_failure_compensates_both_real_objects_and_session_recovers` | DB/MinIO incohérents | PASS | environnement isolé |
| 03 | `test_partial_compensation_leaves_real_orphan_detected_by_reconcile` | fixtures MinIO obsolètes | PASS | environnement isolé |
| 04 | `test_partial_delete_is_not_silent_and_retry_succeeds` | fixtures MinIO obsolètes | PASS | environnement isolé |
| 05 | `test_duration_boundaries_cross_upload_route[0.249]` | schéma non migré | PASS | migration `0008` |
| 06 | `test_duration_boundaries_cross_upload_route[0.8]` | schéma non migré | PASS | migration `0008` |
| 07 | `test_duration_boundaries_cross_upload_route[120.0]` | schéma non migré | PASS | migration `0008` |
| 08 | `test_duration_boundaries_cross_upload_route[120.001]` | schéma non migré | PASS | migration `0008` |
| 09 | `test_audio_failures_cross_upload_route_without_ready[ffmpeg_timeout]` | service app non prêt | PASS | readiness attendue |
| 10 | `test_audio_failures_cross_upload_route_without_ready[ffprobe_timeout]` | service app non prêt | PASS | readiness attendue |
| 11 | `test_audio_failures_cross_upload_route_without_ready[wav_empty]` | service app non prêt | PASS | readiness attendue |
| 12 | `test_real_checksum_and_wav_properties` | MinIO stale | PASS | bucket dédié |
| 13 | `test_real_http_permission_matrix_and_csrf` | volume/fixtures stale | PASS | fixtures synthétiques |
| 14 | `test_sequences_follow_complete_key` | état DB partagé | PASS | DB dédiée |
| 15 | `test_client_cannot_choose_number` | état DB partagé | PASS | DB dédiée |
| 16 | `test_idempotence_and_fingerprint` | état DB partagé | PASS | DB dédiée |
| 17 | `test_concurrent_uploads_keep_distinct_verified_objects` | état DB partagé | PASS | DB dédiée |
| 18 | `test_failed_storage_consumes_number_and_is_idempotent[1]` | état DB partagé | PASS | DB dédiée |
| 19 | `test_failed_storage_consumes_number_and_is_idempotent[2]` | état DB partagé | PASS | DB dédiée |
| 20 | `test_conversion_failure_consumes_number` | service app non prêt | PASS | readiness attendue |
| 21 | `test_rejection_and_deletion_do_not_release_number` | état DB partagé | PASS | DB dédiée |
| 22 | `test_limit_and_schema` | Alembic `0007` | PASS | migration `0008` |
| 23 | `test_same_key_concurrent_pending_then_same_result` | état DB partagé | PASS | DB dédiée |
| 24 | `test_finalization_failure_resolves_commit_outcome[False]` | DB/MinIO stale | PASS | environnement isolé |
| 25 | `test_finalization_failure_resolves_commit_outcome[True]` | DB/MinIO stale | PASS | environnement isolé |
| 26 | `test_compensation_failure_visible_in_reconciliation` | MinIO stale | PASS | `reconcile.py` |
| 27 | `test_deleted_idempotent_receipt_cannot_recreate_audio` | état DB partagé | PASS | DB dédiée |
| 28 | `test_participant_cannot_read_or_submit_other_participant` | fixtures utilisateur stale | PASS | données synthétiques |
| 29 | `test_inactive_utterance_rejected_without_consuming` | fixtures atelier stale | PASS | données synthétiques |
| 30 | `test_same_key_is_scoped_to_authenticated_user` | fixtures utilisateur stale | PASS | données synthétiques |
| 31 | `test_unavailable_database_after_storage_keeps_pending_objects` | dépendance infra | PASS | environnement isolé |
| 32 | `test_export_keeps_logical_names` | objets MinIO absents | PASS | bucket dédié |
| 33 | `test_real_http_export_work_and_benchmark_mixed_statuses` | app lancé sans readiness | PASS | attente healthcheck |
| 34 | `test_real_http_export_permissions_and_csrf` | app lancé sans readiness | PASS | attente healthcheck |
| 35 | `test_end_to_end_http_postgres_minio_permissions_and_reconcile` | app lancé sans readiness | PASS | attente healthcheck |
| 36 | `test_http_csrf_and_invalid_audio_are_rejected` | app lancé sans readiness | PASS | attente healthcheck |
| 37 | `test_http_permission_matrix_idor_sessions_and_csrf` | Form CSRF strict + fixtures | PASS | adaptateur CSRF + DB dédiée |
| 38 | `test_audio_negative_inputs_have_controlled_responses_and_no_ready_rows` | app/MinIO stale | PASS | environnement isolé |
| 39 | `test_concurrent_uploads_return_distinct_takes_and_valid_objects` | état DB/MinIO partagé | PASS | environnement isolé |
| 40 | `test_reconciliation_detects_checksum_and_size_mismatch` | script absent du worktree D | PASS | scripts versionnés |
| 41 | `test_reconciliation_exhaustive_artificial_anomalies_is_read_only` | script absent du worktree D | PASS | scripts versionnés |
| 42 | `test_public_registration_api_permissions_csrf_and_login` | schéma/fixtures stale | PASS | migration + fixtures |
| 43 | `test_real_minio_restore_and_historical_integrity` | restauration non préparée | PASS | sauvegarde/restauration isolée |

Aucun skip ni assertion n’a été ajouté pour masquer ces anomalies. Le seul skip
persistant est `test_dev_environment.py:18`, qui constate l’absence normale du binaire
Docker dans le conteneur de test ; le contrôle Compose est exécuté par l’hôte et passe.

## 3. Corrections effectuées

- Ajout de `docker-compose.e1.test.yml` avec noms explicites de réseau/volumes E.1.
- Conservation des extractions `app/audio_processing.py` et `app/audit.py`, avec wrappers
  de compatibilité pour les seams de test existants.
- Ajout de `render_template()` dans `app/main.py` pour le contrat Starlette récent,
  sans changement de route, permission ou réponse attendue.
- Les tokens CSRF vides atteignent désormais `check_csrf()` et restent refusés en 403.
- Mise à jour de `fastapi`, `python-multipart` et `pytest` dans `requirements.txt`.
- Correction de `.gitignore` afin que les scripts de sauvegarde, restauration,
  réconciliation et diagnostics soient versionnables.

## 4. Résultats des tests

| Contrôle | Résultat |
|---|---|
| Python, passage 1 sur E.1 propre | `153 passed, 1 skipped, 8 warnings` |
| Python, passage 2 | `153 passed, 1 skipped, 8 warnings` |
| Node `.test.cjs` | tous les scripts passent : 2 + 1 + 4 + 3 sous-tests selon les scripts |
| `node --check` | PASS |
| `docker compose ... config --quiet` | PASS |
| liveness/readiness | PASS, `/ready` healthy |
| Alembic | `0008_rate_limit_buckets (head)` |

Les warnings restants sont des dépréciations (`on_event`, `crypt`, `utcnow`, compatibilité
Starlette TestClient), non des échecs de comportement.

## 5. Sécurité

- Bandit 1.8.6 : 3 LOW, appels `subprocess` dans le traitement FFmpeg ; arguments en
  liste, `shell=False`, bornage par sémaphore et tests dédiés. À revoir avec l’équipe sécurité.
- pip-audit 2.9.0 après mise à jour : 2 alertes, `python-jose==3.5.0` et
  `ecdsa==0.19.2`, sans version corrective proposée.
- Gitleaks v8.24.3 : 2 `generic-api-key` dans `graphify-out/cache/stat-index.json`;
  valeurs non publiées. Une confirmation humaine est requise avant exclusion de cet
  artefact généré du périmètre de release.
- Les scripts inline/CSP restent un risque documenté dans `SECURITY_SCAN_REPORT.md`.

## 6. Restauration et migration 0005→0008

Sur l’environnement E.1 isolé :

1. création de volumes PostgreSQL/MinIO distincts de la production ;
2. exécution des tests d’intégration pour produire un jeu synthétique contrôlé ;
3. sauvegarde PostgreSQL et MinIO avec `scripts/backup.sh` ;
4. restauration vers `db-restore`/`minio-restore` avec `scripts/restore.sh` ;
5. vérification de `0008_rate_limit_buckets (head)` ;
6. vérification restaurée : 9 utilisateurs, 4 participants, 4 enregistrements,
   3 transcriptions et 8 objets MinIO source/8 objets restaurés ;
7. `scripts/reconcile.py --json` retourne `[]` ;
8. les tests migrations, inscriptions, prises, transcriptions et exports passent dans
   la suite complète.

Le retour arrière reste une restauration coordonnée PostgreSQL + MinIO depuis le backup,
comme décrit dans `MIGRATION_0005_TO_0008.md`. Aucune migration de production n’a été
exécutée. La fenêtre d’indisponibilité demeure à estimer sur un volume réel par
l’exploitation.

## 7. Risques résiduels et validations humaines

- choix de remplacement ou exception formelle pour `python-jose`/`ecdsa` ;
- triage des deux détections Gitleaks Graphify ;
- extraction des scripts inline et suppression progressive de `unsafe-inline` ;
- revue humaine des diffs, contrats HTTP, volumes restaurés et fenêtre de maintenance ;
- staging/commit des nouveaux scripts et documents avant release.

## 8. Références et statut

- Architecture : `ARCHITECTURE_CURRENT.md`
- Exploitation : `DEPLOYMENT_RUNBOOK.md`
- Migration : `MIGRATION_0005_TO_0008.md`
- Sécurité : `SECURITY_SCAN_REPORT.md`
- Release : `RELEASE_CHECKLIST.md`

**Statut final : BLOQUÉ — validation fonctionnelle et historique démontrées, autorisation
de mise en production non accordée.**
