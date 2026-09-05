# Traceabilite P0-A apres remediation

| ID | Risque | Test exact | Type | Services | Resultat | Preuve |
|---|---|---|---|---|---|---|
| P0A-01 | configuration | tests/test_config.py::* | UNITAIRE | aucun | PARTIELLEMENT PROUVE | 53 passes, couverture non exhaustive |
| P0A-02 | semaphore | tests/test_audio_controls.py::*; tests/test_remediation_evidence.py::test_audio_failures_cross_upload_route_without_ready | INTEGRATION | app-test | PROUVE | liberation timeout/exception et saturation |
| P0A-03 | migration | tests/test_migrations.py::test_migrated_schema_matches_expected | INTEGRATION | db-test | PROUVE | Alembic head et schema PostgreSQL |
| P0A-04 | workflow/checksums/WAV | tests/test_integration_http.py::test_end_to_end_http_postgres_minio_permissions_and_reconcile; tests/test_remediation_evidence.py::test_real_checksum_and_wav_properties | HTTP | PostgreSQL/MinIO reels | PROUVE | SHA-256 recalcules et WAV PCM16 mono 16 kHz |
| P0A-05 | permissions/IDOR/session/CSRF | tests/test_p0a3_negative.py::test_http_permission_matrix_idor_sessions_and_csrf; tests/test_remediation_evidence.py::test_real_http_permission_matrix_and_csrf | HTTP | stack test | PARTIELLEMENT PROUVE | appels reels mais cellules non exhaustives |
| P0A-06 | audio negatif | tests/test_p0a3_negative.py::test_audio_negative_inputs_have_controlled_responses_and_no_ready_rows; tests/test_remediation_evidence.py::test_duration_boundaries_cross_upload_route; test_audio_failures_cross_upload_route_without_ready | HTTP | stack test | PARTIELLEMENT PROUVE | duree/erreurs route couvertes, limites restantes |
| P0A-07 | concurrence | tests/test_p0a3_negative.py::test_concurrent_duplicate_returns_one_success_and_one_conflict | CONCURRENCE | PostgreSQL/MinIO reels | PROUVE | une creation, 409, une ligne |
| P0A-08 | compensation partielle | tests/test_remediation_evidence.py::test_partial_compensation_leaves_real_orphan_detected_by_reconcile | PANNE | PostgreSQL/MinIO reels | PROUVE | orphan reel detecte |
| P0A-09 | checksum/taille | tests/test_p0a3_negative.py::test_reconciliation_detects_checksum_and_size_mismatch; test_real_checksum_and_wav_properties | INTEGRATION | PostgreSQL/MinIO reels | PARTIELLEMENT PROUVE | recalcul reel, cas combine |
| P0A-10 | anomalies reconciliation | tests/test_p0a4_closure.py::test_reconciliation_exhaustive_artificial_anomalies_is_read_only | INTEGRATION | PostgreSQL/MinIO reels | PARTIELLEMENT PROUVE | lecture seule, sous-cas regroupes |
| P0A-11 | erreurs MinIO distinctes | tests/test_remediation_evidence.py::test_reconcile_storage_errors_are_distinct; tests/test_p0a4_closure.py::test_minio_not_found_is_distinguished_from_generic_failure | PANNE | MinIO reel + injections | PROUVE | types timeout/refus/connexion/erreur et NoSuchKey |
| P0A-12 | backup/restore | scripts/backup.sh, scripts/restore.sh; controles Alembic/reconcile/checksums | REPRISE | sources et cibles distinctes | PROUVE | head, [], checksums et WAV OK |
| P0A-13 | pannes PostgreSQL-MinIO | tests/test_remediation_evidence.py::test_real_minio_unavailable_before_upload_has_controlled_rollback; test_second_object_failure_compensates_real_raw_object; test_commit_failure_compensates_both_real_objects_and_session_recovers; test_partial_delete_is_not_silent_and_retry_succeeds | PANNE | services reels + fautes ciblees | PARTIELLEMENT PROUVE | upload/commit/compensation/suppression, combinaisons incompletes |
| P0A-14 | bornes/timeouts audio | tests/test_remediation_evidence.py::test_duration_boundaries_cross_upload_route; test_audio_failures_cross_upload_route_without_ready | HTTP | stack test | PARTIELLEMENT PROUVE | route et etats observes, tailles/proprietes incompletes |
| P0A-15 | permissions HTTP | tests/test_remediation_evidence.py::test_real_http_permission_matrix_and_csrf | HTTP | stack test | PARTIELLEMENT PROUVE | appels de roles reels, toutes methodes non couvertes |
| P0A-16 | controles VPS | HTTPS, appareils, charge, sauvegarde externe, rotation | MANUEL VPS | VPS | MANUEL VPS | hors Docker |

PROUVE signifie que le test et ses assertions couvrent le risque declare. Les exigences partielles ne sont pas declarees PROUVEES par le seul nombre de tests passes.
