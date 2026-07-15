const { test, expect } = require('@playwright/test');
const { AUTH, openPortal, gotoTab, setQty, orderLine } = require('../helpers');
const { seed } = require('../config');

// S4 — Gọi hàng vượt định mức: SL > còn lại -> lỗi rõ ràng (nêu SL còn lại),
// đơn KHÔNG được tạo.
test.use({ storageState: AUTH('customerA') });

test('S4: vượt định mức bị chặn, hiện SL còn lại, không tạo đơn', async ({ page }) => {
  await openPortal(page);
  await gotoTab(page, 'order');

  const over = seed.contract_qty + 50; // 150 > 100
  await setQty(page, seed.item_stock, over);

  // Lỗi ngay tại dòng, nêu đúng SL còn lại (100).
  const line = orderLine(page, seed.item_stock);
  const lineErr = line.locator('.line-error');
  await expect(lineErr).toContainText('còn ' + seed.contract_qty, { timeout: 10000 });

  // Nếu vẫn bấm gửi -> chặn, không có thông báo thành công.
  const submit = page.locator('#btn-submit-order');
  if (await submit.count()) {
    await submit.click();
    await expect(page.locator('#order-alert .alert-error')).toBeVisible();
    await expect(page.locator('#order-alert .alert-success')).toHaveCount(0);
  }

  // Xác nhận không có đơn mới ở tab Đơn hàng cho số lượng vượt (đã gọi vẫn 0).
  await gotoTab(page, 'order');
  await expect(orderLine(page, seed.item_stock).locator('[data-testid="line-sold"]'))
    .toContainText('đã gọi 0');
});
