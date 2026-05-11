// Shared helpers cho UC test suites

export async function apiCall(page, method, args = {}) {
  return page.evaluate(async ({ method, args }) => {
    const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
    const r = await fetch(`/api/method/${method}`, {
      method: 'POST', credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Frappe-CSRF-Token': csrf,
      },
      body: JSON.stringify(args),
    })
    const data = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(data.exception || data._server_messages || `HTTP ${r.status}`)
    return data.message
  }, { method, args })
}

export async function apiGetList(page, doctype, params = {}) {
  return page.evaluate(async ({ doctype, params }) => {
    const usp = new URLSearchParams()
    if (params.fields) usp.set('fields', JSON.stringify(params.fields))
    if (params.filters) usp.set('filters', JSON.stringify(params.filters))
    if (params.order_by) usp.set('order_by', params.order_by)
    if (params.limit) usp.set('limit_page_length', String(params.limit))
    const url = `/api/resource/${encodeURIComponent(doctype)}?${usp.toString()}`
    const r = await fetch(url, { credentials: 'include', headers: { Accept: 'application/json' } })
    if (!r.ok) {
      const txt = await r.text().catch(() => '')
      throw new Error(`apiGetList ${doctype} HTTP ${r.status}: ${txt.slice(0, 200)}`)
    }
    const d = await r.json()
    return d.data || []
  }, { doctype, params })
}

export async function apiGetDoc(page, doctype, name) {
  return page.evaluate(async ({ doctype, name }) => {
    const r = await fetch(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`,
      { credentials: 'include' })
    const d = await r.json()
    return d.data
  }, { doctype, name })
}

export async function apiCount(page, doctype, filters = {}) {
  return apiCall(page, 'frappe.client.get_count', { doctype, filters })
}

export async function apiRunDocMethod(page, doctype, name, method, args = {}) {
  return page.evaluate(async ({ doctype, name, method, args }) => {
    const csrf = window.sc_csrf || ''
    const usp = new URLSearchParams({ method, dt: doctype, dn: name })
    if (Object.keys(args).length) usp.set('args', JSON.stringify(args))
    const r = await fetch(`/api/method/run_doc_method?${usp}`, {
      method: 'POST', credentials: 'include',
      headers: { 'X-Frappe-CSRF-Token': csrf, Accept: 'application/json' },
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.exception || `HTTP ${r.status}`)
    return d.message
  }, { doctype, name, method, args })
}

export async function navigateTo(page, BASE, path) {
  await page.goto(`${BASE}/supplycore${path}`)
  await page.waitForTimeout(800)
}

export async function fillForm(page, fields) {
  // fields = { 'label substring': 'value', ... }
  for (const [label, val] of Object.entries(fields)) {
    const input = page.locator(`label:has-text("${label}") + * input, label:has-text("${label}") ~ * input`).first()
    await input.fill(String(val)).catch(() => null)
  }
}

export async function clickButton(page, text) {
  await page.locator(`button:has-text("${text}")`).first().click()
  await page.waitForTimeout(800)
}

export async function pickFirst(page, doctype, filters = {}) {
  const rows = await apiGetList(page, doctype, { fields: ['name'], filters, limit: 1 })
  return rows[0]?.name || null
}

export async function pickByField(page, doctype, field, valueLike) {
  const rows = await apiGetList(page, doctype, {
    fields: ['name'],
    filters: [[field, 'like', `%${valueLike}%`]],
    limit: 1,
  })
  return rows[0]?.name || null
}

export async function readToast(page) {
  return page.locator('[class*="bg-red-50"], [class*="text-red"]').first().textContent().catch(() => null)
}

export function rand(n = 4) {
  return Math.random().toString(36).slice(2, 2 + n)
}
