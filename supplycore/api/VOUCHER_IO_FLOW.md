# FLOW — Xuất/Nhập phiếu cha-con bằng Excel 2 sheet (engine chung)

**Mục tiêu:** Xuất/nhập **danh sách phiếu kèm danh mục vật tư** ở cấp list, mỗi vật tư
một dòng riêng (KHÔNG nén JSON 1 ô). Một engine cấu hình chung cho mọi chứng từ có 1
child table chính.

Module: `supplycore/api/voucher_io.py` — API `supplycore.api.voucher_io.*`.

## Doctype được hỗ trợ (CONFIGS)
| Doctype | Nhãn | Mã | item child | Ghi chú |
|---|---|---|---|---|
| Framework Contract | Hợp đồng khung | SC-FC | FC Item (`item_code`) | guard theo `approval_stage` |
| SC Material Request | Yêu cầu mua | SC-MR | SC Material Request Item (`item`) | |
| SC Purchase Order | Đơn mua | SC-PO | SC Purchase Order Item (`item`) | guard theo `approval_stage` |
| SC Purchase Receipt | Phiếu nhập (tiếp nhận) | SC-PR | SC Purchase Receipt Item (`item`) | |
| SC Transfer Request | Yêu cầu chuyển kho | SC-TR | SC Transfer Request Item (`item`) | |
| SC Inventory Count Sheet | Phiếu kiểm kê | SC-ICS | SC ICS Item (`item`) | `require_items=False` |

Chưa làm: SC Quality Inspection (CR ghi "ít liên quan", 1 dòng/phiếu) — bỏ qua.
Đối chiếu nghiệp vụ tổng thể: `docs/ba-miyano/SupplyCore_MVL_BA.html`.

## CR-02 — Import/Export/Tải mẫu ngay tại lưới trong form (ChildTable)
- Backend: `parse_child_rows(doctype, content_b64, file_type)` → parse 1 sheet vật tư,
  validate từng dòng (item/uom tồn tại, SL>0 trừ ICS), trả `{rows_ok, rows_error}` — **KHÔNG ghi DB**.
  `child_template(doctype, file_type)` → file mẫu chỉ cột vật tư (xlsx/csv).
- Frontend: `ChildTable.vue` thêm nút **Tải mẫu / Import / Export** (hiện khi doctype ∈
  `VOUCHER_IO_DOCTYPES`). Import → modal: chọn file → kiểm tra (preview ok/lỗi) → **nạp dòng hợp lệ
  vào lưới in-memory** (mặc định Thêm, có tuỳ chọn Thay thế); tự tính cột compute. Export = CSV
  client-side từ lưới đang có (chưa lưu).
- Hành vi mặc định: **bỏ dòng lỗi + báo rõ + nạp dòng hợp lệ** (không lưu im lặng).
- Lưu ý: vài field phụ (PR `manufacturing_date`/`batch_no`, DR `batch`, MR `remarks`/`warehouse`,
  ICS `reason`) import + LƯU bình thường nhưng hiện chưa có cột trong lưới FORM_SCHEMAS — chỉ là
  không hiển thị/sửa được trên lưới (có thể thêm cột sau nếu cần).

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
- Cột read-only/auto (Tên VT, Thành tiền, Tổng…, Trạng thái, Người tạo) chỉ để xem.
