const { test, expect } = require('@playwright/test');
const { AUTH } = require('../helpers');
const { seed } = require('../config');
const { reseed, makeInvoicedOrder } = require('../setup-data');

// S11 — Phân quyền sâu: KH B truy cập TRỰC TIẾP dữ liệu của KH A (qua /api/resource)
// -> bị chặn (403/không lộ dữ liệu).
test.use({ storageState: AUTH('customerB') });

let siA;
test.beforeAll(() => { reseed(); siA = makeInvoicedOrder(); }); // hoá đơn thuộc KH A

async function expectForbidden(request, url) {
  const res = await request.get(url);
  // Chặn hợp lệ: 403 (forbidden) hoặc 404 (not found) — KHÔNG 200 kèm dữ liệu.
  expect([403, 404], `${url} phải bị chặn, nhận ${res.status()}`).toContain(res.status());
}

test('S11: KH B không truy cập được chứng từ/khách của KH A qua /api/resource', async ({ page }) => {
  const req = page.request;

  // Hoá đơn của KH A.
  await expectForbidden(req, `/api/resource/SC Sales Invoice/${encodeURIComponent(siA)}`);
  // Bản ghi khách hàng A.
  await expectForbidden(req, `/api/resource/SC Customer/${encodeURIComponent(seed.customer_a)}`);
  // Hợp đồng khung của KH A (lấy qua danh sách của A — KH B không được thấy).
  // Kiểm thêm: list SC Sales Invoice của KH B KHÔNG chứa hoá đơn của A.
  const listRes = await req.get('/api/resource/SC Sales Invoice?limit_page_length=0');
  if (listRes.status() === 200) {
    const body = await listRes.text();
    expect(body).not.toContain(siA);
  }
});
