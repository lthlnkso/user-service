#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"
if [[ -z "${TARGET}" ]]; then
  echo "Usage: $0 dev|prod|all"
  exit 1
fi

stop_one() {
  local name="$1"
  local port="$2"
  local session="user-service-${name}"

  local pids
  pids="$(pgrep -f "uvicorn app.main:app --host 127.0.0.1 --port ${port}" || true)"
  if [[ -n "${pids}" ]]; then
    kill ${pids}
    echo "stopped ${session} (pid: ${pids})"
  else
    echo "${session} not running"
  fi

  if screen -list | grep -Eq "\\.${session}[[:space:]]"; then
    screen -S "${session}" -X quit || true
  fi
}

case "${TARGET}" in
  dev)
    stop_one "dev" "8011"
    ;;
  prod)
    stop_one "prod" "8010"
    ;;
  all)
    stop_one "dev" "8011"
    stop_one "prod" "8010"
    ;;
  *)
    echo "Usage: $0 dev|prod|all"
    exit 1
    ;;
esac

echo "active screen sessions:"
screen -list | grep -E "\\.user-service-(dev|prod)[[:space:]]" || true
