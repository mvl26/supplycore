const { test, expect } = require('@playwright/test');
const { AUTH } = require('../helpers');
const { seed } = require('../config');
const { reseed, makePendingOrder } = require('../setup-data');

// S7 — Duyệt nội bộ (vai người duyệt, SPA /supplycore): duyệt đơn Chờ duyệt ->
// trạng thái đổi -> tạo phiếu giao hàng -> phiếu giao hiển thị.
test.use({ storageState: AUTH('approver') });

let orderName;
test.beforeAll(() => { reseed(); orderName = makePendingOrder(); });

test('S7: người duyệt duyệt đơn + sinh phiếu giao', async ({ page }) => {
  await page.goto(`/supplycore/doc/SC Sales Order/${encodeURIComponent(orderName)}`,
    { waitUntil: 'domcontentloaded' });

  // Chi tiết đơn nạp xong (mã đơn hiển thị).
  await expect(page.getByText(orderName, { exact: false }).first()).toBeVisible({ timeout: 30000 });

  // Bấm Duyệt.
  await page.getByRole('button', { name: 'Duyệt', exact: true }).click();

  // Trạng thái đổi sang "Đã duyệt" (reload để lấy trạng thái cuối, không phụ thuộc toast).
  await page.waitForTimeout(1500);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Đã duyệt').first()).toBeVisible({ timeout: 20000 });

  // Tạo phiếu giao — nhập kho xuất UITEST-KHO rồi xác nhận.
  await page.getByRole('button', { name: 'Tạo phiếu giao', exact: true }).click();
  const modal = page.locator('.modal, [role="dialog"]').filter({ hasText: 'phiếu giao' }).first();
  // Điền kho xuất (field 'Kho xuất...').
  const whInput = page.getByLabel(/Kho xuất/i);
  if (await whInput.count()) await whInput.first().fill(seed.warehouse);
  await page.getByRole('button', { name: /Xác nhận/i }).click();

  // Điều hướng sang Phiếu giao (SC Delivery Note) — URL hoặc tiêu đề DN xuất hiện.
  await expect(page).toHaveURL(/SC(%20|\s)Delivery(%20|\s)Note/i, { timeout: 25000 });
  await expect(page.getByText(/SC-DN-/).first()).toBeVisible({ timeout: 20000 });
});
