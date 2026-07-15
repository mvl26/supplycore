const { test, expect } = require('@playwright/test');
const { AUTH, openPortal, gotoTab, setQty } = require('../helpers');
const { seed } = require('../config');
const { reseed } = require('../setup-data');

// S5 — Nợ vượt ngưỡng: KH đang nợ > hạn mức -> gọi hàng bị chặn, hiện số tiền
// tối thiểu phải thanh toán.
test.use({ storageState: AUTH('customerDebt') });
test.beforeAll(() => reseed());

test('S5: nợ vượt ngưỡng chặn gọi hàng + hiện số tối thiểu phải trả', async ({ page }) => {
  await openPortal(page);
  await gotoTab(page, 'order');

  await setQty(page, seed.item_stock, 1);
  await page.locator('#btn-submit-order').click();

  const alert = page.locator('#order-alert .alert-error');
  await expect(alert).toBeVisible({ timeout: 15000 });
  await expect(alert).toContainText('BRU-AR-001');
  await expect(alert).toContainText('tối thiểu');
  // Dư nợ 100.000, hạn mức 50.000, đơn 10.000 -> min phải trả = 60.000.
  await expect(alert).toContainText('60000');

  // Không có đơn được tạo thành công.
  await expect(page.locator('#order-alert .alert-success')).toHaveCount(0);
});
