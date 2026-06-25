// Util helpers

export const today = () => new Date().toISOString().slice(0, 10)

export const fmtVND = (v) => new Intl.NumberFormat('vi-VN', {
  style: 'currency', currency: 'VND', maximumFractionDigits: 0,
}).format(Number(v) || 0)

export const fmtNumber = (v) => new Intl.NumberFormat('vi-VN').format(Number(v) || 0)

export const fmtShort = (v) => {
  const n = Number(v) || 0
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(2) + ' tỷ'
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + ' tr'
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'k'
  return n.toLocaleString('vi-VN')
}

// T04: thống nhất dd/mm/yyyy (chuẩn VN, có số 0 đứng đầu). Parse thẳng chuỗi
// ISO yyyy-mm-dd để tránh lệch múi giờ.
export const fmtDate = (v) => {
  if (!v) return ''
  const s = String(v)
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (m) return `${m[3]}/${m[2]}/${m[1]}`
  const d = new Date(s)
  if (isNaN(d)) return ''
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`
}
export const fmtDateTime = (v) => {
  if (!v) return ''
  const d = new Date(v)
  if (isNaN(d)) return ''
  const date = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`
  const time = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  return `${date} ${time}`
}
