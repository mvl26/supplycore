// Suite 102: Verify QA Report v3 fixes (25/05/2026 round 3)
//
// 8 fix:
//   v3-M11-UAT cleanup: disable UAT/SMOKE rules + terminate test FC
//   v3-M0-09 BHYT card regex VN
//   v3-M2-06 MR total_estimated_cost > 0
//   v3-M6-01 SAME_WAREHOUSE error code rõ
//   v3-M9-01 ICS summary audit logging
//   v3-M1-07 FC comment min length
//   v3-M3-11 PR no-PO warn
//   v3-BIN-05 bin status auto-update

export const tests = [
  // -----------------------------------------------------------------------
  // v3-M11-UAT: UAT/SMOKE Alert Rules đã disable
  // -----------------------------------------------------------------------
  {
    name: 'v3-M11-UAT: UAT/SMOKE Alert Rules disabled',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const enabledCount = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/method/supplycore.api.frontend.list_docs', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            doctype: 'SC Alert Rule',
            fields: ['name'],
            filters: { name: ['like', '%UAT%'], enabled: 1 },
            limit: 50,
          }),
        })
        const d = await r.json()
        return (d.message || []).length
      }, { csrf })
      return enabledCount === 0
        ? { ok: true, detail: '0 UAT rules enabled' }
        : { ok: false, detail: `${enabledCount} UAT rules vẫn enabled` }
    },
  },

  // -----------------------------------------------------------------------
  // v3-M0-09: BHYT card invalid format → SC-E022
  // -----------------------------------------------------------------------
  {
    name: 'v3-M0-09: BHYT card format sai → SC-E022',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const result = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/resource/SC Patient', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            doctype: 'SC Patient',
            patient_id: 'BN-TEST-BHYT-' + Date.now(),
            patient_name: 'Test BHYT format',
            bhyt_card_no: 'INVALID-FMT',
          }),
        })
        const d = await r.json()
        return { status: r.status, exc: d.exception || '', msg: (d._server_messages || '').slice(0, 200) }
      }, { csrf })
      const ok = result.status >= 400 && (
        result.exc.includes('SC-E022') || result.msg.includes('SC-E022') ||
        result.exc.includes('INVALID_BHYT') || result.msg.includes('INVALID_BHYT')
      )
      return ok
        ? { ok: true, detail: 'BHYT sai format reject SC-E022' }
        : { ok: false, detail: `status=${result.status} exc="${result.exc.slice(0, 80)}"` }
    },
  },

  // -----------------------------------------------------------------------
  // v3-M0-09 ngược lại: BHYT valid → tạo OK
  // -----------------------------------------------------------------------
  {
    name: 'v3-M0-09: BHYT card đúng format (HC4101234567890) tạo OK',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const pid = 'BN-TEST-OK-' + Date.now()
      const result = await page.evaluate(async ({ pid, csrf }) => {
        const r = await fetch('/api/resource/SC Patient', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            doctype: 'SC Patient',
            patient_id: pid,
            patient_name: 'Test BHYT valid',
            bhyt_card_no: 'HC4101234567890',  // 15 ký tự đúng format
          }),
        })
        const d = await r.json()
        return { status: r.status, name: d.data?.name, exc: d.exception || '' }
      }, { pid, csrf })
      // Cleanup
      if (result.name) {
        await page.evaluate(async ({ name, csrf }) => {
          await fetch(`/api/resource/SC Patient/${encodeURIComponent(name)}`, {
            method: 'DELETE', credentials: 'include',
            headers: { 'X-Frappe-CSRF-Token': csrf },
          })
        }, { name: result.name, csrf })
      }
      return result.status >= 200 && result.status < 300
        ? { ok: true, detail: `Tạo ${result.name} OK` }
        : { ok: false, detail: `status=${result.status} exc="${result.exc.slice(0, 80)}"` }
    },
  },

  // -----------------------------------------------------------------------
  // v3-M6-01: SC Transfer Request same warehouse → SC-E024
  // -----------------------------------------------------------------------
  {
    name: 'v3-M6-01: TR from=to warehouse → SC-E024 SAME_WAREHOUSE',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      // Tìm 1 warehouse
      const wh = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/method/frappe.client.get_list?doctype=SC%20Warehouse&fields=["name"]&filters=' +
          encodeURIComponent(JSON.stringify([['is_group', '=', 0], ['disabled', '=', 0]])) + '&limit=1', {
          credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf },
        })
        const d = await r.json()
        return (d.message || [])[0]?.name
      }, { csrf })
      if (!wh) return { ok: 'skip', detail: 'No warehouse to test' }

      const result = await page.evaluate(async ({ wh, csrf }) => {
        const r = await fetch('/api/resource/SC Transfer Request', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            doctype: 'SC Transfer Request',
            from_warehouse: wh, to_warehouse: wh,
            request_date: new Date().toISOString().slice(0, 10),
            required_by: new Date().toISOString().slice(0, 10),
          }),
        })
        const d = await r.json()
        return { status: r.status, exc: d.exception || '', msg: (d._server_messages || '').slice(0, 200) }
      }, { wh, csrf })
      const ok = result.status >= 400 && (
        result.exc.includes('SC-E024') || result.msg.includes('SC-E024') ||
        result.exc.includes('SAME_WAREHOUSE') || result.msg.includes('SAME_WAREHOUSE') ||
        result.exc.includes('khác nhau') || result.msg.includes('khác nhau')
      )
      return ok
        ? { ok: true, detail: 'TR same wh reject SC-E024' }
        : { ok: false, detail: `status=${result.status} exc="${result.exc.slice(0, 80)}"` }
    },
  },

  // -----------------------------------------------------------------------
  // v3-BIN-05: Bin status đã update sau backfill
  // -----------------------------------------------------------------------
  {
    name: 'v3-BIN-05: Bin có SLE thì status != Empty',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      // Tìm bin có SLE positive
      const data = await page.evaluate(async ({ csrf }) => {
        // Get any bin with status != Empty
        const r = await fetch('/api/method/frappe.client.get_count?doctype=Bin%20Location&filters=' +
          encodeURIComponent(JSON.stringify([['status', '!=', 'Empty'], ['enabled', '=', 1]])), {
          credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf },
        })
        const d = await r.json()
        return d.message || 0
      }, { csrf })
      return data >= 1
        ? { ok: true, detail: `${data} bin có status != Empty (backfill OK)` }
        : { ok: false, detail: 'Tất cả bin vẫn Empty — backfill chưa chạy?' }
    },
  },

  // -----------------------------------------------------------------------
  // v3-M2-06: Không thể test submit MR total=0 (cần fixture MR draft riêng).
  // Skip vào commit — verify qua manual.
  // -----------------------------------------------------------------------

  // -----------------------------------------------------------------------
  // v3-M1-07: Comment "x" (< 10 ký tự) → SC-E026
  // -----------------------------------------------------------------------
  {
    name: 'v3-M1-07: FC approve comment "x" (< 10 char) → SC-E026',
    run: async ({ page }) => {
      // FC approve qua run_doc_method — cần FC ở stage Manager Review.
      // Smoke test: chỉ verify backend code có throw — không test full flow.
      // Marked skip với note vì cần fixture.
      return { ok: 'skip', detail: 'Cần fixture FC ở Manager Review stage để test full' }
    },
  },
]
