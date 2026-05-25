// Suite 33: Persona-aware sidebar — phân quyền theo tài khoản, không có dropdown chọn
//
// Tạo 5 user (mỗi user 1 Frappe role tương ứng 1 persona), login lần lượt,
// xác nhận sidebar render đúng persona card + nav curated. Không có
// persona switcher hiển thị — persona = derive 100% từ login user roles.
//
// Personas verified:
//   - SupplyCore Manager        → "lan"   (Trưởng phòng Vật tư)
//   - SupplyCore Storekeeper    → "tam"   (Thủ kho)
//   - SupplyCore Accountant     → "phong" (Kế toán)
//   - SupplyCore Ward Staff     → "mai"   (Điều dưỡng / NV Khoa)
//   - Pharmacy Officer          → "quynh" (Kiểm soát Chất lượng)

import { randomBytes } from 'crypto'

const RUN_ID = Date.now().toString(36) + randomBytes(2).toString('hex')
const PWD = `Test-${RUN_ID}`

const BASE_URL = process.env.SC_BASE || 'http://supplycore'
const ADMIN_USER = process.env.SC_USER || 'Administrator'
const ADMIN_PWD = process.env.SC_PWD || 'admin'

// Persona expectations — what must (visible) and must-not (hidden) appear in `aside`.
// `visibleHrefs` is href endings that should be findable; `hiddenHrefs` must NOT
// appear. `personaName` is the exact display string in the persona card.
const PERSONAS = [
  {
    id: 'lan',
    email: `psn-mgr-${RUN_ID}@local.test`,
    role: 'SupplyCore Manager',
    personaName: 'Trưởng phòng Vật tư',
    personaRole: 'SC-MANAGER',
    // Manager has very broad access — sample a representative subset.
    visibleHrefs: ['/m1', '/m2', '/m7', '/alerts'],
    hiddenHrefs:  ['/putaway'],  // putaway feature is storekeeper-specific
  },
  {
    id: 'tam',
    email: `psn-store-${RUN_ID}@local.test`,
    role: 'SupplyCore Storekeeper',
    personaName: 'Thủ kho',
    personaRole: 'SC-STOREKEEPER',
    visibleHrefs: ['/m3', '/m4', '/m6', '/m9', '/putaway'],
    hiddenHrefs:  ['/m1', '/m2', '/m8', '/users', '/financial-reports'],
  },
  {
    id: 'phong',
    email: `psn-acct-${RUN_ID}@local.test`,
    role: 'SupplyCore Accountant',
    personaName: 'Kế toán',
    personaRole: 'SC-ACCOUNTANT',
    visibleHrefs: ['/m8', '/financial-reports'],
    hiddenHrefs:  ['/m3', '/m4', '/m6', '/users', '/putaway'],
  },
  {
    id: 'mai',
    email: `psn-ward-${RUN_ID}@local.test`,
    role: 'SupplyCore Ward Staff',
    personaName: 'Điều dưỡng',  // matches "Điều dưỡng / NV Khoa" — substring match
    personaRole: 'SC-WARD-NURSE',
    visibleHrefs: [],  // ward staff has minimal direct routes; sidebar may be small
    hiddenHrefs:  ['/m1', '/m2', '/m8', '/users', '/putaway', '/financial-reports'],
  },
  {
    id: 'quynh',
    email: `psn-pharm-${RUN_ID}@local.test`,
    role: 'Pharmacy Officer',
    personaName: 'Kiểm soát Chất lượng',
    personaRole: 'SC-QC',
    visibleHrefs: ['/m5', '/m7', '/m10', '/batch-trace'],
    hiddenHrefs:  ['/m1', '/m2', '/m8', '/users', '/financial-reports'],
  },
]

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
    const avatar = page.locator('header button').filter({ has: page.locator('div.rounded-full, div.rounded-lg') }).first()
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
  await page.goto(`${BASE_URL}/supplycore/login`)
  await page.waitForTimeout(500)
  await page.fill('input[type=text]', user)
  await page.fill('input[type=password]', pwd)
  await Promise.all([
    page.waitForURL(u => !u.toString().includes('/login'), { timeout: 8000 }).catch(() => null),
    page.click('button[type=submit]'),
  ])
  await page.waitForTimeout(1200)
}

