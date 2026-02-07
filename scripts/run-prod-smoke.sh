#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/lthlnkso/users/user-service"
BASE_URL="${PROD_BASE_URL:-https://users.lthlnkso.com}"

cd "${ROOT_DIR}"

echo "Running prod smoke tests against: ${BASE_URL}"
RUN_PROD_TESTS=1 PROD_BASE_URL="${BASE_URL}" \
  "${ROOT_DIR}/.venv/bin/pytest" -q tests_prod/test_prod_smoke.py "$@"
