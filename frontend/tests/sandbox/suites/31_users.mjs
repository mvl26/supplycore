// Suite 31: User Management & RBAC
//
// 1. Sidebar có link "Người dùng & Quyền" (admin)
// 2. Trang /users render với bảng + nút "+ Tạo user"
// 3. Mở modal "+ Tạo user" — hiện list role checkboxes + panel giải thích rỗng
// 4. Tick 1 role → panel giải thích bên trái hiện chức năng/giới hạn của role
// 5. Tick role nguy hiểm (System Manager) → có badge "⚠ TỐI CAO"
// 6. Tạo user thật + verify xuất hiện trong bảng + cleanup
// 7. Mở Sửa quyền của user vừa tạo → roles được tick lại đúng
// 8. Toggle Bật/Tắt user

const RUN_ID = Date.now().toString(36)
const TEST_EMAIL = `rbac-test-${RUN_ID}@local.test`

async function cleanup(page, BASE, email) {
  // Xoá user qua bench Frappe API
  await page.evaluate(async (em) => {
    try {
      await fetch('/api/method/frappe.client.delete', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Frappe-CSRF-Token': window.sc_csrf || '',
        },
        body: `doctype=User&name=${encodeURIComponent(em)}`,
      })
    } catch (e) {}
  }, email)
}

