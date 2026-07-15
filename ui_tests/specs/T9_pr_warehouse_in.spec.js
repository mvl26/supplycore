const { test, expect } = require('@playwright/test');
const { AUTH } = require('../helpers');
const { makePrReadyForConfirm } = require('../setup-data');

// T9 — Trọn luồng nhập kho 2 bước trên UI: phiếu Đã tiếp nhận (QC Pass) ->
// bấm "Xác nhận nhập kho" -> trạng thái đổi 'Đã nhập kho'. Nhãn "Phiếu tiếp nhận tạm".
test.use({ storageState: AUTH('approver') }); // test.manager có role SupplyCore Manager

let prName;
test.beforeAll(() => { prName = makePrReadyForConfirm(); });

test('T9: xác nhận nhập kho trên UI đổi trạng thái Đã nhập kho', async ({ page }) => {
  await page.goto(`/supplycore/doc/SC Purchase Receipt/${encodeURIComponent(prName)}`,
    { waitUntil: 'domcontentloaded' });
  await expect(page.getByText(prName, { exact: false }).first()).toBeVisible({ timeout: 30000 });

  // Nhãn "Phiếu tiếp nhận tạm" hiển thị (accentLabel detail view).
  await expect(page.getByText('Phiếu tiếp nhận tạm').first()).toBeVisible({ timeout: 15000 });

  // Trạng thái ban đầu (QC đạt, chưa nhập kho) → badge "Chờ nhập kho" + có nút xác nhận.
  const confirmBtn = page.getByRole('button', { name: 'Xác nhận nhập kho', exact: true });
  await expect(confirmBtn).toBeVisible({ timeout: 15000 });

  // Bấm "Xác nhận nhập kho" -> modal (ngày, để trống) -> Xác nhận.
  await confirmBtn.click();
  await page.getByRole('button', { name: /^Xác nhận$/i }).last().click();

  // Reload lấy trạng thái cuối -> "Đã nhập kho" + nút xác nhận biến mất.
  await page.waitForTimeout(1500);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Đã nhập kho').first()).toBeVisible({ timeout: 20000 });
  await expect(page.getByRole('button', { name: 'Xác nhận nhập kho', exact: true })).toHaveCount(0);
});
