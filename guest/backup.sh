#!/usr/bin/env bash
# guest/backup.sh — chạy bởi systemd timer; sao lưu site vào /data/backups (đĩa bền).
set -euo pipefail
DATA_DIR="${DATA_DIR:-/data}"
SITE_NAME="${SITE_NAME:-supplycore.local}"
mkdir -p "$DATA_DIR/backups"
bench --site "$SITE_NAME" backup --with-files --backup-path "$DATA_DIR/backups"
