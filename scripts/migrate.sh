#!/usr/bin/env bash
set -Eeuo pipefail

# Explicit, operator-approved schema change. The application startup command
# intentionally does not call this script.
alembic -c "${ALEMBIC_CONFIG:-alembic.ini}" upgrade "${ALEMBIC_TARGET:-head}"
alembic -c "${ALEMBIC_CONFIG:-alembic.ini}" current
