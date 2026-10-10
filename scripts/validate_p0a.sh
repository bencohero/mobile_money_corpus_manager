#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q app migrations tests
docker compose config --quiet
docker compose -f docker-compose.test.yml config --quiet
docker compose -f docker-compose.test.yml build
docker compose -f docker-compose.test.yml run --rm test pytest -q -ra
