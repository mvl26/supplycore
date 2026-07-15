#!/usr/bin/env bash
# Dựng/seed môi trường cho UI test (Playwright). Idempotent — chạy lại được nhiều lần.
#
#   bash scripts/setup_test_env.sh
#
# - Seed user nội bộ (Manager/Storekeeper... pass TestPass123!) qua seed_test_users.
# - Seed dataset UI test (KH A/B + KH nợ + item tồn/hết tồn + HĐ khung) qua
#   seed_ui_test.write_state → ghi ui_tests/seed-state.json cho test đọc.
#
# An toàn: CHỈ trỏ vào SITE test cấu hình dưới đây. Đổi SITE nếu cần.
set -euo pipefail

SITE="${SC_TEST_SITE:-supplycore-miyano.local}"
BENCH_DIR="${SC_BENCH_DIR:-/home/hoangvietyeuem/frappe-bench-yhct}"

echo "==> Site test: $SITE (bench: $BENCH_DIR)"
cd "$BENCH_DIR"

# Bảo vệ: xác nhận site tồn tại trước khi seed.
if [ ! -d "sites/$SITE" ]; then
  echo "!! Site '$SITE' không tồn tại trong $BENCH_DIR/sites — DỪNG." >&2
  exit 1
fi

echo "==> Đảm bảo role nhãn 'Khách hàng' + gán cho user portal (idempotent)"
bench --site "$SITE" execute supplycore.setup.ensure_customer_role.run

echo "==> Đảm bảo Print Format TT99 + default_print_format (idempotent)"
# Chạy trực tiếp execute() — KHÔNG dựa vào bench migrate (patch có thể đã log ở
# môi trường đã migrate trước đó nên migrate sẽ không chạy lại). Bước này tạo lại
# print format + đặt default_print_format + clear cache → S10 luôn có TT99.
bench --site "$SITE" execute supplycore.patches.v0_11.create_tt99_print_formats.execute

echo "==> Seed user nội bộ (roles)"
bench --site "$SITE" execute supplycore.setup.seed_test_users.run

echo "==> Seed dataset UI test + ghi seed-state.json"
bench --site "$SITE" execute supplycore.setup.seed_ui_test.write_state

echo "==> Xong. seed-state.json:"
cat "$BENCH_DIR/apps/supplycore/ui_tests/seed-state.json" 2>/dev/null || echo "(chưa thấy file — kiểm tra output trên)"
