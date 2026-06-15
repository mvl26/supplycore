setup() {
  export TEST_DIR="$(mktemp -d)"
  export DATA_DIR="$TEST_DIR/data"; mkdir -p "$DATA_DIR"
  export STUB_LOG="$TEST_DIR/calls.log"
  export PATH="$TEST_DIR/bin:$PATH"; mkdir -p "$TEST_DIR/bin"
  cat > "$TEST_DIR/bin/bench" <<EOF
#!/usr/bin/env bash
echo "bench \$*" >> "$STUB_LOG"
EOF
  chmod +x "$TEST_DIR/bin/bench"
  export SITE_NAME="supplycore.local"
}
teardown() { rm -rf "$TEST_DIR"; }

@test "gọi bench backup --with-files vào /data/backups" {
  run bash guest/backup.sh
  [ "$status" -eq 0 ]
  grep -q "backup --with-files" "$STUB_LOG"
  [ -d "$DATA_DIR/backups" ]
}
