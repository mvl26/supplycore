#!/usr/bin/env bash
# guest/first-boot.sh — systemd oneshot mỗi lần boot.
# Compose (service create-site) lo tạo site + cài app. Script này KHÔNG tạo site:
# đảm bảo DB_PASSWORD bền trên disk1, đưa stack lên (offline PULL_POLICY=never),
# chờ backend sẵn sàng, rồi bench migrate (idempotent — áp schema mới khi update).
set -euo pipefail
[ -d /opt/supplycore/bin ] && export PATH="/opt/supplycore/bin:$PATH"

DATA_DIR="${DATA_DIR:-/data}"
SITE_NAME="${SITE_NAME:-supplycore.localhost}"
COMPOSE_DIR="${COMPOSE_DIR:-/opt/supplycore}"
: "${ADMIN_PASSWORD:?ADMIN_PASSWORD bắt buộc}"
export SITE_NAME
export PULL_POLICY="${PULL_POLICY:-never}"
export HTTP_PORT="${HTTP_PORT:-80}"
export ADMIN_PASSWORD

mkdir -p "$DATA_DIR/mariadb" "$DATA_DIR/sites" "$DATA_DIR/backups"

# Bind-mount /data/sites do root tạo, nhưng container frappe ghi bằng uid 1000.
# chown để container ghi được (chạy root trong VM; no-op khi test non-root).
chown -R 1000:1000 "$DATA_DIR/sites" 2>/dev/null || true

# DB_PASSWORD bền theo disk1: sinh 1 lần (atomic temp+mv), đọc lại nếu đã có.
# Dùng -s (tồn tại VÀ khác rỗng) tránh kẹt file 0 byte nếu lần trước openssl chết giữa chừng.
DB_PW_FILE="$DATA_DIR/.db_password"
if [ ! -s "$DB_PW_FILE" ]; then
  ( umask 077; openssl rand -hex 24 > "$DB_PW_FILE.tmp" && mv "$DB_PW_FILE.tmp" "$DB_PW_FILE" )
  echo "first-boot: DB_PASSWORD generated"
else
  echo "first-boot: DB_PASSWORD reused"
fi
DB_PASSWORD="$(cat "$DB_PW_FILE")"
export DB_PASSWORD

compose_up() {
  docker compose -f "$COMPOSE_DIR/compose.yml" -f "$COMPOSE_DIR/compose.override.yml" "$@"
}

# Đưa stack lên. Compose chờ create-site completed_successfully rồi mới start backend.
compose_up up -d

# Chờ backend sẵn sàng trước khi migrate (tránh race cold boot).
for _ in $(seq 1 60); do
  if compose_up exec -T backend bench --site "$SITE_NAME" version >/dev/null 2>&1; then
    break
  fi
  sleep 5
done

# create-site đã tạo site; migrate áp schema mới khi update (idempotent, an toàn lần đầu).
bench --site "$SITE_NAME" migrate
