const { test, expect } = require('@playwright/test');
const { AUTH, openPortal, gotoTab, orderLine } = require('../helpers');
const { seed } = require('../config');
const { reseed } = require('../setup-data');

// S2 — Xem HĐ khung: số HĐ, hiệu lực, dòng hàng định mức/đã gọi/còn lại khớp seed.
test.use({ storageState: AUTH('customerA') });
test.beforeAll(() => reseed());

test('S2: HĐ khung hiển thị định mức/đã gọi/còn lại khớp seed', async ({ page }) => {
  await openPortal(page);
  await gotoTab(page, 'order');

  // Số HĐ khung của KH A hiển thị trong dropdown chọn HĐ (mã SC-SFC-...).
  await expect(page.locator('#contract-select')).toContainText(/SC-SFC-/, { timeout: 15000 });

  // Hiệu lực hiển thị.
  await expect(page.locator('[data-testid="contract-validity"]')).toContainText('Hiệu lực');

  // Dòng hàng ITEM_STOCK: định mức 100 / đã gọi 0 / còn lại 100 (KH A fresh).
  const line = orderLine(page, seed.item_stock);
  await expect(line).toBeVisible();
  await expect(line.locator('[data-testid="line-quota"]')).toContainText(String(seed.contract_qty));
  await expect(line.locator('[data-testid="line-sold"]')).toContainText('đã gọi 0');
  await expect(line.locator('[data-testid="line-remaining"]')).toContainText(String(seed.contract_qty));
});
