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
  export SITE_NAME="supplycore.local"
}
teardown() { rm -rf "$TEST_DIR"; }

@test "lần đầu: tạo site + cài app khi marker chưa tồn tại" {
  run bash guest/first-boot.sh
  [ "$status" -eq 0 ]
  grep -q "new-site" "$STUB_LOG"
  grep -q "install-app supplycore" "$STUB_LOG"
  [ -f "$DATA_DIR/.provisioned" ]
}

@test "lần sau: KHÔNG tạo lại site, chạy migrate" {
  touch "$DATA_DIR/.provisioned"
  run bash guest/first-boot.sh
  [ "$status" -eq 0 ]
  ! grep -q "new-site" "$STUB_LOG"
  grep -q "migrate" "$STUB_LOG"
}
