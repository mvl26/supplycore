const { test, expect } = require('@playwright/test');
const { AUTH, openPortal, gotoTab, setQty } = require('../helpers');
const { seed } = require('../config');
const { reseed } = require('../setup-data');

// S12 — Responsive nhanh: chạy lại S1–S3 với viewport mobile 390x844 -> form
// vẫn thao tác được.
test.use({ storageState: AUTH('customerA'), viewport: { width: 390, height: 844 } });
test.beforeAll(() => reseed());

test('S12: portal thao tác được trên mobile (đăng nhập/xem HĐ/gọi hàng)', async ({ page }) => {
  // S1: vào portal, thấy tên KH.
  await openPortal(page);
  await expect(page.locator('#hdr-customer-name')).toContainText('UITEST Khách Hàng A');

  // S2: tab Đặt hàng, thấy HĐ khung + dòng hàng.
  await gotoTab(page, 'order');
  await expect(page.locator('#contract-select')).toBeVisible();

  // S3: điền SL + gửi đơn thành công trên mobile.
  await setQty(page, seed.item_stock, 2);
  await expect(page.locator('#btn-submit-order')).toBeEnabled();
  await page.locator('#btn-submit-order').click();
  await expect(page.locator('#order-alert .alert-success')).toContainText('Đặt hàng thành công', { timeout: 15000 });
});
