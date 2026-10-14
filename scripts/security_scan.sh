#!/usr/bin/env bash
set -Eeuo pipefail

report_dir="${1:-security-reports}"
mkdir -p "$report_dir"

command -v bandit >/dev/null 2>&1 || { echo "bandit unavailable" >&2; exit 2; }
command -v pip-audit >/dev/null 2>&1 || { echo "pip-audit unavailable" >&2; exit 2; }
command -v gitleaks >/dev/null 2>&1 || { echo "gitleaks unavailable" >&2; exit 2; }

bandit -r app -f json -o "$report_dir/bandit.json"
pip-audit -r requirements.txt -f json -o "$report_dir/pip-audit.json"
gitleaks detect --no-banner --redact --report-format json --report-path "$report_dir/gitleaks.json"
echo "Security scans completed: $report_dir"
