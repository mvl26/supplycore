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

IMAGE="${SC_IMAGE:-ghcr.io/mvl26/supplycore:latest}"

# uid:gid user frappe trong image (mặc định 1000) — override entrypoint để chỉ chạy `id`.
FRAPPE_UID="$(docker run --rm --entrypoint id "$IMAGE" -u frappe 2>/dev/null || true)"; FRAPPE_UID="${FRAPPE_UID:-1000}"
FRAPPE_GID="$(docker run --rm --entrypoint id "$IMAGE" -g frappe 2>/dev/null || true)"; FRAPPE_GID="${FRAPPE_GID:-1000}"

# Bind-mount /data/sites RỖNG không được Docker tự seed như named volume → thiếu
# sites/common_site_config.json + apps.txt mà image đã dựng sẵn (→ configurator chết).
# Seed 1 lần từ image khi rỗng. Chạy như ROOT (--user 0 + override entrypoint=bash để
# tránh entrypoint "Linking fresh assets" của image) → ghi được vào /dst dù /dst root-owned.
# (Khi update: disk1 đã có site → sites KHÔNG rỗng → bỏ qua, giữ nguyên dữ liệu.)
if [ -z "$(ls -A "$DATA_DIR/sites" 2>/dev/null)" ]; then
  echo "first-boot: seed sites/ từ image (lần đầu)"
  docker run --rm --user 0 --entrypoint bash -v "$DATA_DIR/sites:/dst" "$IMAGE" \
    -c 'cp -a /home/frappe/frappe-bench/sites/. /dst/'
fi

# chown BẮT BUỘC: bind mount giữ owner host (=root); container frappe (uid trên) phải ghi được sites/.
chown -R "$FRAPPE_UID:$FRAPPE_GID" "$DATA_DIR/sites" 2>/dev/null || true

# DB_PASSWORD bền theo disk1: sinh 1 lần (atomic temp+mv), đọc lại nếu đã có.
# Dùng -s (tồn tại VÀ khác rỗng) tránh kẹt file 0 byte nếu lần trước openssl chết giữa chừng.
DB_PW_FILE="$DATA_DIR/.db_password"
if [ ! -s "$DB_PW_FILE" ]; then
  ( umask 077; openssl rand -hex 24 > "$DB_PW_FILE.tmp" && mv "$DB_PW_FILE.tmp" "$DB_PW_FILE" )
  echo "first-boot: DB_PASSWORD generated"
else
  echo "first-boot: DB_PASSWORD reused"
fi
# Đẩy ngay xuống disk1 (đề phòng VM tắt trước khi ext4 commit/Docker giữ /data bận khi shutdown).
sync || true
DB_PASSWORD="$(cat "$DB_PW_FILE")"
export DB_PASSWORD

compose_up() {
  docker compose -f "$COMPOSE_DIR/compose.yml" -f "$COMPOSE_DIR/compose.override.yml" "$@"
}

# Dump trạng thái + log mọi service khi có sự cố (để debug từ serial log).
dump_compose() {
  echo "===== first-boot: DUMP compose ps ====="
  compose_up ps || true
  echo "===== first-boot: DUMP compose logs (tail) ====="
  compose_up logs --no-color --tail=120 || true
  echo "===== end dump ====="
}

# Đưa stack lên. Compose chờ create-site completed_successfully rồi mới start backend.
# Nếu up thất bại (vd configurator/create-site exit !=0) → in log đầy đủ rồi thoát lỗi.
if ! compose_up up -d; then
  echo "first-boot: 'compose up -d' THẤT BẠI — log bên dưới:"
  dump_compose
  exit 1
fi

# Chờ backend sẵn sàng trước khi migrate (tránh race cold boot).
for _ in $(seq 1 60); do
  if compose_up exec -T backend bench --site "$SITE_NAME" version >/dev/null 2>&1; then
    break
  fi
  sleep 5
done

# create-site đã tạo site; migrate áp schema mới khi update (idempotent, an toàn lần đầu).
if ! bench --site "$SITE_NAME" migrate; then
  echo "first-boot: 'bench migrate' THẤT BẠI — log bên dưới:"
  dump_compose
  exit 1
fi
