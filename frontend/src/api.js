// Frappe REST API client
const getCsrf = () => {
  const meta = document.querySelector('meta[name="csrf-token"]')
  return (meta && meta.content && meta.content !== '{{ csrf_token }}') ? meta.content : null
}

async function request(path, options = {}) {
  const headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-Frappe-CSRF-Token': getCsrf() || '',
    ...(options.headers || {}),
  }
  const res = await fetch(path, {
    credentials: 'include',
    ...options,
    headers,
  })
  if (!res.ok) {
    let detail = ''
    try { detail = (await res.json())._server_messages || '' } catch (e) {}
    throw new Error(`${res.status} ${res.statusText} ${detail}`)
  }
  return res.json()
}

// Whitelisted method
export async function call(method, args = {}) {
  const data = await request(`/api/method/${method}`, {
    method: 'POST',
    body: JSON.stringify(args),
  })
  return data.message
}

// REST: list documents
export async function getList(doctype, params = {}) {
  const usp = new URLSearchParams()
  if (params.fields) usp.set('fields', JSON.stringify(params.fields))
  if (params.filters) usp.set('filters', JSON.stringify(params.filters))
  if (params.order_by) usp.set('order_by', params.order_by)
  if (params.limit) usp.set('limit_page_length', String(params.limit))
  if (params.start) usp.set('limit_start', String(params.start))
  const data = await request(`/api/resource/${encodeURIComponent(doctype)}?${usp.toString()}`)
  return data.data || []
}

// REST: get document
export async function getDoc(doctype, name) {
  const data = await request(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`)
  return data.data
}

// REST: count
export async function count(doctype, filters = {}) {
  return call('frappe.client.get_count', {
    doctype, filters,
  })
}

// Current user
export async function getCurrentUser() {
  try {
    const data = await request('/api/method/frappe.auth.get_logged_user')
    return data.message
  } catch (e) {
    return 'Guest'
  }
}
