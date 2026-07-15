// Cấu hình tập trung cho UI test — credentials + URL + seed-state.
// KHÔNG hard-code rải rác trong spec; mọi spec import từ đây.
const fs = require('fs');
const path = require('path');

// baseURL site TEST — qua NGINX (port 80) của site supplycore-miyano.local.
// LƯU Ý: nginx (80) phục vụ /assets + proxy động về gunicorn bench-yhct (:8002).
// KHÔNG dùng :8002 trực tiếp — gunicorn chạy qua supervisor KHÔNG serve /assets
// (thiếu SharedDataMiddleware) → SPA/desk/login-form hỏng. Site này KHÁC :8000/:8001.
const BASE_URL = process.env.SC_BASE_URL || 'http://supplycore-miyano.local';

// State do seed_ui_test.write_state ghi ra (chạy scripts/setup_test_env.sh trước).
let seed = {};
try {
  seed = JSON.parse(fs.readFileSync(path.join(__dirname, 'seed-state.json'), 'utf8'));
} catch (e) {
  // Để test báo lỗi rõ ràng nếu thiếu seed thay vì fail mơ hồ.
  seed = {};
}

const PASSWORD = seed.password || 'TestPass123!';

const ROLES = {
  customerA: { email: seed.email_a || 'ui.custa@sc.local', password: PASSWORD, storage: '.auth/customerA.json' },
  customerB: { email: seed.email_b || 'ui.custb@sc.local', password: PASSWORD, storage: '.auth/customerB.json' },
  customerDebt: { email: seed.email_debt || 'ui.custdebt@sc.local', password: PASSWORD, storage: '.auth/customerDebt.json' },
  approver: { email: 'test.manager@sc.local', password: 'TestPass123!', storage: '.auth/approver.json' },
};

module.exports = { BASE_URL, ROLES, PASSWORD, seed };
