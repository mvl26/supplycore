// Helper TRÌNH BÀY trạng thái/KCS/hạn dùng — chỉ hiển thị, KHÔNG đụng giá trị/logic nghiệp vụ.
// Dùng chung để 1 trạng thái = 1 màu và cảnh báo HSD nổi bật đồng nhất mọi màn.

// KCS (QC) → badge class chuẩn (gốc: BatchTrace). Rejected LUÔN critical.
export const qcBadge = (s) => ({
  Accepted: 'sc-badge-success', Rejected: 'sc-badge-critical',
  Pending: 'sc-badge-warning', Conditional: 'sc-badge-warning',
}[s] || 'sc-badge-neutral')

export const qcLabel = (s) => ({
  Accepted: 'Đạt', Rejected: 'Không đạt',
  Pending: 'Chờ KCS', Conditional: 'Có điều kiện',
}[s] || s)

// Số ngày còn lại tới hạn dùng (âm = đã hết hạn). null nếu không có ngày hợp lệ.
export function daysToExpiry(expiryDate) {
  if (!expiryDate) return null
  const exp = new Date(expiryDate)
  if (isNaN(exp)) return null
  return Math.floor((exp - new Date()) / 86400000)
}

// Mức khẩn HSD → class token (text + nền mờ token, KHÔNG hardcode hex/palette thô).
// Ngưỡng thống nhất: hết hạn / <30 ngày = danger; <90 ngày = warning; còn lại = ok.
export function expiryInfo(expiryDate) {
  const days = daysToExpiry(expiryDate)
  if (days === null) return null
  if (days < 0)  return { level: 'expired',  cls: 'text-sc-danger bg-sc-danger/10',   label: 'Đã hết hạn', days }
  if (days < 30) return { level: 'critical', cls: 'text-sc-danger bg-sc-danger/10',   label: `Còn ${days} ngày`, days }
  if (days < 90) return { level: 'warning',  cls: 'text-sc-warning bg-sc-warning/10', label: `Còn ${days} ngày`, days }
  return { level: 'ok', cls: 'text-sc-success', label: `Còn ${days} ngày`, days }
}

// Chỉ lấy class tô cảnh báo cho ô ngày HSD ('' nếu bình thường/không cần nổi bật).
export function expiryClass(expiryDate) {
  const info = expiryInfo(expiryDate)
  if (!info || info.level === 'ok') return ''
  return info.cls
}

// Mức độ nghiêm trọng (Alert/cảnh báo) → badge class chuẩn. Gộp thang 3↔4 mức.
export const severityBadge = (s) => ({
  Critical: 'sc-badge-critical', High: 'sc-badge-critical',
  Warning: 'sc-badge-warning', Medium: 'sc-badge-warning',
  Info: 'sc-badge-info', Low: 'sc-badge-info',
}[s] || 'sc-badge-neutral')

