#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/lthlnkso/users/user-service"

echo "[1/5] Installing user-service systemd unit"
install -m 0644 "${REPO_DIR}/deploy/user-service.service" /etc/systemd/system/user-service.service

echo "[2/5] Installing cloudflared config"
cp /etc/cloudflared/config.yml /etc/cloudflared/config.yml.bak.$(date +%Y%m%d%H%M%S)
install -m 0644 "${REPO_DIR}/deploy/cloudflared-config.yml" /etc/cloudflared/config.yml

echo "[3/5] Running DB migrations"
sudo -u lthlnkso "${REPO_DIR}/.venv/bin/alembic" -c "${REPO_DIR}/alembic.ini" upgrade head

echo "[4/5] Restarting services"
systemctl daemon-reload
systemctl enable --now user-service
systemctl restart user-service
systemctl restart cloudflared

echo "[5/5] Status"
systemctl --no-pager --full status user-service | sed -n '1,30p'
systemctl --no-pager --full status cloudflared | sed -n '1,30p'
echo "Done."
