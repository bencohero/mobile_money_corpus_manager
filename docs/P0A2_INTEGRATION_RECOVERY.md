# P0-A.2 Integration and recovery

The test project is exclusively `mobile-money-corpus-p0a2-test`, with a dedicated network and volumes `p0a2-test-*`. No production resource is used.

```bash
docker compose -f docker-compose.test.yml config --quiet
docker compose -f docker-compose.test.yml build
docker compose -f docker-compose.test.yml up -d db-test minio-test db-restore minio-restore app-test
docker compose -f docker-compose.test.yml run --rm --entrypoint pytest test -q -ra
```

The runtime image targets `runtime` and does not copy tests. The test image targets `test` and copies tests, migrations, scripts and Alembic. A fresh database is migrated by `alembic upgrade head`; observed revision: `0002_p0a_recording_sync`. Existing create_all schemas require inspection and compatibility comparison before conditional `stamp`; backup is mandatory.

Backup uses `pg_dump` and `mc` in `tools`. Restore targets a distinct empty PostgreSQL and MinIO. The target bucket is initialized explicitly; `CONFIRM_RESTORE=NO` is refused with code 2. Reconciliation is read-only by default: code 0 means no finding, code 1 means findings.

Before cleanup list compose resources, volumes and network filtered by `mobile-money-corpus-p0a2-test`, then use only:
```bash
docker compose -f docker-compose.test.yml down --volumes --remove-orphans
```

Remaining blockers: exhaustive PostgreSQL-MinIO fault simulations, complete four-role endpoint matrix, and every requested negative audio/reconciliation scenario.
