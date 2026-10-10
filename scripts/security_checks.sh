#!/usr/bin/env bash
set -Eeuo pipefail

# Optional scanners are reported as unavailable; no secrets or scanner dumps
# are emitted.  The checks are deliberately reproducible in CI and Docker.
python3 -m compileall -q app migrations scripts tests
docker compose config --quiet
docker compose -f docker-compose.test.yml config --quiet

if command -v bandit >/dev/null 2>&1; then bandit -q -r app; else echo "SAST=SKIPPED bandit-unavailable"; fi
if command -v pip-audit >/dev/null 2>&1; then pip-audit -r requirements.txt --format=columns; else echo "SCA=SKIPPED pip-audit-unavailable"; fi
if command -v gitleaks >/dev/null 2>&1; then gitleaks detect --no-banner --redact; else echo "SECRETS=SKIPPED gitleaks-unavailable"; fi
if [[ -f package-lock.json ]]; then npm audit --audit-level=high --omit=dev; else echo "FRONTEND_SCA=NOT_APPLICABLE no-package-lock"; fi
