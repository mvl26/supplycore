const { test, expect } = require('@playwright/test');
const { AUTH, openPortal, gotoTab, orderLine } = require('../helpers');
const { seed } = require('../config');
const { reseed, makeInvoicedOrder } = require('../setup-data');

// S9 — Công nợ & lịch sử: tổng đã gọi, số lần gọi, công nợ sau hoá đơn mới —
// số khớp tính tay từ seed + đơn qty 4 * 10.000 = 40.000.
test.use({ storageState: AUTH('customerA') });

let siName;
test.beforeAll(() => { reseed(); siName = makeInvoicedOrder(); });

test('S9: tổng đã gọi / số lần gọi / công nợ hiển thị đúng', async ({ page }) => {
  await openPortal(page);

  // Tab Đặt hàng: tổng đã gọi = 4, số lần gọi = 1 (1 đơn đã duyệt qty 4).
  await gotoTab(page, 'order');
  await expect(page.locator('[data-testid="contract-ordered-total"]')).toContainText('4', { timeout: 15000 });
  await expect(page.locator('[data-testid="contract-order-count"]')).toContainText('Số lần gọi: 1');
  // Dòng ITEM_STOCK: đã gọi 4 / còn lại 96.
  await expect(orderLine(page, seed.item_stock).locator('[data-testid="line-sold"]')).toContainText('đã gọi 4');
  await expect(orderLine(page, seed.item_stock).locator('[data-testid="line-remaining"]')).toContainText('còn lại 96');

  // Tab Công nợ: công nợ phải trả = 40.000, hoá đơn hiện.
  await gotoTab(page, 'debt');
  await expect(page.locator('#debt-summary')).toContainText('40.000', { timeout: 15000 });
  await expect(page.locator('#invoices-list .order-card', { hasText: siName })).toBeVisible();
});
