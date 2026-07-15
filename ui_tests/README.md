# UI Test (Playwright) — SupplyCore MVL Portal

Bộ kiểm thử giao diện web tự động mô phỏng thao tác người dùng thật (đăng nhập, bấm,
điền form, xác nhận, đọc số liệu) trên site test **supplycore-miyano.local** (qua nginx
port 80). Headless, có screenshot/trace/video khi fail.

## Chạy một lệnh
```bash
bash ui_tests/run.sh            # seed môi trường + chạy toàn bộ 12 kịch bản
bash ui_tests/run.sh specs/S3_order_success.spec.js   # chạy 1 spec
```
`run.sh` gồm 2 bước: (1) `scripts/setup_test_env.sh` — tạo lại Print Format TT99 (idempotent) +
seed user + seed dataset, (2) `npx playwright test`.

**Prerequisite lần đầu trên môi trường mới** (một lần, không nằm trong run.sh):
```bash
bench --site supplycore-miyano.local migrate      # sync doctype/patch (field Settings, quyền...)
bench build --app frappe                           # build asset frappe (login form + desk/SPA cần)
```
`setup_test_env.sh` ĐÃ tự chạy `create_tt99_print_formats.execute` mỗi lần (không dựa vào migrate,
vì patch có thể đã log ở môi trường đã migrate) → S10 luôn có sẵn print format TT99.

> **Lưu ý side-effect toàn cục:** bước tạo TT99 đặt `default_print_format` cho 6 doctype bán hàng
> (SI/DN/Acceptance/SFC/Receipt/SO) → in mặc định trên **desk/SPA nội bộ** cũng dùng mẫu TT99, không
> chỉ đường tải của portal. Đây là ý định TT99 của GĐ1 nên chấp nhận được, nhưng là thay đổi hành vi
> in toàn hệ thống — nêu rõ để không bất ngờ.

- baseURL: `http://supplycore-miyano.local` (nginx :80 — phục vụ /assets + proxy về gunicorn
  :8002). **KHÔNG** dùng :8002 trực tiếp (gunicorn qua supervisor không serve /assets).
- Chốt an toàn trong `global-setup.js`: chỉ chạy khi baseURL trỏ site test đã biết.
- Report HTML: `ui_tests/report/`, artifacts (screenshot/trace/video khi fail): `ui_tests/artifacts/`.

## Kết quả — 12/12 XANH (chạy 2 lần liên tiếp đều xanh, chống flaky)

| # | Kịch bản | Trạng thái | Ghi chú |
|---|---|---|---|
| S1 | Đăng nhập & điều hướng (KH A thấy dữ liệu mình, không thấy KH B) | ✅ | portal /portal |
| S2 | Xem HĐ khung (định mức/đã gọi/còn lại khớp seed) | ✅ | render bổ sung 3 số + stats |
| S3 | Gọi hàng thành công → đơn Chờ duyệt | ✅ | fix BUG-UI-01 |
| S4 | Gọi vượt định mức bị chặn (nêu SL còn lại), không tạo đơn | ✅ | |
| S5 | Nợ vượt ngưỡng bị chặn + hiện số tối thiểu phải trả | ✅ | BRU-AR-001, min 60.000 |
| S6 | Hết tồn bị chặn (BRU-INV-002) | ✅ | item seed hết tồn |
| S7 | Duyệt nội bộ (SPA) → sinh phiếu giao | ✅ | vai Manager, SPA /supplycore |
| S8 | KH xác nhận nhận hàng → nghiệm thu → hoá đơn hiện đúng số tiền | ✅ | bán tự động (NV xuất HĐ) |
| S9 | Công nợ & lịch sử (tổng đã gọi/số lần gọi/công nợ) | ✅ | số khớp tính tay |
| S10 | In chứng từ TT99 (trường bắt buộc + số liệu khớp) | ✅ | fix BUG-UI-02, BUG-UI-03 |
| S11 | Phân quyền sâu (KH B truy cập /api/resource của KH A → 403) | ✅ | REST isolation |
| S12 | Responsive mobile 390×844 (S1–S3) | ✅ | |

## Bug app đã sửa (chi tiết trong `CHANGELOG_TEST.md`)
- **BUG-UI-01** — `submitOrder()` (portal) xoá thông báo thành công ngay khi vừa hiện (selectContract
  clear #order-alert). Sửa: re-render trước, set alert sau.
- **BUG-UI-02** — bản in dùng dấu phẩy phân tách nghìn (40,000) thay dấu chấm VN (40.000). Sửa: inline
  `.replace(",", ".")` trong template TT99 (không thêm jinja helper mới — workers preload không reload code).
- **BUG-UI-03** — `portal_document_download` render format Standard thay vì TT99. Sửa: đặt TT99 làm
  `default_print_format` của doctype qua Property Setter (không đụng portal.py).

## data-testid đã thêm vào app
`supplycore/www/portal/index.html`: `contract-value`, `contract-validity`, `contract-ordered-total`,
`contract-order-count`, `order-line` (+`data-item`), `line-item`, `line-quota`, `line-sold`, `line-remaining`.

## Ràng buộc môi trường (đã xác minh)
- 3 bench chạy song song: :8000 (frappe-bench), :8001 (lms), :8002 (yhct = app này). Test CHỈ trỏ site yhct.
- Assets phải build (`bench build --app frappe`) + serve qua nginx :80. Gunicorn preload KHÔNG reload code
  Python → mọi thay đổi hàm Python/hook cần restart worker mới có hiệu lực (đã tránh bằng cách chỉ đổi
  template/DB/property setter).

## Đề xuất kịch bản nên thêm (tương lai)
- Thanh toán một phần trên portal (nếu có UI thu tiền cho KH) → công nợ giảm → mở khoá gọi hàng.
- Đăng ký khách mới (portal_register) + luồng guest.
- Huỷ đơn/huỷ phiếu và kiểm SLE/công nợ đảo đúng trên UI.
- Đa lô FEFO khi giao (nhiều batch) hiển thị đúng trên phiếu giao.
- Kiểm tra fiscal lock chặn thao tác trên UI.
