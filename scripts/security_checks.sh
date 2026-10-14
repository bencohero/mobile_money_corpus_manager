#!/usr/bin/env bash
set -Eeuo pipefail

# Optional scanners are reported as unavailable; no secrets or scanner dumps
# are emitted.  The checks are deliberately reproducible in CI and Docker.
python3 -m compileall -q app migrations scripts tests
docker compose config --quiet
docker compose -f docker-compose.test.yml config --quiet

echo "Running mandatory security scanners"
bash scripts/security_scan.sh "${SECURITY_REPORT_DIR:-security-reports}"
if [[ -f package-lock.json ]]; then npm audit --audit-level=high --omit=dev; else echo "FRONTEND_SCA=NOT_APPLICABLE no-package-lock"; fi
