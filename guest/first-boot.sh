#!/usr/bin/env bash
# guest/first-boot.sh — idempotent provisioning chạy bởi systemd oneshot mỗi lần boot.
set -euo pipefail
[ -d /opt/supplycore/bin ] && export PATH="/opt/supplycore/bin:$PATH"

DATA_DIR="${DATA_DIR:-/data}"
SITE_NAME="${SITE_NAME:-supplycore.local}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?ADMIN_PASSWORD bắt buộc}"
MARKER="$DATA_DIR/.provisioned"
COMPOSE_DIR="${COMPOSE_DIR:-/opt/supplycore}"

mkdir -p "$DATA_DIR/mariadb" "$DATA_DIR/sites" "$DATA_DIR/backups"

docker compose -f "$COMPOSE_DIR/compose.yml" -f "$COMPOSE_DIR/compose.override.yml" up -d

if [ ! -f "$MARKER" ]; then
  bench new-site "$SITE_NAME" --admin-password "$ADMIN_PASSWORD" --no-mariadb-socket --force
  bench --site "$SITE_NAME" install-app supplycore
  bench use "$SITE_NAME"
  touch "$MARKER"
else
  bench --site "$SITE_NAME" migrate
fi
