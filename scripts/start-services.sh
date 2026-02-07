#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"
if [[ -z "${TARGET}" ]]; then
  echo "Usage: $0 dev|prod|all"
  exit 1
fi

ROOT_DIR="/home/lthlnkso/users/user-service"
VENV_BIN="${ROOT_DIR}/.venv/bin"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"

start_one() {
  local name="$1"
  local port="$2"
  local db_url="$3"
  local uploads_dir="$4"
  local app_name="$5"
  local reload_flag="${6:-}"
  local log_file="${LOG_DIR}/${name}.log"

  local session="user-service-${name}"
  if pgrep -f "uvicorn app.main:app --host 127.0.0.1 --port ${port}" >/dev/null 2>&1; then
    echo "${session} already running"
    return
  fi

  (
    cd "${ROOT_DIR}"
    export APP_NAME="${app_name}"
    export DATABASE_URL="${db_url}"
    export UPLOADS_DIR="${uploads_dir}"
    "${VENV_BIN}/alembic" -c "${ROOT_DIR}/alembic.ini" upgrade head >/dev/null
  )

  mkdir -p "${ROOT_DIR}/${uploads_dir#./}"

  local cmd
  cmd="cd ${ROOT_DIR} && "
  cmd+="export APP_NAME='${app_name}' DATABASE_URL='${db_url}' UPLOADS_DIR='${uploads_dir}' && "
  cmd+="exec ${VENV_BIN}/uvicorn app.main:app --host 127.0.0.1 --port ${port} ${reload_flag} >> '${log_file}' 2>&1"

  screen -dmS "${session}" bash -lc "${cmd}"

  local i
  for i in {1..8}; do
    if curl -fsS "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  if curl -fsS "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
    echo "started ${session} on 127.0.0.1:${port}"
  else
    echo "failed to start ${session}; check ${log_file}"
    tail -n 50 "${log_file}" || true
    exit 1
  fi
}

case "${TARGET}" in
  dev)
    start_one "dev" "8011" "sqlite:///./user_service_dev.db" "./uploads_dev" "user-service-dev" "--reload"
    ;;
  prod)
    start_one "prod" "8010" "sqlite:///./user_service.db" "./uploads_prod" "user-service"
    ;;
  all)
    start_one "prod" "8010" "sqlite:///./user_service.db" "./uploads_prod" "user-service"
    start_one "dev" "8011" "sqlite:///./user_service_dev.db" "./uploads_dev" "user-service-dev" "--reload"
    ;;
  *)
    echo "Usage: $0 dev|prod|all"
    exit 1
    ;;
esac

echo "active screen sessions:"
screen -list | grep -E "\\.user-service-(dev|prod)[[:space:]]" || true
