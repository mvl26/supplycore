// Suite 101: Verify QA Report v2 fixes (25/05/2026)
//
// 8 fix:
//   BUG-M2-02 sendmail delayed=True (perf — không test trực tiếp, smoke)
//   BUG-M1-02 FC remaining=0 → Exhausted
//   BUG-M5-02/03 block "/" trong batch_id
//   BUG-M9-01 ICS summary read-only
//   BUG-M0-02 MST regex VN
//   BUG-M3-01 qc_status field-aware label
//   BUG-M11-01/M5-01/M7-02 cleanup test data

export const tests = [
  // BUG-M11-01: 0 test alert
  {
    name: 'BUG-M11-01: Không còn [TEST] alert trong production',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const count = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/method/frappe.client.get_count?doctype=SC%20Alert&filters=' +
          encodeURIComponent(JSON.stringify([['title', 'like', '%TEST%']])), {
          credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf },
        })
        const d = await r.json()
        return d.message || 0
      }, { csrf })
      return count === 0
        ? { ok: true, detail: '0 [TEST] alert (cleanup OK)' }
        : { ok: false, detail: `${count} [TEST] alert còn` }
    },
  },

  // BUG-M5-01: Không còn batch test
  {
    name: 'BUG-M5-01: Test batch (asdasd / TEST-BC-*) đã disable',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const count = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/method/frappe.client.get_count?doctype=SC%20Batch&filters=' +
          encodeURIComponent(JSON.stringify([
            ['batch_id', 'like', 'asd%'], ['disabled', '=', 0]
          ])), {
          credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf },
        })
        const d = await r.json()
        return d.message || 0
      }, { csrf })
      return count === 0
        ? { ok: true, detail: '0 batch test active' }
        : { ok: false, detail: `${count} batch test còn active` }
    },
  },

  // BUG-M5-02: Không còn batch_id có '/'
  {
    name: 'BUG-M5-02: Batch_id "/" đã rename',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const count = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/method/frappe.client.get_count?doctype=SC%20Batch&filters=' +
          encodeURIComponent(JSON.stringify([['batch_id', 'like', '%/%']])), {
          credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf },
        })
        const d = await r.json()
        return d.message || 0
      }, { csrf })
      return count === 0
        ? { ok: true, detail: '0 batch có "/" trong batch_id' }
        : { ok: false, detail: `${count} batch còn '/'` }
    },
  },

  // BUG-M5-02/03: Block tạo batch với '/' trong batch_id
  {
    name: 'BUG-M5-02 validator: Tạo batch_id chứa "/" → SC-E020',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const result = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/resource/SC Batch', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            doctype: 'SC Batch',
            batch_id: 'test/with/slash',
            item: 'DTRC-GLU5',
            expiry_date: '2027-12-31',
          }),
        })
        const d = await r.json()
        return { status: r.status, exc: d.exception || '', msg: (d._server_messages || '').slice(0, 200) }
      }, { csrf })
      const ok = result.status >= 400 && (
        result.exc.includes('SC-E020') || result.msg.includes('SC-E020') ||
        result.exc.includes('INVALID_CHAR') || result.msg.includes('INVALID_CHAR')
      )
      return ok
        ? { ok: true, detail: 'Reject batch_id "/" với SC-E020' }
        : { ok: false, detail: `status=${result.status} exc="${result.exc.slice(0, 60)}"` }
    },
  },

  // BUG-M1-02: FC có Exhausted status
  {
    name: 'BUG-M1-02: FC remaining<=0 chuyển Exhausted',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const counts = await page.evaluate(async ({ csrf }) => {
        const r1 = await fetch('/api/method/frappe.client.get_count?doctype=Framework%20Contract&filters=' +
          encodeURIComponent(JSON.stringify([['status', '=', 'Exhausted']])), {
          credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf },
        })
        const r2 = await fetch('/api/method/frappe.client.get_count?doctype=Framework%20Contract&filters=' +
          encodeURIComponent(JSON.stringify([['status', '=', 'Active'], ['remaining_value', '<=', 0]])), {
          credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf },
        })
        return { exhausted: (await r1.json()).message || 0, bad: (await r2.json()).message || 0 }
      }, { csrf })
      return (counts.exhausted >= 1 && counts.bad === 0)
        ? { ok: true, detail: `Exhausted=${counts.exhausted}, Active+remain<=0=${counts.bad}` }
        : { ok: false, detail: `Exhausted=${counts.exhausted}, lỗi=${counts.bad}` }
    },
  },

  // BUG-M0-02: MST format invalid → reject
  {
    name: 'BUG-M0-02: MST 8 chữ số → SC-E021 INVALID_TAX_ID',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const result = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/resource/SC Supplier', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            doctype: 'SC Supplier',
            supplier_name: 'Test NCC MST sai ' + Date.now(),
            tax_id: '12345678',  // 8 digits — invalid
            supplier_type: 'Nhà phân phối',
            email_id: 't@x.com', mobile_no: '0901234567',
            address: '1 Test', province: 'Hà Nội',
          }),
        })
        const d = await r.json()
        return { status: r.status, exc: d.exception || '', msg: (d._server_messages || '').slice(0, 200) }
      }, { csrf })
      const ok = result.status >= 400 && (
        result.exc.includes('SC-E021') || result.msg.includes('SC-E021') ||
        result.exc.includes('INVALID_TAX_ID') || result.msg.includes('INVALID_TAX_ID')
      )
      return ok
        ? { ok: true, detail: 'Reject MST 8 số với SC-E021' }
        : { ok: false, detail: `status=${result.status} exc="${result.exc.slice(0, 60)}"` }
    },
  },

  // BUG-M3-01: qc_status badge dùng label "Chờ QC" thay vì "Chờ duyệt"
  {
    name: 'BUG-M3-01: qc_status="Pending" hiển thị "Chờ QC" không phải "Chờ duyệt"',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/list/SC%20Purchase%20Receipt`)
      await page.waitForTimeout(2000)
      // Tìm row có qc_status Pending → kiểm tra text badge
      const labels = await page.evaluate(() => {
        const cells = Array.from(document.querySelectorAll('table tbody tr td'))
        return cells.map(c => c.textContent.trim()).filter(t => /Chờ QC|Chờ duyệt/.test(t))
      })
      await page.screenshot({ path: `${OUT}/${name}.png` })
      const hasChoQC = labels.some(t => /Chờ QC/.test(t))
      // Có thể không có PR pending nào — skip
      if (labels.length === 0) return { ok: 'skip', detail: 'Không có PR có badge Chờ duyệt/Chờ QC để verify' }
      return hasChoQC
        ? { ok: true, detail: `Tìm thấy "Chờ QC" trên qc_status column` }
        : { ok: false, detail: `Badge vẫn dùng "Chờ duyệt": ${JSON.stringify(labels.slice(0, 3))}` }
    },
  },
]
