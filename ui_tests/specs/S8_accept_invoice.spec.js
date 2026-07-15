const { test, expect } = require('@playwright/test');
const { AUTH, openPortal, gotoTab } = require('../helpers');
const { reseed, makeDeliveredDn, makeInvoiceFromDn } = require('../setup-data');

// S8 — Nghiệm thu trên portal: KH thấy phiếu giao -> xác nhận nhận hàng ->
// trạng thái biên bản đổi -> (nhân viên xuất HĐ) -> hoá đơn hiện với số tiền đúng.
test.use({ storageState: AUTH('customerA') });

let dnName;
test.beforeAll(() => { reseed(); dnName = makeDeliveredDn(); });

test('S8: KH xác nhận nhận hàng -> nghiệm thu -> hoá đơn hiển thị đúng số tiền', async ({ page }) => {
  await openPortal(page);
  await gotoTab(page, 'deliveries');

  const card = page.locator('.order-card', { hasText: dnName });
  await expect(card).toBeVisible({ timeout: 15000 });
  await expect(card.locator('.badge')).toContainText('Đã giao');

  // Xác nhận nhận hàng.
  await card.getByRole('button', { name: /Xác nhận nhận hàng/i }).click();

  // Sau xác nhận, phiếu giao chuyển "Đã nghiệm thu".
  const cardAfter = page.locator('.order-card', { hasText: dnName });
  await expect(cardAfter.locator('.badge')).toContainText('Đã nghiệm thu', { timeout: 15000 });

  // Bước nhân viên: xuất hoá đơn từ DN đã nghiệm thu.
  const siName = makeInvoiceFromDn();
  expect(siName).toMatch(/^SC-SI-/);

  // KH mở tab Công nợ -> hoá đơn hiện với số tiền đúng (qty 4 * 10.000 = 40.000).
  await gotoTab(page, 'debt');
  const invCard = page.locator('#invoices-list .order-card', { hasText: siName });
  await expect(invCard).toBeVisible({ timeout: 15000 });
  await expect(invCard).toContainText('40.000');
});
