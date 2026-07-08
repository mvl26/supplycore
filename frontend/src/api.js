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

// UX-001: ánh xạ raw exception → thông báo nghiệp vụ thân thiện + mã lỗi.
// Mọi lỗi không khớp sẽ giữ nguyên (để dev dễ debug), nhưng các lỗi điển hình
// (AttributeError, TimestampMismatch, MandatoryError, Permission…) được dịch
// sang câu tiếng Việt + error code SC-Exxx ngắn gọn cho người dùng cuối.
const ERROR_MAP = [
  { re: /['"]?\w+['"]?\s+object has no attribute ['"](lft|rgt|old_parent|parent_group|parent_warehouse)['"]/i,
    code: 'SC-E101',
    msg: 'Lỗi cấu trúc dữ liệu phân cấp. Vui lòng liên hệ quản trị viên để chạy lại migration.' },
  { re: /TimestampMismatchError|has been modified after you have opened it/i,
    code: 'SC-E102',
    msg: 'Bản ghi đã được người khác cập nhật. Vui lòng tải lại trang và thử lại.' },
  { re: /MandatoryError|Value missing for/i,
    code: 'SC-E103',
    msg: 'Thiếu trường bắt buộc. Vui lòng kiểm tra các ô có dấu * trên form.' },
  { re: /DuplicateEntryError|already exists|Duplicate entry/i,
    code: 'SC-E104',
    msg: 'Bản ghi đã tồn tại (mã hoặc khoá duy nhất bị trùng).' },
  { re: /LinkValidationError|Could not find/i,
    code: 'SC-E105',
    msg: 'Tham chiếu không hợp lệ — bản ghi liên kết không tồn tại.' },
  { re: /PermissionError|Not permitted|No permission|no permission/i,
    code: 'SC-E106',
    msg: 'Bạn không có quyền thực hiện thao tác này. Vui lòng liên hệ quản trị viên.' },
  { re: /ValidationError|Invalid|không hợp lệ/i,
    code: 'SC-E107',
    msg: null /* giữ message gốc nếu là ValidationError có message rõ ràng */ },
  { re: /CSRFTokenError|Invalid CSRF/i,
    code: 'SC-E108',
    msg: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.' },
  { re: /AttributeError|TypeError|KeyError|InternalServerError/i,
    code: 'SC-E999',
    msg: 'Đã xảy ra lỗi hệ thống. Vui lòng liên hệ quản trị viên.' },
]

export function friendlyError(rawMsg) {
  if (!rawMsg) return rawMsg
  const txt = String(rawMsg)
  for (const rule of ERROR_MAP) {
    if (rule.re.test(txt)) {
      // ValidationError không có msg cố định → giữ original (chỉ thêm prefix code nếu cần)
      if (!rule.msg) return txt
      // Log raw để dev debug ở console
      try { console.warn(`[${rule.code}] ${txt}`) } catch (e) {}
      return `${rule.msg} (Mã: ${rule.code})`
    }
  }
  return txt
}

function parseFrappeError(body) {
  if (!body) return null
  // _server_messages = nguồn đầy đủ nhất (frappe.throw / msgprint), ưu tiên.
  if (body._server_messages) {
    try {
      const arr = JSON.parse(body._server_messages)
      const msgs = arr.map(m => {
        const o = typeof m === 'string' ? JSON.parse(m) : m
        return (o && o.message != null) ? o.message : String(m)
      })
      const txt = msgs.join('\n').replace(/<[^>]+>/g, '').trim()
      if (txt) return friendlyError(txt)
    } catch (e) { /* fall through */ }
  }
  // exception: có thể là "module.path.XxxError: message" HOẶC message thuần.
  // Chỉ cắt prefix khi khớp đúng dạng class path — tránh nuốt mất message
  // không có dấu ':' (vd "Tick FEFO Override + ghi lý do") hoặc message
  // chứa dấu ':' của riêng nó.
  if (body.exception) {
    const ex = String(body.exception).trim()
    const m = ex.match(/^([\w.]+(?:Error|Exception)):\s*([\s\S]+)$/)
    const txt = (m ? m[2] : ex).trim()
    if (txt) return friendlyError(txt)
  }
  if (body._error_message) {
    return friendlyError(String(body._error_message).replace(/<[^>]+>/g, '').trim())
  }
  if (typeof body.message === 'string') return friendlyError(body.message)
  if (body.message?.message) return friendlyError(body.message.message)
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
// Dùng custom backend API để bypass Frappe v15 field whitelist
export async function getList(doctype, params = {}) {
  const payload = {
    doctype,
    fields: params.fields || ['name'],
    filters: params.filters || {},
    order_by: params.order_by || 'modified desc',
    limit: params.limit || 20,
    start: params.start || 0,
  }
  if (params.or_filters) payload.or_filters = params.or_filters
  return call('supplycore.api.frontend.list_docs', payload)
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
  return call('supplycore.api.frontend.count_docs', { doctype, filters })
}

export async function submitDoc(doctype, name) {
  // Dùng backend wrapper để tránh TimestampMismatchError
  return call('supplycore.api.frontend.submit_doc', { doctype, name })
}

export async function cancelDoc(doctype, name) {
  return call('supplycore.api.frontend.cancel_doc', { doctype, name })
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

// === Data I/O ===
export const dataIo = {
  listImportable: () => call('supplycore.api.data_io.list_importable'),
  getSchema: (doctype) => call('supplycore.api.data_io.get_doctype_schema', { doctype }),
  getTemplate: (doctype, opts = {}) => call('supplycore.api.data_io.get_template', {
    doctype,
    file_type: opts.file_type || 'csv',
    with_data: opts.with_data ? 1 : 0,
    limit: opts.limit || 100,
  }),
  exportData: (doctype, opts = {}) => call('supplycore.api.data_io.export_data', {
    doctype,
    fields: opts.fields ? JSON.stringify(opts.fields) : '',
    filters: opts.filters ? JSON.stringify(opts.filters) : '',
    file_type: opts.file_type || 'csv',
    limit: opts.limit || 10000,
    order_by: opts.order_by || 'modified desc',
  }),
  importData: (doctype, payload) => call('supplycore.api.data_io.import_data', {
    doctype,
    content_b64: payload.content_b64,
    file_type: payload.file_type || 'csv',
    update_existing: payload.update_existing ? 1 : 0,
    submit_after: payload.submit_after ? 1 : 0,
    dry_run: payload.dry_run === false ? 0 : 1,
    two_row_header: payload.two_row_header ? 1 : 0,
  }),
  // Inline list import/export — format 3-dòng (label / fieldname / data)
  getListColumns: (doctype) => call('supplycore.api.data_io.get_list_columns', { doctype }),
  exportList: (doctype, opts = {}) => call('supplycore.api.data_io.export_list', {
    doctype,
    columns: opts.columns ? JSON.stringify(opts.columns) : '',
    filters: opts.filters ? JSON.stringify(opts.filters) : '',
    file_type: opts.file_type || 'csv',
    limit: opts.limit || 10000,
    order_by: opts.order_by || 'modified desc',
  }),
  getListTemplate: (doctype, opts = {}) => call('supplycore.api.data_io.get_list_template', {
    doctype,
    columns: opts.columns ? JSON.stringify(opts.columns) : '',
    file_type: opts.file_type || 'csv',
    with_data: opts.with_data ? 1 : 0,
    limit: opts.limit || 50,
  }),
}

// === Phiếu cha-con — xuất/nhập Excel 2 sheet (engine chung, theo doctype) ===
// Hỗ trợ: Framework Contract, SC Material Request, SC Purchase Order,
//   SC Purchase Receipt, SC Transfer Request, SC Inventory Count Sheet.
export const voucherIo = {
  export: (doctype, opts = {}) => call('supplycore.api.voucher_io.export_voucher', {
    doctype,
    filters: opts.filters ? JSON.stringify(opts.filters) : '',
    order_by: opts.order_by || 'modified desc',
    limit: opts.limit || 10000,
  }),
  template: (doctype, opts = {}) => call('supplycore.api.voucher_io.voucher_template', {
    doctype,
    with_data: opts.with_data ? 1 : 0,
    limit: opts.limit || 50,
  }),
  import: (doctype, payload) => call('supplycore.api.voucher_io.import_voucher', {
    doctype,
    content_b64: payload.content_b64,
    dry_run: payload.dry_run === false ? 0 : 1,
    allow_create: payload.allow_create === false ? 0 : 1,
  }),
  // CR-02 — import/template ngay tại lưới trong form (parse, KHÔNG ghi DB)
  childTemplate: (doctype, opts = {}) => call('supplycore.api.voucher_io.child_template', {
    doctype, file_type: opts.file_type || 'xlsx',
  }),
  parseChild: (doctype, payload) => call('supplycore.api.voucher_io.parse_child_rows', {
    doctype, content_b64: payload.content_b64, file_type: payload.file_type || 'xlsx',
  }),
}

// Doctype hỗ trợ xuất/nhập phiếu cha-con (khớp voucher_io.CONFIGS).
export const VOUCHER_IO_DOCTYPES = [
  'Framework Contract', 'SC Material Request', 'SC Purchase Order',
  'SC Purchase Receipt', 'SC Transfer Request', 'SC Inventory Count Sheet',
]

// === Bản đồ kho — khuôn viên BV + sơ đồ bin ===
export const warehouseMap = {
  site: (targetWarehouse) => call('supplycore.api.warehouse_map.get_site_map',
    targetWarehouse ? { target_warehouse: targetWarehouse } : {}),
  warehouse: (warehouse, targetBin) => call('supplycore.api.warehouse_map.get_warehouse_map',
    { warehouse, ...(targetBin ? { target_bin: targetBin } : {}) }),
  route: (fromWarehouse, toWarehouse) => call('supplycore.api.warehouse_map.get_route',
    { from_warehouse: fromWarehouse, to_warehouse: toWarehouse }),
  listMapped: () => call('supplycore.api.warehouse_map.list_mapped_warehouses'),
}

// === Fetch upstream — pull data từ doc cha vào doc mới ===
export const fetchUpstream = {
  sourcesFor: (targetDoctype) =>
    call('supplycore.api.fetch_upstream.sources_for', { target_doctype: targetDoctype }),
  listCandidates: (sourceDoctype, targetDoctype, search = '', limit = 20) =>
    call('supplycore.api.fetch_upstream.list_candidates', {
      source_doctype: sourceDoctype, target_doctype: targetDoctype, search, limit,
    }),
  fetch: (sourceDoctype, sourceName, targetDoctype) =>
    call('supplycore.api.fetch_upstream.fetch', {
      source_doctype: sourceDoctype, source_name: sourceName, target_doctype: targetDoctype,
    }),
}

// === User management ===
export const users = {
  listRoles: () => call('supplycore.api.users.list_roles'),
  list: (search = '', limit = 100, onlySC = 1) =>
    call('supplycore.api.users.list_users', { search, limit, only_supplycore: onlySC }),
  get: (name) => call('supplycore.api.users.get_user', { name }),
  create: (payload) => call('supplycore.api.users.create_user', {
    email: payload.email,
    full_name: payload.full_name,
    roles: JSON.stringify(payload.roles || []),
    password: payload.password || '',
    send_welcome: payload.send_welcome ? 1 : 0,
    user_type: payload.user_type || 'System User',
  }),
  updateRoles: (name, roles) =>
    call('supplycore.api.users.update_user_roles', { name, roles: JSON.stringify(roles || []) }),
  setEnabled: (name, enabled) =>
    call('supplycore.api.users.set_user_enabled', { name, enabled: enabled ? 1 : 0 }),
  resetPassword: (name) =>
    call('supplycore.api.users.reset_password', { name }),
}

// Trigger browser download từ {filename, content_b64, content_type}
export function downloadFile({ filename, content_b64, content_type }) {
  const bin = atob(content_b64)
  const len = bin.length
  const buf = new Uint8Array(len)
  for (let i = 0; i < len; i++) buf[i] = bin.charCodeAt(i)
  const blob = new Blob([buf], { type: content_type || 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

// Đọc file local → base64 (bỏ data:..;base64, prefix)
export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => {
      const s = String(r.result || '')
      const idx = s.indexOf('base64,')
      resolve(idx >= 0 ? s.slice(idx + 7) : s)
    }
    r.onerror = () => reject(r.error)
    r.readAsDataURL(file)
  })
}
