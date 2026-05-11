// Frappe REST API client — standalone SupplyCore

const getCsrf = () => {
  if (window.sc_csrf && window.sc_csrf !== '{{ csrf_token }}') return window.sc_csrf
  const meta = document.querySelector('meta[name="csrf-token"]')
  return (meta && meta.content && meta.content !== '{{ csrf_token }}') ? meta.content : null
}

let _csrf = getCsrf()
export const setCsrf = (v) => { _csrf = v; window.sc_csrf = v }

async function request(path, options = {}) {
  const isForm = options.body instanceof FormData
  const headers = {
    'Accept': 'application/json',
    'X-Frappe-CSRF-Token': _csrf || getCsrf() || '',
    ...(options.headers || {}),
  }
  if (!isForm) headers['Content-Type'] = 'application/json'
  const res = await fetch(path, {
    credentials: 'include',
    ...options,
    headers,
  })
  let body = null
  try { body = await res.json() } catch (e) { /* ignore */ }
  if (!res.ok) {
    const msg = parseFrappeError(body) || `HTTP ${res.status}`
    const err = new Error(msg)
    err.status = res.status
    err.body = body
    throw err
  }
  return body
}

function parseFrappeError(body) {
  if (!body) return null
  if (body.exception) return body.exception.split(':').slice(1).join(':').trim()
  if (body._server_messages) {
    try {
      const arr = JSON.parse(body._server_messages)
      const msgs = arr.map(m => typeof m === 'string' ? JSON.parse(m).message : m.message)
      return msgs.join('; ').replace(/<[^>]+>/g, '')
    } catch (e) {}
  }
  if (body.message?.message) return body.message.message
  return null
}

// === Auth ===
export async function login(usr, pwd) {
  const fd = new FormData()
  fd.append('usr', usr)
  fd.append('pwd', pwd)
  const data = await request('/api/method/login', { method: 'POST', body: fd })
  // Refresh CSRF
  const ses = await getSession()
  return { user: ses, raw: data }
}

export async function logout() {
  await request('/api/method/logout', { method: 'POST' })
  setCsrf(null)
}

export async function getSession() {
  try {
    const d = await request('/api/method/frappe.auth.get_logged_user')
    return d.message
  } catch (e) {
    return 'Guest'
  }
}

export async function getUserInfo(name) {
  try {
    const d = await request(`/api/resource/User/${encodeURIComponent(name)}?fields=${encodeURIComponent('["name","full_name","email","user_image","roles.role as role"]')}`)
    return d.data
  } catch (e) {
    return null
  }
}

// === Whitelisted methods ===
export async function call(method, args = {}) {
  const data = await request(`/api/method/${method}`, {
    method: 'POST',
    body: JSON.stringify(args),
  })
  return data.message
}

// === REST resources ===
export async function getList(doctype, params = {}) {
  const usp = new URLSearchParams()
  if (params.fields) usp.set('fields', JSON.stringify(params.fields))
  if (params.filters) usp.set('filters', JSON.stringify(params.filters))
  if (params.or_filters) usp.set('or_filters', JSON.stringify(params.or_filters))
  if (params.order_by) usp.set('order_by', params.order_by)
  if (params.limit) usp.set('limit_page_length', String(params.limit))
  if (params.start) usp.set('limit_start', String(params.start))
  const data = await request(`/api/resource/${encodeURIComponent(doctype)}?${usp.toString()}`)
  return data.data || []
}

export async function getDoc(doctype, name) {
  const data = await request(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`)
  return data.data
}

export async function createDoc(doctype, fields) {
  const data = await request(`/api/resource/${encodeURIComponent(doctype)}`, {
    method: 'POST', body: JSON.stringify(fields),
  })
  return data.data
}

export async function updateDoc(doctype, name, fields) {
  const data = await request(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`, {
    method: 'PUT', body: JSON.stringify(fields),
  })
  return data.data
}

export async function deleteDoc(doctype, name) {
  await request(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  })
}

export async function count(doctype, filters = {}) {
  return call('frappe.client.get_count', { doctype, filters })
}

export async function submitDoc(doctype, name) {
  return call('frappe.client.submit', { doc: { doctype, name } })
}

export async function cancelDoc(doctype, name) {
  return call('frappe.client.cancel', { doctype, name })
}

// Run a doctype instance method (whitelisted via @frappe.whitelist on doc class)
export async function runDocMethod(doctype, name, method, args = {}) {
  // Frappe v15: use /api/method/run_doc_method (mapped to frappe.handler.run_doc_method)
  const params = new URLSearchParams({
    method,
    dt: doctype,
    dn: name,
  })
  if (Object.keys(args).length) params.set('args', JSON.stringify(args))
  const res = await fetch(`/api/method/run_doc_method?${params.toString()}`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Accept': 'application/json',
      'X-Frappe-CSRF-Token': _csrf || getCsrf() || '',
    },
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = parseFrappeError(body) || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return body
}

// Get DocType meta (fields, options)
export async function getMeta(doctype) {
  return call('frappe.client.get_meta', { doctype }).catch(async () => {
    // Frappe doesn't have public get_meta - fallback to private
    const r = await request(`/api/method/frappe.desk.form.load.getdoctype?doctype=${encodeURIComponent(doctype)}`)
    return r.docs?.[0] || null
  })
}
