// Tạo dữ liệu tiền đề cho spec qua `bench execute` (test setup — hành động
// người dùng chính vẫn qua UI). Trả về tên doc do seed in "RESULT:<name>".
const { execSync } = require('child_process');

const BENCH_DIR = process.env.SC_BENCH_DIR || '/home/hoangvietyeuem/frappe-bench-yhct';
const SITE = process.env.SC_TEST_SITE || 'supplycore-miyano.local';

// Reseed toàn bộ về trạng thái gốc (cleanup + tạo lại) — dùng ở beforeAll các
// spec cần state xác định, chống flaky do dữ liệu tích luỹ giữa các spec.
function reseed() {
  execSync(`bench --site ${SITE} execute supplycore.setup.seed_ui_test.run`,
    { cwd: BENCH_DIR, encoding: 'utf8', timeout: 120000 });
}

function execSeed(func) {
  const out = execSync(
    `bench --site ${SITE} execute supplycore.setup.seed_ui_test.${func}`,
    { cwd: BENCH_DIR, encoding: 'utf8', timeout: 120000 }
  );
  const m = out.match(/RESULT:(\S+)/);
  if (!m) throw new Error(`seed ${func} không trả RESULT. Output: ${out.slice(-300)}`);
  return m[1];
}

module.exports = {
  reseed,
  makePendingOrder: () => execSeed('make_pending_order'),
  makeDeliveredDn: () => execSeed('make_delivered_dn'),
  makeInvoiceFromDn: () => execSeed('make_invoice_from_dn'),
  makeInvoicedOrder: () => execSeed('make_invoiced_order'),
  makePrReadyForConfirm: () => execSeed('make_pr_ready_for_confirm'),
};
