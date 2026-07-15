const { test, expect } = require('@playwright/test');
const { AUTH, openPortal, gotoTab } = require('../helpers');
const { reseed, makeInvoicedOrder } = require('../setup-data');

// S10 — In/PDF: từ portal mở bản in hoá đơn -> nội dung chứa trường TT99 bắt buộc
// + số liệu khớp màn hình. (Portal xuất bản in HTML; khách in ra PDF từ trình duyệt.)
test.use({ storageState: AUTH('customerA') });

let siName;
test.beforeAll(() => { reseed(); siName = makeInvoicedOrder(); });

test('S10: bản in hoá đơn TT99 chứa trường bắt buộc + số liệu khớp', async ({ page, context }) => {
  await openPortal(page);
  await gotoTab(page, 'debt');

  const invCard = page.locator('#invoices-list .order-card', { hasText: siName });
  await expect(invCard).toBeVisible({ timeout: 15000 });

  // Bấm "Tải hoá đơn" -> mở tab mới chứa bản in HTML.
  const [popup] = await Promise.all([
    context.waitForEvent('page'),
    invCard.getByRole('button', { name: /Tải hoá đơn/i }).click(),
  ]);
  // Nội dung bản in được ghi ASYNC (fetch xong mới document.write) — auto-wait
  // tới khi thân trang có nội dung thật thay cho "Đang tải…".
  const body = popup.locator('body');
  await expect(body).toContainText('HOÁ ĐƠN', { timeout: 15000 });  // tên chứng từ
  const html = await popup.content();

  // Trường TT99 bắt buộc + số liệu khớp.
  expect(html).toMatch(/MST/);                  // mã số thuế
  expect(html).toContain(siName);               // số chứng từ
  expect(html).toMatch(/bằng chữ/);             // số tiền bằng chữ
  expect(html).toMatch(/Ký/);                   // block chữ ký
  expect(html).toContain('40.000');             // tổng tiền
  expect(html).toMatch(/Bốn mươi nghìn đồng/i); // đọc chữ
});
