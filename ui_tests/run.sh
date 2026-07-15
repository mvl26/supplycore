#!/usr/bin/env bash
# Chạy TOÀN BỘ UI test bằng một lệnh: seed môi trường + Playwright headless.
#   bash ui_tests/run.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$HERE/.." && pwd)"

echo "==> [1/2] Seed môi trường test"
bash "$APP_DIR/scripts/setup_test_env.sh"

echo "==> [2/2] Chạy Playwright (headless)"
cd "$HERE"
npx playwright test "$@"
