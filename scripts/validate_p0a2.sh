#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT=mobile-money-corpus-p0a2-test
C=(docker compose -p "$PROJECT" -f docker-compose.test.yml)
cleanup(){ if [[ "${KEEP_TEST_ENV:-0}" != 1 ]]; then "${C[@]}" ps -a; docker volume ls --filter "name=$PROJECT"; docker network ls --filter "name=$PROJECT"; "${C[@]}" down --volumes --remove-orphans; else echo "KEEP_TEST_ENV=1: environment kept"; fi; }
trap cleanup EXIT
python3 -m compileall -q app migrations tests scripts
docker compose config --quiet
"${C[@]}" config --quiet
"${C[@]}" build
"${C[@]}" up -d db-test minio-test app-test
"${C[@]}" run --rm --entrypoint pytest test -q -ra