export const tests = [
  {
    name: 'Sidebar có link "Người dùng & Quyền"',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/`)
      await page.waitForTimeout(800)
      const link = await page.locator('aside a[href*="/users"]').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return link >= 1
        ? { ok: true, detail: 'link found' }
        : { ok: false, detail: 'no sidebar link' }
    },
  },
  {
    name: 'Trang /users render — bảng + nút Tạo user',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/users`)
      await page.waitForTimeout(1500)
      const h1 = (await page.locator('h1').first().textContent()) || ''
      const createBtn = await page.locator('button:has-text("Tạo user")').count()
      const tableHeader = await page.locator('th:has-text("SupplyCore Roles")').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return h1.includes('Người dùng') && createBtn >= 1 && tableHeader >= 1
        ? { ok: true, detail: `h1="${h1}"` }
        : { ok: false, detail: `h1="${h1}", btn=${createBtn}, hdr=${tableHeader}` }
    },
  },
  {
    name: 'Modal Tạo user hiện list role checkboxes',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/users`)
      await page.waitForTimeout(1500)
      await page.click('button:has-text("+ Tạo user")')
      await page.waitForTimeout(700)
      // Check input email visible
      const emailVisible = await page.locator('input[type="email"]').isVisible()
      const checkboxes = await page.locator('label:has-text("SupplyCore")').count()
      // Panel rỗng hiện hướng dẫn
      const emptyHint = await page.locator('text=Tick vào role bên phải').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return emailVisible && checkboxes >= 5 && emptyHint >= 1
        ? { ok: true, detail: `${checkboxes} role checkboxes` }
        : { ok: false, detail: `email=${emailVisible}, cb=${checkboxes}, hint=${emptyHint}` }
    },
  },
  {
    name: 'Tick role → panel giải thích hiện chức năng + giới hạn',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/users`)
      await page.waitForTimeout(1500)
      await page.click('button:has-text("+ Tạo user")')
      await page.waitForTimeout(700)
      // Tick "SupplyCore Storekeeper"
      const lbl = page.locator('label', { hasText: 'SupplyCore Storekeeper' }).first()
      await lbl.scrollIntoViewIfNeeded()
      await lbl.locator('input[type="checkbox"]').first().check()
      await page.waitForTimeout(400)
      // Panel bên trái phải hiện Storekeeper + Chức năng + Giới hạn
      const heading = await page.locator('h4:has-text("Giải thích quyền đang chọn")').count()
      const dutyTxt = await page.locator('text=Chức năng:').count()
      const limitTxt = await page.locator('text=Giới hạn:').count()
      const storekeeperPanel = await page.locator('text=Thủ kho').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return heading >= 1 && dutyTxt >= 1 && limitTxt >= 1 && storekeeperPanel >= 1
        ? { ok: true, detail: 'duties + limits shown' }
        : { ok: false, detail: `hdr=${heading} duty=${dutyTxt} lim=${limitTxt} sk=${storekeeperPanel}` }
    },
  },
  {
    name: 'Tick System Manager → badge "⚠ TỐI CAO"',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/users`)
      await page.waitForTimeout(1500)
      await page.click('button:has-text("+ Tạo user")')
      await page.waitForTimeout(700)
      const lbl = page.locator('label', { hasText: 'System Manager' }).first()
      await lbl.scrollIntoViewIfNeeded()
      await lbl.locator('input[type="checkbox"]').first().check()
      await page.waitForTimeout(400)
      const danger = await page.locator('text=SIÊU QUYỀN').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return danger >= 1
        ? { ok: true, detail: 'SIÊU QUYỀN badge shown' }
        : { ok: false, detail: 'high-danger badge missing' }
    },
  },
  {
    name: `Tạo user ${TEST_EMAIL} với role Storekeeper + Auditor`,
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/users`)
      await page.waitForTimeout(1500)
      await page.click('button:has-text("+ Tạo user")')
      await page.waitForTimeout(700)
      // Fill form
      await page.fill('input[type="email"]', TEST_EMAIL)
      await page.fill('input[placeholder*="Nguyễn"]', 'Test RBAC User')
      await page.fill('input[placeholder*="Tự sinh"]', 'TestPwd-' + RUN_ID)
      // Uncheck send_welcome (để khỏi tìm SMTP)
      const welcome = page.locator('input[type="checkbox"]').filter({ has: page.locator('xpath=..//text()[contains(., "welcome")]') })
      // Đơn giản hơn — uncheck checkbox đầu trong modal nằm cạnh "Gửi welcome email"
      const welcomeLbl = page.locator('label:has-text("Gửi welcome email")')
      await welcomeLbl.locator('input[type="checkbox"]').uncheck().catch(() => null)
      // Tick 2 roles
      for (const r of ['SupplyCore Storekeeper', 'SupplyCore Auditor']) {
        const lbl = page.locator('label', { hasText: r }).first()
        await lbl.scrollIntoViewIfNeeded()
        await lbl.locator('input[type="checkbox"]').first().check()
        await page.waitForTimeout(200)
      }
      // Submit — footer button (last "Tạo user" trên page hiện là footer modal)
      const respP = page.waitForResponse(r => r.url().includes('users.create_user'), { timeout: 15000 })
      await page.locator('button:has-text("Tạo user")').last().click()
      const resp = await respP
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Verify hiện trong bảng
      const inTable = await page.locator(`td:has-text("${TEST_EMAIL}")`).count()
      return resp.status() === 200 && inTable >= 1
        ? { ok: true, detail: `created, in table=${inTable}` }
        : { ok: false, detail: `status=${resp.status()}, table=${inTable}` }
    },
  },
  {
    name: 'Sửa quyền user vừa tạo — roles được tick lại',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/users`)
      await page.waitForTimeout(1500)
      // Tìm row của user vừa tạo + click "Sửa quyền"
      const row = page.locator('tr', { hasText: TEST_EMAIL }).first()
      await row.locator('button:has-text("Sửa quyền")').click()
      await page.waitForTimeout(800)
      // Verify Storekeeper + Auditor đã tick
      const storekeeperChecked = await page.locator('label', { hasText: 'SupplyCore Storekeeper' })
        .first().locator('input[type="checkbox"]').isChecked()
      const auditorChecked = await page.locator('label', { hasText: 'SupplyCore Auditor' })
        .first().locator('input[type="checkbox"]').isChecked()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return storekeeperChecked && auditorChecked
        ? { ok: true, detail: 'both roles pre-ticked' }
        : { ok: false, detail: `sk=${storekeeperChecked}, aud=${auditorChecked}` }
    },
  },
  {
    name: 'Toggle Tắt → trạng thái cập nhật',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/users`)
      await page.waitForTimeout(1500)
      const row = page.locator('tr', { hasText: TEST_EMAIL }).first()
      page.once('dialog', d => d.accept())
      const respP = page.waitForResponse(r => r.url().includes('users.set_user_enabled'), { timeout: 8000 })
      await row.locator('button:has-text("Tắt")').click()
      const resp = await respP
      await page.waitForTimeout(800)
      const body = (await resp.json()).message
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Cleanup user sau khi test
      await cleanup(page, BASE, TEST_EMAIL)
      return body.enabled === 0
        ? { ok: true, detail: 'disabled OK' }
        : { ok: false, detail: `still enabled=${body.enabled}` }
    },
  },
]
