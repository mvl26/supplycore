// In nhãn (mã vạch + thông tin) — dùng chung cho in 1 nhãn (BarcodeDisplay) và
// in hàng loạt (danh sách Lô). Mỗi item: { value, title, subtitle?, lines?, format? }.
import JsBarcode from 'jsbarcode'

const escHtml = (s) => String(s ?? '').replace(/[&<>"]/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]))

function labelHtml(item) {
  const tmp = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  try {
    JsBarcode(tmp, String(item.value), {
      format: item.format || 'CODE128', height: 44, width: 1.6,
      displayValue: true, fontSize: 13, textMargin: 1, margin: 0,
    })
  } catch (e) {
    return ''
  }
  const svgStr = new XMLSerializer().serializeToString(tmp)
  const extra = (item.lines || []).filter(Boolean)
  const linesHtml = extra.length
    ? extra.map((l) => `<div class="ln info">${escHtml(l)}</div>`).join('')
    : (item.subtitle ? `<div class="ln exp">${escHtml(item.subtitle)}</div>` : '')
  return `<div class="label">
    <div class="bc">${svgStr}</div>
    ${item.title ? `<div class="ln name">${escHtml(item.title)}</div>` : ''}
    ${linesHtml}
  </div>`
}

// In 1 hoặc nhiều nhãn trong CÙNG 1 lần in (mỗi nhãn 1 trang → cuộn tem liên tục).
// Mỗi item có thể đặt `copies` = số nhãn cần in cho item đó (mặc định 1) — 1 lô
// dán nhiều tem thì tăng copies.
export function printLabels(items) {
  const src = (items || []).filter((it) => it && it.value)
  if (!src.length) return
  // Nhân bản theo copies (tối đa 200/tem để tránh in nhầm số quá lớn)
  const list = src.flatMap((it) => {
    const n = Math.min(200, Math.max(1, Math.floor(Number(it.copies) || 1)))
    return Array.from({ length: n }, () => it)
  })
  const anyLines = list.some((it) => (it.lines || []).filter(Boolean).length)
  const H = anyLines ? '40mm' : '30mm'   // có nhiều dòng info → nhãn cao hơn
  const body = list.map(labelHtml).join('')
  const win = window.open('', '_blank', 'width=480,height=520')
  if (!win) return
  win.document.write(`<!doctype html><html><head><title>In nhãn (${list.length})</title>
    <style>
      @page { size: 50mm ${H}; margin: 0; }
      * { box-sizing: border-box; }
      html, body { margin: 0; padding: 0; }
      .label { width: 50mm; height: ${H}; padding: 1.5mm 2mm; gap: 0.4mm;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        font-family: Arial, sans-serif; text-align: center; overflow: hidden;
        page-break-after: always; break-after: page; }
      .label:last-child { page-break-after: auto; break-after: auto; }
      .bc { width: 100%; line-height: 0; }
      .bc svg { width: 100%; height: auto; max-height: 15mm; }
      .ln { max-width: 46mm; }
      .name { font-size: 8pt; font-weight: 700; line-height: 1.1;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
      .exp  { font-size: 8pt; line-height: 1.1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .info { font-size: 7pt; line-height: 1.18; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    </style></head><body>
    ${body}
    <script>window.onload=function(){window.print();setTimeout(function(){window.close()},400)}<\/script>
    </body></html>`)
  win.document.close()
}

// Chuẩn hóa 1 bản ghi Lô (SC Batch) → item nhãn (bỏ trường trống).
export function batchLabelItem(b) {
  const lines = []
  if (b.supplier_batch_no) lines.push(`Lô NCC: ${b.supplier_batch_no}`)
  const dates = []
  if (b.manufacturing_date) dates.push(`NSX: ${b.manufacturing_date}`)
  if (b.expiry_date) dates.push(`HSD: ${b.expiry_date}`)
  if (dates.length) lines.push(dates.join(' · '))
  const mo = []
  if (b.model) mo.push(`Model: ${b.model}`)
  if (b.country_of_origin) mo.push(`Xuất xứ: ${b.country_of_origin}`)
  if (mo.length) lines.push(mo.join(' · '))
  return { value: b.barcode || b.batch_id, title: b.item_name || b.item || '', lines }
}
