# tests/installer/test_first_boot.bats
setup() {
  export TEST_DIR="$(mktemp -d)"
  export DATA_DIR="$TEST_DIR/data"
  mkdir -p "$DATA_DIR"
  export STUB_LOG="$TEST_DIR/calls.log"
  export PATH="$TEST_DIR/bin:$PATH"
  mkdir -p "$TEST_DIR/bin"
  for cmd in docker bench; do
    cat > "$TEST_DIR/bin/$cmd" <<EOF
#!/usr/bin/env bash
echo "$cmd \$*" >> "$STUB_LOG"
EOF
    chmod +x "$TEST_DIR/bin/$cmd"
  done
  export ADMIN_PASSWORD="secret123"
  export SITE_NAME="supplycore.localhost"
  export COMPOSE_DIR="$TEST_DIR/opt"
  mkdir -p "$COMPOSE_DIR"
}
teardown() { rm -rf "$TEST_DIR"; }

@test "đưa stack lên + migrate, KHÔNG tạo site, KHÔNG marker" {
  run bash guest/first-boot.sh
  [ "$status" -eq 0 ]
  grep -q "compose .* up -d" "$STUB_LOG"
  grep -q "migrate" "$STUB_LOG"
  ! grep -q "new-site" "$STUB_LOG"
  ! grep -q "install-app" "$STUB_LOG"
  [ ! -f "$DATA_DIR/.provisioned" ]
}

@test "sinh DB_PASSWORD lần đầu vào /data/.db_password (0600)" {
  run bash guest/first-boot.sh
  [ "$status" -eq 0 ]
  [ -f "$DATA_DIR/.db_password" ]
  [ -s "$DATA_DIR/.db_password" ]
  perm="$(stat -c '%a' "$DATA_DIR/.db_password")"
  [ "$perm" = "600" ]
}

@test "DB_PASSWORD bền: tái dùng file đã có, không ghi đè" {
  echo "fixedpw123" > "$DATA_DIR/.db_password"
  run bash guest/first-boot.sh
  [ "$status" -eq 0 ]
  [ "$(cat "$DATA_DIR/.db_password")" = "fixedpw123" ]
}

@test "thiếu ADMIN_PASSWORD: thoát lỗi" {
  unset ADMIN_PASSWORD
  run bash guest/first-boot.sh
  [ "$status" -ne 0 ]
}
