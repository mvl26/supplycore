// Suite 104: Persona RBAC sandbox
//
// Mục đích: với từng persona (4 personas còn lại trong personas.js +
// ROLE_TO_PERSONA — GĐ1 đã bỏ "mai"/"quynh" vì role nguồn bị xoá), dựng 1
// user sandbox idempotent, login, kiểm chức năng tiêu biểu của role:
//   - Login đúng → get_logged_user trả email user.
//   - list_docs trên doctype thuộc quyền đọc → status 200.
//   - list_docs trên doctype ngoài quyền → status 403 + PermissionError.
//
// Bootstrap chạy dưới session Administrator (runner đã login admin).
// Mỗi persona test logout → login user mới → assert → giữ session.
//
// User sandbox không bị xoá cuối run — tái sử dụng giữa các lần chạy
// (sandbox environment). Password fix: `Sandbox2026!` cho cả 4 user.

const PWD_SANDBOX = 'Sandbox2026!'

// Persona matrix — email + role + allowed/forbidden doctype để smoke perm.
// admin: skip forbidden (Sys Manager full access).
// lan: skip forbidden (Manager wide access). Allowed = SC Purchase Order.
// tam: Storekeeper — đọc PR/SE/MR, không đọc Payment Entry.
// phong: Accountant — đọc PI/PE/GL, không đọc Purchase Receipt.
const PERSONAS = [
  { id: 'admin', email: 'sandbox.admin@sc.test', full: 'Sandbox Admin',
    role: 'System Manager',
    allowed: 'User', forbidden: null },
  { id: 'lan',   email: 'sandbox.lan@sc.test',   full: 'Sandbox Manager Lan',
    role: 'SupplyCore Manager',
    allowed: 'SC Purchase Order', forbidden: null },
  { id: 'tam',   email: 'sandbox.tam@sc.test',   full: 'Sandbox Storekeeper Tam',
    role: 'SupplyCore Storekeeper',
    allowed: 'SC Purchase Receipt', forbidden: 'SC Payment Entry' },
  { id: 'phong', email: 'sandbox.phong@sc.test', full: 'Sandbox Accountant Phong',
    role: 'SupplyCore Accountant',
    allowed: 'SC Purchase Invoice', forbidden: 'SC Stock Entry' },
]

// ===== Helpers =====
async function adminCreateOrUpdateUser(page, { email, full, role }) {
  const csrf = await page.evaluate(() => window.sc_csrf)
  return page.evaluate(async ({ email, full, role, pwd, csrf }) => {
    const headers = { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf }
    const exists = await fetch(`/api/method/frappe.client.get_count?doctype=User&filters=${encodeURIComponent(JSON.stringify([['email','=',email]]))}`,
      { credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf } })
    const existsJson = await exists.json()
    const count = existsJson.message || 0

    if (count === 0) {
      const r = await fetch('/api/resource/User', {
        method: 'POST', credentials: 'include', headers,
        body: JSON.stringify({
          doctype: 'User', email, first_name: full, full_name: full,
          send_welcome_email: 0, enabled: 1, new_password: pwd,
          user_type: 'System User', language: 'vi',
          roles: [{ role }],
        }),
      })
      const d = await r.json()
      if (!r.ok) return { ok: false, action: 'create', detail: d.exception || `HTTP ${r.status}` }
    } else {
      // Update password + ensure role assigned + ensure enabled
      const rp = await fetch('/api/method/frappe.client.set_value', {
        method: 'POST', credentials: 'include', headers,
        body: JSON.stringify({
          doctype: 'User', name: email,
          fieldname: { enabled: 1, full_name: full, language: 'vi' },
        }),
      })
      await rp.json().catch(() => null)
      // Force password reset via update_password
      await fetch('/api/method/frappe.core.doctype.user.user.update_password', {
        method: 'POST', credentials: 'include', headers,
        body: JSON.stringify({ new_password: pwd, key: '', old_password: '', logout_all_sessions: 0 }),
      }).catch(() => null)
      // Direct password write via custom endpoint — fallback: re-save user with new_password
      await fetch(`/api/resource/User/${encodeURIComponent(email)}`, {
        method: 'PUT', credentials: 'include', headers,
        body: JSON.stringify({ new_password: pwd, enabled: 1 }),
      }).catch(() => null)
      // Ensure role
      const userDoc = await (await fetch(`/api/resource/User/${encodeURIComponent(email)}`,
        { credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf } })).json()
      const hasRole = (userDoc.data?.roles || []).some(r => r.role === role)
      if (!hasRole) {
        const roles = [...(userDoc.data?.roles || []), { role }]
        await fetch(`/api/resource/User/${encodeURIComponent(email)}`, {
          method: 'PUT', credentials: 'include', headers,
          body: JSON.stringify({ roles }),
        }).catch(() => null)
      }
    }
    return { ok: true, action: count === 0 ? 'created' : 'updated' }
  }, { email, full, role, pwd: PWD_SANDBOX, csrf })
}

