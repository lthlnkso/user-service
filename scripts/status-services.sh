#!/usr/bin/env bash
set -euo pipefail

show_one() {
  local name="$1"
  local port="$2"
  local pid
  pid="$(pgrep -f "uvicorn app.main:app --host 127.0.0.1 --port ${port}" || true)"
  if [[ -n "${pid}" ]]; then
    if curl -fsS "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
      echo "${name}: running (pid ${pid}) on 127.0.0.1:${port} health=ok"
    else
      echo "${name}: running (pid ${pid}) on 127.0.0.1:${port} health=fail"
    fi
  else
    echo "${name}: stopped"
  fi
}

show_one "prod" "8010"
show_one "dev" "8011"

echo "screen sessions:"
screen -list | grep -E "\\.user-service-(dev|prod)[[:space:]]" || true
