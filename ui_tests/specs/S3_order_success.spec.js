const { test, expect } = require('@playwright/test');
const { AUTH, openPortal, gotoTab, setQty } = require('../helpers');
const { seed } = require('../config');

// S3 — Gọi hàng thành công: điền SL hợp lệ -> submit -> thông báo thành công +
// đơn xuất hiện trong danh sách với trạng thái Chờ duyệt.
test.use({ storageState: AUTH('customerA') });

test('S3: gọi hàng hợp lệ tạo đơn Chờ duyệt', async ({ page }) => {
  await openPortal(page);
  await gotoTab(page, 'order');

  await setQty(page, seed.item_stock, 5);
  await expect(page.locator('#btn-submit-order')).toBeEnabled();
  await page.locator('#btn-submit-order').click();

  // Thông báo thành công (server trả tên đơn).
  const alert = page.locator('#order-alert .alert-success');
  await expect(alert).toBeVisible({ timeout: 15000 });
  await expect(alert).toContainText('Đặt hàng thành công');
  await expect(alert).toContainText('Chờ duyệt');
  const orderCode = (await alert.locator('.mono').first().textContent())?.trim();
  expect(orderCode).toMatch(/^SC-SO-/);

  // Đơn xuất hiện trong tab Đơn hàng với trạng thái Chờ duyệt.
  await gotoTab(page, 'orders');
  const card = page.locator('.order-card', { hasText: orderCode });
  await expect(card).toBeVisible({ timeout: 15000 });
  await expect(card.locator('.badge')).toContainText('Chờ duyệt');
});
