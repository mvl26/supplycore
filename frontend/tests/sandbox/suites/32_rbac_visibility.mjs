// Suite 32: RBAC visibility — "không có phận sự thì không thấy"
//
// Setup: tạo user
//   - rbac-store-{run}: chỉ "SupplyCore Storekeeper" → M3+M4+M5+M6+M9 + Putaway
// User: login → check sidebar + thử vào /m1 → 403 → thử /users → 403 → logout
// Cleanup user sau test.

import { randomBytes } from 'crypto'

const RUN_ID = Date.now().toString(36) + randomBytes(2).toString('hex')

const STORE_EMAIL = `rbac-store-${RUN_ID}@local.test`
const TEST_PWD = `Test-${RUN_ID}`

const BASE_URL = process.env.SC_BASE || 'http://supplycore'
const ADMIN_USER = process.env.SC_USER || 'Administrator'
const ADMIN_PWD = process.env.SC_PWD || 'admin'

async function frappeCall(page, method, args = {}) {
  return page.evaluate(async ({ m, a }) => {
    const fd = new FormData()
    for (const [k, v] of Object.entries(a)) fd.append(k, v)
    const r = await fetch(`/api/method/${m}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-Frappe-CSRF-Token': window.sc_csrf || '' },
      body: fd,
    })
    return { ok: r.ok, status: r.status, body: await r.text() }
  }, { m: method, a: args })
}

async function loginAs(page, user, pwd) {
  // Logout trước (nếu đang login)
  try {
    await page.goto(`${BASE_URL}/supplycore/`)
    await page.waitForTimeout(400)
    // Click avatar → logout
    const avatar = page.locator('header button').filter({ has: page.locator('div.rounded-full') }).first()
    if (await avatar.count() > 0) {
      await avatar.click().catch(() => null)
      await page.waitForTimeout(200)
      const lo = page.locator('button:has-text("Đăng xuất")')
      if (await lo.count() > 0) {
        await lo.click()
        await page.waitForTimeout(700)
      }
    }
  } catch (e) {}
  // Login
  await page.goto(`${BASE_URL}/supplycore/login`)
  await page.waitForTimeout(500)
  await page.fill('input[type=text]', user)
  await page.fill('input[type=password]', pwd)
  await Promise.all([
    page.waitForURL(u => !u.toString().includes('/login'), { timeout: 8000 }).catch(() => null),
    page.click('button[type=submit]'),
  ])
  await page.waitForTimeout(800)
}

export const tests = [
  {
    name: 'Setup: tạo user Storekeeper',
    run: async ({ page, BASE, OUT, name }) => {
      const r = await frappeCall(page, 'supplycore.api.users.create_user', {
        email: STORE_EMAIL, full_name: 'RBAC SupplyCore Storekeeper',
        roles: JSON.stringify(['SupplyCore Storekeeper']),
        password: TEST_PWD, send_welcome: 0,
      })
      if (!r.ok) return { ok: false, detail: `setup ${STORE_EMAIL} fail: ${r.status} ${r.body.slice(0, 200)}` }
      return { ok: true, detail: `created ${STORE_EMAIL}` }
    },
  },
  {
    name: 'Storekeeper: sidebar thấy M3+M4+M6+M9 + Putaway, không thấy M1/M8',
    run: async ({ page, BASE, OUT, name }) => {
      await loginAs(page, STORE_EMAIL, TEST_PWD)
      await page.goto(`${BASE}/supplycore/dashboard`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const hasMod = async (mid) => (await page.locator(`aside a[href$="/${mid}"]`).count()) > 0
      const hasFeat = async (path) => (await page.locator(`aside a[href$="${path}"]`).count()) > 0
      const seeM3 = await hasMod('m3')
      const seeM4 = await hasMod('m4')
      const seeM6 = await hasMod('m6')
      const seeM9 = await hasMod('m9')
      const seePutaway = await hasFeat('/putaway')
      const seeM1 = await hasMod('m1')
      const seeM8 = await hasMod('m8')
      const seeUsers = await hasFeat('/users')
      const ok = seeM3 && seeM4 && seeM6 && seeM9 && seePutaway
                  && !seeM1 && !seeM8 && !seeUsers
      return ok
        ? { ok: true, detail: 'visibility chuẩn cho Storekeeper' }
        : { ok: false, detail: `M3=${seeM3} M4=${seeM4} M6=${seeM6} M9=${seeM9} Put=${seePutaway} | M1=${seeM1} M8=${seeM8} Users=${seeUsers}` }
    },
  },
  {
    name: 'Storekeeper: vào /m1 → 403 Forbidden',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/m1`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const url = page.url()
      const banner = await page.locator('text=403').count()
      const reason = await page.locator('text=phạm vi quyền').count()
      return (url.includes('/403') || url.includes('forbidden')) && banner >= 1 && reason >= 1
        ? { ok: true, detail: `redirected to ${url.split('/').slice(-2).join('/')}` }
        : { ok: false, detail: `url=${url} banner=${banner} reason=${reason}` }
    },
  },
  {
    name: 'Storekeeper: vào /users → 403 Forbidden',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/users`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const url = page.url()
      const banner = await page.locator('text=403').count()
      return url.includes('/403') && banner >= 1
        ? { ok: true, detail: '403 page shown' }
        : { ok: false, detail: `url=${url} banner=${banner}` }
    },
  },
  {
    name: 'Cleanup: login lại Administrator + xoá user test',
    run: async ({ page, BASE, OUT, name }) => {
      await loginAs(page, ADMIN_USER, ADMIN_PWD)
      const r = await frappeCall(page, 'frappe.client.delete', { doctype: 'User', name: STORE_EMAIL })
      return r.ok
        ? { ok: true, detail: '1/1 user cleaned' }
        : { ok: false, detail: 'cleanup failed' }
    },
  },
]
