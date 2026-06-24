# FLOW — Xuất/Nhập phiếu cha-con bằng Excel 2 sheet (engine chung)

**Mục tiêu:** Xuất/nhập **danh sách phiếu kèm danh mục vật tư** ở cấp list, mỗi vật tư
một dòng riêng (KHÔNG nén JSON 1 ô). Một engine cấu hình chung cho mọi chứng từ có 1
child table chính.

Module: `supplycore/api/voucher_io.py` — API `supplycore.api.voucher_io.*`.

## Doctype được hỗ trợ (CONFIGS)
| Doctype | Nhãn | Sheet phiếu | Mã | item child |
|---|---|---|---|---|
| Framework Contract | Hợp đồng khung | Hợp đồng | SC-FC | FC Item (`item_code`) |
| SC Transfer Request | Yêu cầu chuyển kho | Phiếu | SC-TR | SC Transfer Request Item (`item`) |
| SC Purchase Receipt | Phiếu nhập (tiếp nhận) | Phiếu | SC-PR | SC Purchase Receipt Item (`item`) |
| SC Dispensing Request | Yêu cầu cấp phát | Phiếu | SC-DR | SC DR Item (`item`) |
| SC Patient Dispensing | Cấp phát bệnh nhân | Phiếu | SC-PD | SC PD Item (`item`) |

Thêm doctype mới = thêm 1 entry vào `CONFIGS` + 1 chuỗi vào `VOUCHER_IO_DOCTYPES`
(frontend/src/pages/DocList.vue). Không phải viết code mới.

## Định dạng file (chốt với người dùng)
1 file Excel `.xlsx` gồm 2 sheet nối nhau bằng **Mã phiếu** (cột đầu mỗi sheet):
- Sheet phiếu (vd "Hợp đồng" / "Phiếu") — mỗi phiếu 1 dòng.
- Sheet **"Vật tư"** — mỗi item 1 dòng.
- Sheet **"Hướng dẫn"** (chỉ trong template) — giải thích Mã phiếu + quy tắc.

Header mỗi sheet 2 dòng: **dòng 1 = label**, **dòng 2 = fieldname**, dữ liệu từ **dòng 3**.
Người dùng tự gõ file **1 dòng header** (chỉ nhãn) cũng được — `_read_sheet` tự nhận diện
1 hay 2 dòng (dựa vào dòng 2 có khớp fieldname hay không).

## Quy tắc NHẬP (quan trọng)
- **Phiếu nhập vào LUÔN ở Draft** — engine chỉ `insert()`/`save()`, KHÔNG bao giờ `submit()`.
- Gom dòng theo **Mã phiếu**:
  - Mã **chưa có** → **tạo mới** (Draft). Mã trong file chỉ là khoá gom; hệ thống tự cấp
    mã thật theo autoname series.
  - Mã **đã có** → **cập nhật**, **thay toàn bộ** danh mục vật tư.
- **Guardrail:** chỉ phiếu đang **Draft** (`docstatus=0`; với FC thêm điều kiện
  `approval_stage ∈ {Draft, Rejected, ''}`) mới cập nhật/ghi đè được. Phiếu đã
  submit/duyệt/ghi sổ → **bỏ qua kèm lý do**.
- Tạo mới cần đủ field `required_create` + ≥1 dòng vật tư.
- Coerce theo fieldtype thật: ngày (`datetime`/`yyyy-mm-dd`/`dd/mm/yyyy`), số (bỏ dấu phẩy),
  Check (1/0/true/có…). Ô rỗng → **bỏ qua** (giữ default/giá trị cũ).
- Kiểm tra Link tồn tại theo `link_header`/`link_item` (NCC, kho, khoa, BN, item, UOM, lô…).
- `dry_run=1`: chỉ validate + đếm, preview **theo từng phiếu**. `dry_run=0`: savepoint
  **mỗi phiếu** — phiếu lỗi rollback riêng, phiếu OK commit (partial success). Controller
  `validate()` của từng doctype vẫn chạy.

## Endpoints
- `export_voucher(doctype, filters, order_by, limit)` → file 2 sheet (có dữ liệu).
- `voucher_template(doctype, with_data, limit)` → template (kèm sheet Hướng dẫn).
- `import_voucher(doctype, content_b64, dry_run, allow_create)` → {summary, preview, errors}.
- `list_voucher_doctypes()` → danh sách doctype hỗ trợ.

## Frontend
- `frontend/src/api.js` → `voucherIo` (export/template/import, tham số doctype).
- `frontend/src/components/VoucherIO.vue` → nút Xuất/Nhập + 2 modal, kết quả theo phiếu.
- `frontend/src/pages/DocList.vue` → render `VoucherIO` cho doctype ∈ `VOUCHER_IO_DOCTYPES`,
  còn lại dùng `ListImportExport` generic.

## Lưu ý
- Chỉ Excel `.xlsx` (CSV không chứa 2 sheet).
- Cột read-only/auto (Tên VT, Thành tiền, Tổng…, Trạng thái, Người tạo, BHYT) chỉ để xem.
