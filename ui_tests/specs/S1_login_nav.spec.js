const { test, expect } = require('@playwright/test');
const path = require('path');
const { seed } = require('../config');

// S1 — Đăng nhập & điều hướng: KH A thấy portal của mình, KHÔNG thấy dữ liệu KH B.
test.use({ storageState: path.join(__dirname, '..', '.auth', 'customerA.json') });

test('S1: KH A đăng nhập thấy portal của mình, không thấy dữ liệu KH B', async ({ page }) => {
  await page.goto('/portal', { waitUntil: 'domcontentloaded' });

  // Thấy tên KH A ở header (portal_me trả customer_name).
  const name = page.locator('#hdr-customer-name');
  await expect(name).toContainText('UITEST Khách Hàng A', { timeout: 20000 });

  // Không lộ tên KH B ở bất kỳ đâu trên trang.
  await expect(page.locator('body')).not.toContainText('UITEST Khách Hàng B');

  // Có thanh điều hướng portal (các tab).
  await expect(page.locator('#sc-navbar')).toBeVisible();
});
