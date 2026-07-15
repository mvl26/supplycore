const { test, expect } = require('@playwright/test');
const { AUTH, openPortal, gotoTab, setQty } = require('../helpers');
const { seed } = require('../config');

// S6 — Gọi hàng hết tồn: chọn mặt hàng seed hết tồn -> bị chặn với thông báo đúng.
// ITEM_EMPTY nằm trong định mức (còn 100) nhưng tồn kho = 0 -> BRU-INV-002.
test.use({ storageState: AUTH('customerA') });

test('S6: hết tồn kho chặn gọi hàng (BRU-INV-002)', async ({ page }) => {
  await openPortal(page);
  await gotoTab(page, 'order');

  // ITEM_EMPTY: quota còn nhưng tồn 0 -> qua check client (còn định mức), server chặn.
  await setQty(page, seed.item_empty, 5);
  await page.locator('#btn-submit-order').click();

  const alert = page.locator('#order-alert .alert-error');
  await expect(alert).toBeVisible({ timeout: 15000 });
  await expect(alert).toContainText('BRU-INV-002');
  await expect(alert).toContainText(/tồn kho|không đủ/i);

  await expect(page.locator('#order-alert .alert-success')).toHaveCount(0);
});
