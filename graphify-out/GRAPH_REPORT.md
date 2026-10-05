# Graph Report - mobile_money_corpus_manager_v0_1  (2026-10-05)

## Corpus Check
- Corpus is ~13,002 words - fits in a single context window. You may not need a graph.

## Summary
- 294 nodes · 635 edges · 23 communities (14 shown, 3 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 64 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- API and Audio Orchestration
- Web Interface Workflows
- Core Data and Authentication
- Corpus Export Test Doubles
- Operations and Recovery
- Storage Failure Handling
- Runtime Configuration Validation
- Remediation Evidence Tests
- Export and Validation Governance
- Corpus Export Engine
- Deployment Services and Dependencies
- HTTP Integration Tests
- Isolated Recovery Test Stack
- Audio Command Safety
- Browser Recording Upload
- P0-A.2 Test Environment
- Secret Generation Utility

## God Nodes (most connected - your core abstractions)
1. `Recording` - 31 edges
2. `require()` - 19 edges
3. `upload_recording()` - 16 edges
4. `User` - 15 edges
5. `Settings` - 13 edges
6. `Base` - 12 edges
7. `check_csrf()` - 11 edges
8. `Participant` - 11 edges
9. `upload()` - 11 edges
10. `Base Application Template` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Recorded-to-Transcribed-to-Verified Workflow` --semantically_similar_to--> `Collaborative Voice Corpus Workflow`  [INFERRED] [semantically similar]
  app/templates/transcribe.html → README.md
- `Backup and Restore Validation` --conceptually_related_to--> `Collaborative Voice Corpus Workflow`  [INFERRED]
  docker-compose.test.yml → README.md
- `Team Role Management` --semantically_similar_to--> `Role-Based Workflow`  [INFERRED] [semantically similar]
  app/templates/users.html → README.md
- `Participant Consent Management` --semantically_similar_to--> `Consent Before Collection`  [INFERRED] [semantically similar]
  app/templates/participants.html → README.md
- `Benchmark Export Filtering` --semantically_similar_to--> `Benchmark Corpus Export`  [INFERRED] [semantically similar]
  app/templates/export.html → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Role-Governed Corpus Interfaces** — app_templates_base_role_aware_navigation, app_templates_participants_participants_template, app_templates_users_users_template, app_templates_export_export_template, app_templates_transcribe_validator_decision [INFERRED 0.95]
- **Audio Corpus Lifecycle** — app_templates_record_record_template, app_templates_recordings_recordings_template, app_templates_transcribe_transcription_template, app_templates_export_export_template [INFERRED 0.95]
- **Isolated Backup and Restore Test Topology** — docker_compose_test_db_test, docker_compose_test_minio_test, docker_compose_test_db_restore, docker_compose_test_minio_restore, docker_compose_test_tools [EXTRACTED 1.00]
- **P0-A Validation Lifecycle** — docs_p0a1_validation_p0a1_validation, docs_p0a2_integration_recovery_p0a2_integration_recovery, docs_p0a3_negative_tests_p0a3_negative_tests, docs_p0a4_closure_p0a4_closure, docs_p0a_traceability_matrix_p0a_traceability_matrix [EXTRACTED 1.00]
- **PostgreSQL-MinIO Integrity and Recovery Flow** — docker_compose_db, docker_compose_minio, docs_implementation_report_p0a_postgresql_minio_compensation, docs_backup_restore_post_restore_verification, docs_p0a_traceability_matrix_postgresql_minio_integrity_evidence [INFERRED 0.85]
- **Operational Resilience Controls** — docs_backup_restore_backup_restore_procedure, docs_incident_runbook_incident_runbook, docs_p0a2_integration_recovery_distinct_recovery_targets, docs_p0a4_closure_manual_vps_scope [INFERRED 0.85]

## Communities (23 total, 3 thin omitted)

### Community 0 - "API and Audio Orchestration"
Cohesion: 0.18
Nodes (39): create_token(), verify_password(), parse_filters(), stream_file(), audio(), audio_error(), audit(), check_csrf() (+31 more)

### Community 1 - "Web Interface Workflows"
Cohesion: 0.07
Nodes (34): Base Application Template, cookieValue, CSRF Token Form Injection, Role-Aware Navigation, Corpus Statistics, Corpus Dashboard Template, Benchmark Export Filtering, Corpus Export Template (+26 more)

### Community 2 - "Core Data and Authentication"
Cohesion: 0.12
Nodes (23): get_current_user(), hash_password(), Request, Session, Base, get_db(), startup(), AuditLog (+15 more)

### Community 3 - "Corpus Export Test Doubles"
Cohesion: 0.12
Nodes (15): FakeDB, FakeQuery, FakeResponse, parametrize, record(), test_benchmark_strict_false_excludes_technical_anomaly_and_counts_it(), test_benchmark_strict_rejects_unverified_without_archive(), test_build_export_contains_audio_metadata_manifest_and_checksums() (+7 more)

### Community 4 - "Operations and Recovery"
Cohesion: 0.11
Nodes (22): Backup and Restore Procedure, Isolated Restore Safety, Post-Restore Reconciliation and Alembic Verification, Pilot Recovery Objectives, P0-A Implementation Report, PostgreSQL-MinIO Compensation Strategy, P0-A Residual Risks, Initial Container Test Collection Gap (+14 more)

### Community 5 - "Storage Failure Handling"
Cohesion: 0.21
Nodes (15): delete_file(), get_bytes(), list_files(), put_file(), login(), remaining_recording(), test_audio_negative_inputs_have_controlled_responses_and_no_ready_rows(), test_concurrent_duplicate_returns_one_success_and_one_conflict() (+7 more)

### Community 6 - "Runtime Configuration Validation"
Cohesion: 0.16
Nodes (12): Settings, BaseSettings, model_validator, test_production_error_does_not_contain_secret(), test_production_rejects_short_jwt(), test_production_requires_secure_cookie(), test_test_configuration_is_valid(), parametrize (+4 more)

### Community 7 - "Remediation Evidence Tests"
Cohesion: 0.39
Nodes (16): Recording, login(), parametrize, test_audio_failures_cross_upload_route_without_ready(), test_commit_failure_compensates_both_real_objects_and_session_recovers(), test_duration_boundaries_cross_upload_route(), test_partial_compensation_leaves_real_orphan_detected_by_reconcile(), test_partial_delete_is_not_silent_and_retry_succeeds() (+8 more)

### Community 8 - "Export and Validation Governance"
Cohesion: 0.13
Nodes (17): Benchmark Export Mode, Corpus ZIP Export, CSV Formula Injection Protection, Export Archive Layout, Read-Only Corpus Export, Strict Export Validation, Isolated P0-A.1 Test Project, P0-A.1 Technical Validation (+9 more)

### Community 9 - "Corpus Export Engine"
Cohesion: 0.27
Nodes (9): build_export(), classify_storage_error(), ExportFailure, Exception, Session, _query(), Read-only, bounded-resource corpus ZIP export., _read_validate_object() (+1 more)

### Community 10 - "Deployment Services and Dependencies"
Cohesion: 0.24
Nodes (11): Corpus Manager Application Service, Internal Backend Network, PostgreSQL Database Service, External Frontend Network, MinIO Object Storage Service, Traefik HTTPS Routing, Alembic 1.16.4, FastAPI 0.116.1 (+3 more)

### Community 11 - "HTTP Integration Tests"
Cohesion: 0.50
Nodes (8): stat_file(), create_participant(), create_user(), csrf(), login(), test_end_to_end_http_postgres_minio_permissions_and_reconcile(), test_http_csrf_and_invalid_audio_are_rejected(), wav_bytes()

### Community 12 - "Isolated Recovery Test Stack"
Cohesion: 0.29
Nodes (8): app-test Service, Backup and Restore Validation, db-restore Service, db-test Service, minio-restore Service, minio-test Service, test Service, Backup and Restore Tools Service

### Community 13 - "Audio Command Safety"
Cohesion: 0.38
Nodes (6): ConversionSaturated, Exception, run_audio_command(), test_audio_command_always_releases_slot(), test_audio_command_never_uses_shell(), test_audio_command_rejects_saturated_slot()

## Knowledge Gaps
- **28 isolated node(s):** `generate_secret.sh script`, `Mobile Money Corpus Manager`, `Role-Aware Navigation`, `cookieValue`, `Corpus Statistics` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 79 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Recording` connect `Remediation Evidence Tests` to `API and Audio Orchestration`, `Core Data and Authentication`, `Storage Failure Handling`, `Corpus Export Engine`, `HTTP Integration Tests`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `Settings` connect `Runtime Configuration Validation` to `Core Data and Authentication`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `P0-A Implementation Report` connect `Operations and Recovery` to `Deployment Services and Dependencies`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Recording` (e.g. with `_query()` and `audio()`) actually correct?**
  _`Recording` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `upload_recording()` (e.g. with `Participant` and `Recording`) actually correct?**
  _`upload_recording()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `generate_secret.sh script`, `Mobile Money Corpus Manager`, `Role-Aware Navigation` to the rest of the system?**
  _28 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Web Interface Workflows` be split into smaller, more focused modules?**
  _Cohesion score 0.0659536541889483 - nodes in this community are weakly interconnected._