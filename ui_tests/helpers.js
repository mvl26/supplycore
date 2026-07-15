// Helpers dùng chung cho spec portal.
const path = require('path');

const AUTH = (role) => path.join(__dirname, '.auth', `${role}.json`);

// Mở portal + chờ header tên khách hiển thị (portal đã nạp).
async function openPortal(page) {
  await page.goto('/portal', { waitUntil: 'domcontentloaded' });
  await page.locator('#hdr-customer-name').waitFor({ state: 'visible', timeout: 20000 });
}

// Vào tab bằng data-goto trên navbar.
async function gotoTab(page, tab) {
  await page.locator(`#sc-navbar .navitem[data-goto="${tab}"]`).click();
  await page.locator(`#tab-${tab}.tab-panel.active`).waitFor({ state: 'visible', timeout: 10000 });
}

// Trong tab Đặt hàng: chọn HĐ khung (nếu nhiều) và trả về dòng theo mã item.
function orderLine(page, itemCode) {
  return page.locator(`[data-testid="order-line"][data-item="${itemCode}"]`);
}

// Đặt số lượng cho 1 item trong tab Đặt hàng.
async function setQty(page, itemCode, qty) {
  const line = orderLine(page, itemCode);
  const input = line.locator('.qty-input');
  await input.fill(String(qty));
  await input.dispatchEvent('input');
}

module.exports = { AUTH, openPortal, gotoTab, orderLine, setQty };
