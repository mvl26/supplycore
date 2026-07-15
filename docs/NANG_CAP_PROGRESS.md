# Tiến độ nâng cấp theo tài liệu BA (báo cáo lỗi 16/06 + CR 24/06)

> Cập nhật: 25/06/2026. Làm tuần tự theo ưu tiên; mỗi mục đọc lại BA + kiểm thử.
> ⚠️ **Backend cần reload web để LIVE**: gunicorn `--preload` không tự nạp code .py.
> Chạy `sudo supervisorctl restart frappe-bench-frappe-web` (agent không có quyền restart).

## Đã xong (9/15)

| # | Mục | Nội dung | Kiểm thử |
|---|-----|----------|----------|
| 1 | L03/T05 | Droplist/ô chọn hiển thị **Tên (mã)**, tên làm chính | ✅ Live (Playwright) |
| 2 | L11 | Tìm HĐ khung theo **tên/mã NCC, số HĐ, mã/tên vật tư** (endpoint `search_framework_contract`) | ✅ Backend-proven; live cần reload |
| 3 | L04 | HĐK chọn Ngày ký → tự điền Hiệu lực từ = ngày ký, Hết hạn = +1 năm | ✅ Live + backend |
| 4 | L09/T13 | YC mua "+ Thêm dòng" → tự điền Ngày cần dòng = Ngày cần chung | ✅ Live |
| 5 | T14 | Cảnh báo (mềm) khi Ngày cần < hôm nay | ✅ Live |
| 6 | L07/T03 | Bảng/cột tiền dùng **đầy đủ + ₫**; rút gọn k/tr chỉ ở KPI (có tooltip) | ✅ Live ("5.000.000 ₫") |
| 7 | T04 | Mọi hiển thị ngày → **dd/mm/yyyy** (số 0 đứng đầu) | ✅ Live |
| 8 | L16 | "Gửi duyệt" chỉ hiện khi draft đã **Lưu (sạch)**; đang sửa → ẩn + nhắc "Lưu để hiện nút Gửi duyệt" | ✅ Live |
| 9 | L10 | Bối cảnh duyệt YC mua: Người yêu cầu = **Tên (account)** (mặc định = người tạo), bỏ mục thừa | ✅ Backend + config; live cần reload |

**Cơ chế dùng chung đã thêm (tái sử dụng cho sau):** `derive` (DocForm), `inheritFrom` (ChildTable),
`warnPastDate` (FormField), `or_filters` (list_docs), `_seq` chống race (LinkAutocomplete).

## Đã xong thêm (10–13)
| # | Mục | Nội dung | Kiểm thử |
|---|-----|----------|----------|
| 10 | T07 | QC bắt buộc chọn Checklist trước khi kết luận (SC-E033) | ✅ backend (console); live cần reload |
| 11 | L05 | Đính kèm **1 hoặc nhiều tệp** (FormField AttachMultiple + field `attachments`) | ✅ Live (upload 2 → 2, gỡ 1 → 1) |
| 12 | T01 | Alias /contracts, /inventory, /suppliers… + trang 404 gợi ý | ✅ Live |
| 13 | Esc | Modal đóng bằng phím Esc | ✅ Live |

## Đã xong (14–15) — IMPORT (CR-01 + CR-02)
| # | Mục | Nội dung | Kiểm thử |
|---|-----|----------|----------|
| 14 | CR-01 | Export/Import **list-level** Excel 2 sheet (Phiếu + Vật tư, nối bằng Mã phiếu) cho **8 doctype** (FC, MR, PO, PR, TR, DR, PD, ICS). Engine chung `supplycore/api/voucher_io.py`. Nhập tạo mới + cập nhật, **phiếu luôn Draft**; guardrail chỉ Draft mới đè item. | ✅ backend round-trip + tạo/cập nhật Draft (console, rollback) |
| 15 | CR-02 | Nút **Tải mẫu / Import / Export ngay tại lưới** trong form (ChildTable.vue) — parse+validate từng dòng, **nạp vào lưới in-memory (chưa lưu)**, tổng tự tính. API `voucher_io.parse_child_rows` / `child_template`. | ✅ backend parse/template (console) + frontend build |

> Quyết định mặc định CR-02 (theo tài liệu yêu cầu chốt): **bỏ dòng lỗi + báo rõ + nạp dòng hợp lệ**
> (mặc định "Thêm vào lưới", có tuỳ chọn "Thay thế"). Không lưu im lặng (nhất quán T12).
> Xem chi tiết: `supplycore/api/VOUCHER_IO_FLOW.md`.

## Cần BẠN chốt nghiệp vụ (chưa làm)
L08 (bỏ bắt comment dài duyệt HĐK), L18 (thêm bước Duyệt QC), **L22 (bỏ kho 3 tầng — ngược requirement)**, T15 (khóa người thực hiện M6/M9).
L10 phần "Khoa lấy từ khoa người yêu cầu": **không có liên kết User→Khoa** trong data model (chỉ `SC Department.head_user`) → cần bổ sung mapping nếu muốn auto.

## Việc vận hành còn lại
- **Reload web 1 lần** để mọi thay đổi backend (cả các fix buổi trước) + #2/#9/#10 lên LIVE, rồi verify live.
- Frontend đã build vào `public/frontend` (live ngay).
