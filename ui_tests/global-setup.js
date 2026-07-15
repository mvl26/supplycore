// Global setup: đăng nhập từng vai qua form /login, lưu storageState tái sử dụng.
const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const { BASE_URL, ROLES } = require('./config');

async function loginAndSave(browser, role) {
  const ctx = await browser.newContext({ baseURL: BASE_URL });
  const page = await ctx.newPage();
  await page.goto('/login', { waitUntil: 'domcontentloaded' });

  // Form login mặc định của Frappe: #login_email + #login_password + .btn-login.
  await page.fill('#login_email', role.email);
  await page.fill('#login_password', role.password);
  await page.click('.btn-login');

  // Login của Frappe là AJAX rồi redirect JS → poll cookie sid tới 20s.
  let sid = null;
  for (let i = 0; i < 40; i++) {
    const cookies = await ctx.cookies();
    sid = cookies.find((c) => c.name === 'sid' && c.value && c.value !== 'Guest');
    if (sid) break;
    await page.waitForTimeout(500); // poll — không có sự kiện DOM ổn định để chờ
  }
  if (!sid) {
    const err = await page.locator('#login-error, .alert-danger, .msgprint').textContent().catch(() => '');
    throw new Error(`Login THẤT BẠI cho ${role.email} — không có sid. Lỗi trang: ${(err || '').slice(0, 150)}`);
  }

  const dir = path.dirname(path.join(__dirname, role.storage));
  fs.mkdirSync(dir, { recursive: true });
  await ctx.storageState({ path: path.join(__dirname, role.storage) });
  await ctx.close();
  console.log(`  ✓ auth saved: ${role.email}`);
}

module.exports = async () => {
  // Chốt an toàn: chỉ chạy khi baseURL trỏ site test đã biết (nginx port 80 hoặc :8002).
  if (!/^https?:\/\/supplycore-miyano\.local(:8002)?\/?$|test-mvl\.localhost/.test(BASE_URL)) {
    throw new Error(`baseURL không phải site test (${BASE_URL}) — DỪNG để tránh chạy nhầm site.`);
  }
  console.log(`Global setup: đăng nhập các vai trên ${BASE_URL}`);
  const browser = await chromium.launch();
  try {
    for (const key of Object.keys(ROLES)) {
      await loginAndSave(browser, ROLES[key]);
    }
  } finally {
    await browser.close();
  }
};
