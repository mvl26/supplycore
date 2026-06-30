// Stack handler cho nút Back cứng Android. Màn nào có "chi tiết" mở (state cục
// bộ, KHÔNG phải route — vd Receiving.current / ApproveDocs.activeDoc /
// StockLookup mode='stock') thì push handler đóng-chi-tiết khi mở, pop khi đóng.
// MobileShell gọi handleBack() TRƯỚC khi router.back()/exitApp → Back đóng chi
// tiết (giữ dữ liệu đang nhập) thay vì thoát app.
const _stack = []

export function pushBack(fn) {
  if (typeof fn === 'function') _stack.push(fn)
}
export function popBack(fn) {
  const i = _stack.lastIndexOf(fn)
  if (i >= 0) _stack.splice(i, 1)
}
// Chạy handler trên cùng. Trả true nếu đã xử lý (Back KHÔNG nên thoát app/back route).
export function handleBack() {
  const fn = _stack[_stack.length - 1]
  if (fn) { fn(); return true }
  return false
}
