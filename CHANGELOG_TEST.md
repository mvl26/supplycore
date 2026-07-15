# CHANGELOG_TEST — Bug app phát hiện & sửa qua UI test (Playwright)

## BUG-UI-01 — Thông báo "Đặt hàng thành công" bị xoá ngay lập tức
- **Phát hiện:** S3 (gọi hàng thành công) — sau submit, `#order-alert .alert-success` không hiển thị.
- **Nguyên nhân:** `submitOrder()` set thông báo thành công vào `#order-alert`, rồi gọi
  `selectContract()` để reset form — mà `selectContract()` lại `innerHTML = ""` chính
  `#order-alert` → alert bị xoá trong cùng tick, khách không bao giờ thấy.
- **File/hàm:** `supplycore/www/portal/index.html` → `submitOrder()`.
- **Sửa:** đảo thứ tự — gọi `selectContract()` (re-render) TRƯỚC, set alert thành công SAU.
- **Loại:** bug thật của app (UX/hiển thị), không phải lỗi test.

## BUG-UI-02 — Bản in chứng từ dùng dấu phẩy phân tách nghìn (40,000) thay vì dấu chấm VN
- **Phát hiện:** S10 (in hoá đơn) — bản in hiện "40,000" trong khi màn hình portal hiện "40.000".
- **Nguyên nhân:** template print format dùng `"{:,.0f}".format(x)` → phân tách bằng dấu phẩy.
- **File:** `supplycore/patches/v0_11/create_tt99_print_formats.py` (12 chỗ).
- **Sửa:** dùng `"{:,.0f}".format(x).replace(",", ".")` (inline, kiểu VN, khớp fmtVND màn hình).
  Lưu ý: KHÔNG thêm jinja helper mới (`sc_vnd`) vì workers gunicorn preload không reload
  code Python → tham chiếu symbol mới trong hooks gây 500 mọi trang jinja. Inline an toàn.
- **Loại:** bug thật của app (số liệu/định dạng), không phải lỗi test.

## BUG-UI-03 — Portal tải chứng từ ra bản in MẶC ĐỊNH (Standard), không phải TT99
- **Phát hiện:** S10 — bản in tải từ portal thiếu tiêu đề "HOÁ ĐƠN", MST người bán, tiền bằng chữ.
- **Nguyên nhân:** `portal_document_download` gọi `frappe.get_print(doctype, name)` KHÔNG chỉ
  định `print_format` → Frappe render format mặc định (Standard), bỏ qua TT99 vừa tạo.
- **Sửa (không đụng portal.py để tránh reload code):** đặt print format TT99 làm
  `default_print_format` của từng doctype bán hàng qua Property Setter trong patch
  `create_tt99_print_formats.execute` → `get_print` không tham số dùng TT99.
- **File:** `supplycore/patches/v0_11/create_tt99_print_formats.py::execute`.
- **Loại:** bug thật của app (chứng từ in sai mẫu), không phải lỗi test.

---
## data-testid đã thêm vào template app (cho selector ổn định)
File `supplycore/www/portal/index.html` (tab Đặt hàng):
- `contract-value`, `contract-validity`, `contract-ordered-total`, `contract-order-count` (contract-meta)
- `order-line` (+ `data-item="<mã VT>"`), `line-item`, `line-quota`, `line-sold`, `line-remaining` (mỗi dòng hàng)

Đồng thời render bổ sung **định mức / đã gọi / còn lại** per dòng + **tổng đã gọi / số lần gọi**
(dữ liệu đã có ở API `portal_contracts`, trước đó chưa hiển thị).