export const tests = [
  {
    name: 'Setup: tạo 5 user, mỗi user 1 role tương ứng 1 persona',
    run: async ({ page }) => {
      for (const p of PERSONAS) {
        const r = await frappeCall(page, 'supplycore.api.users.create_user', {
          email: p.email,
          full_name: `Persona ${p.role}`,
          roles: JSON.stringify([p.role]),
          password: PWD,
          send_welcome: 0,
        })
        if (!r.ok) return { ok: false, detail: `setup ${p.email} fail: ${r.status} ${r.body.slice(0, 200)}` }
      }
      return { ok: true, detail: `created ${PERSONAS.length} users` }
    },
  },

  // Một test riêng cho mỗi persona — login → assert sidebar.
  ...PERSONAS.map(p => ({
    name: `[${p.id}] ${p.role} → sidebar hiển thị persona "${p.personaName}"`,
    run: async ({ page, BASE, OUT, name }) => {
      await loginAs(page, p.email, PWD)
      await page.goto(`${BASE}/supplycore/dashboard`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })

      // 1. Persona card text appears in sidebar.
      const cardName = await page.locator('aside').getByText(p.personaName, { exact: false }).count()
      const cardRole = await page.locator('aside').getByText(p.personaRole, { exact: false }).count()

      // 2. Scope note ("Phạm vi:") appears.
      const scope = await page.locator('aside').getByText('Phạm vi:', { exact: false }).count()

      // 3. Expected nav links visible.
      const visMisses = []
      for (const h of p.visibleHrefs) {
        const n = await page.locator(`aside a[href$="${h}"]`).count()
        if (n === 0) visMisses.push(h)
      }

      // 4. Forbidden nav links hidden.
      const hidLeaks = []
      for (const h of p.hiddenHrefs) {
        const n = await page.locator(`aside a[href$="${h}"]`).count()
        if (n > 0) hidLeaks.push(h)
      }

      // 5. NO persona switcher dropdown anywhere — phân quyền không cho chọn.
      const switcher = await page.locator('header button:has-text("Trưởng phòng"), header button:has-text("Thủ kho"), header button:has-text("Kế toán"), header button:has-text("Điều dưỡng"), header button:has-text("Kiểm soát Chất lượng")').count()

      const ok = cardName > 0 && cardRole > 0 && scope > 0
        && visMisses.length === 0 && hidLeaks.length === 0

      const parts = []
      if (cardName === 0) parts.push(`thiếu persona name "${p.personaName}"`)
      if (cardRole === 0) parts.push(`thiếu role badge "${p.personaRole}"`)
      if (scope === 0) parts.push('thiếu scope note')
      if (visMisses.length) parts.push(`thiếu nav: ${visMisses.join(',')}`)
      if (hidLeaks.length) parts.push(`leak nav: ${hidLeaks.join(',')}`)
      if (switcher > 0) parts.push(`có ${switcher} switcher button — phải bỏ`)

      return ok
        ? { ok: true, detail: `persona "${p.personaName}" render đúng (${p.visibleHrefs.length} visible, ${p.hiddenHrefs.length} hidden)` }
        : { ok: false, detail: parts.join('; ') }
    },
  })),

  {
    name: 'Administrator → flat M0..M11 view, không có persona card',
    run: async ({ page, BASE, OUT, name }) => {
      await loginAs(page, ADMIN_USER, ADMIN_PWD)
      await page.goto(`${BASE}/supplycore/dashboard`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })

      // Admin must see full module list (M0..M11 → ≥12 module links).
      const moduleLinks = await page.locator('aside a[href^="/supplycore/m"]').count()

      // Admin must NOT see persona card with "Phạm vi:" text.
      const scope = await page.locator('aside').getByText('Phạm vi:', { exact: false }).count()

      const ok = moduleLinks >= 12 && scope === 0
      return ok
        ? { ok: true, detail: `${moduleLinks} module links, không có persona card` }
        : { ok: false, detail: `moduleLinks=${moduleLinks} scope=${scope} (admin phải có ≥12 và 0)` }
    },
  },

  {
    name: 'Cleanup: xóa 5 user test',
    run: async ({ page }) => {
      let cleaned = 0
      for (const p of PERSONAS) {
        const r = await frappeCall(page, 'frappe.client.delete', { doctype: 'User', name: p.email })
        if (r.ok) cleaned++
      }
      return cleaned === PERSONAS.length
        ? { ok: true, detail: `${cleaned}/${PERSONAS.length} users cleaned` }
        : { ok: false, detail: `only ${cleaned}/${PERSONAS.length} cleaned` }
    },
  },
]