async function logoutAndLogin(page, BASE, email, pwd) {
  // Force a fresh login flow by navigating to /login
  await page.goto(`${BASE}/api/method/logout`).catch(() => null)
  await page.goto(`${BASE}/supplycore/login`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(400)
  await page.fill('input[type=text]', email)
  await page.fill('input[type=password]', pwd)
  await Promise.all([
    page.waitForURL((u) => !u.toString().includes('/login'), { timeout: 10000 }).catch(() => null),
    page.click('button[type=submit]'),
  ])
  await page.waitForTimeout(800)
}

async function whoAmI(page) {
  return page.evaluate(async () => {
    const r = await fetch('/api/method/frappe.auth.get_logged_user', { credentials: 'include' })
    const d = await r.json()
    return d.message || ''
  })
}

async function tryListDocs(page, doctype) {
  const csrf = await page.evaluate(() => window.sc_csrf)
  return page.evaluate(async ({ doctype, csrf }) => {
    const r = await fetch('/api/method/supplycore.api.frontend.list_docs', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify({ doctype, fields: ['name'], limit: 1 }),
    })
    const d = await r.json()
    return { status: r.status, exc: d.exception || '', count: Array.isArray(d.message) ? d.message.length : 0 }
  }, { doctype, csrf })
}

// ===== Tests =====
export const tests = [
  // ---------------------------------------------------------------------
  // Bootstrap: tạo / refresh 4 user sandbox (chạy với session Admin)
  // ---------------------------------------------------------------------
  {
    name: 'Bootstrap 4 sandbox users (idempotent)',
    run: async ({ page }) => {
      const results = []
      for (const p of PERSONAS) {
        const r = await adminCreateOrUpdateUser(page, p)
        results.push(`${p.id}:${r.ok ? r.action : 'FAIL'}`)
        if (!r.ok) {
          return { ok: false, detail: `${p.id} ${r.action}: ${r.detail?.slice(0, 80)}` }
        }
      }
      return { ok: true, detail: results.join(' ') }
    },
  },

  // ---------------------------------------------------------------------
  // Persona tests: logout admin → login persona → assert quyền truy cập
  // ---------------------------------------------------------------------
  ...PERSONAS.map(p => ({
    name: `Persona ${p.id} (${p.role}): login + allowed=${p.allowed}${p.forbidden ? ` + forbidden=${p.forbidden}` : ''}`,
    run: async ({ page, BASE }) => {
      await logoutAndLogin(page, BASE, p.email, PWD_SANDBOX)
      const me = await whoAmI(page)
      if (me !== p.email) {
        return { ok: false, detail: `Login fail: get_logged_user=${me || '(guest)'}` }
      }
      // Allowed
      const okCall = await tryListDocs(page, p.allowed)
      if (okCall.status >= 400) {
        return { ok: false, detail: `Allowed ${p.allowed} bị reject status=${okCall.status} exc="${okCall.exc.slice(0, 80)}"` }
      }
      // Forbidden
      if (p.forbidden) {
        const noCall = await tryListDocs(page, p.forbidden)
        const isReject = noCall.status >= 400 &&
          (noCall.exc.includes('PermissionError') || noCall.exc.includes('Không có quyền'))
        if (!isReject) {
          return { ok: false, detail: `Forbidden ${p.forbidden} không bị reject (status=${noCall.status})` }
        }
        return { ok: true, detail: `me=${me} ${p.allowed}=OK ${p.forbidden}=403` }
      }
      return { ok: true, detail: `me=${me} ${p.allowed}=OK (admin/manager — no forbidden check)` }
    },
  })),
]
