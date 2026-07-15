# Phân tích yêu cầu cải tiến CR-01 / CR-02 / CR-03 (Import/Export & Quick-create)

> Nguồn: `docs/09. Yêu cầu cải tiến 20260624.rar` →
> `TaiLieu_YeuCau_CaiTien_ImportExport_NgayTao24062026.html` (BA lập 24/06/2026, đã chốt với chủ đầu tư).
> Phân tích đối chiếu **mã nguồn thực tế**. Ngày: 24/06/2026.
> Loại: **enhancement** (không phải bug) — khớp với phân loại L06/T11 (import Excel) đã ghi nhận trước đó.

## 0. Tóm tắt điều hành

| CR | Yêu cầu | Nền tảng đã có | Khoảng trống chính | Ưu tiên | Ước lượng |
|----|---------|----------------|--------------------|---------|-----------|
| CR-01 | Export/Import **list-level** đủ Header + **toàn bộ dòng vật tư** | `data_io.py` đã round-trip child (cột JSON) | (1) `export_data` đang **bỏ** child; (2) chưa có **Excel 2 sheet quan hệ** | **P1** | ~3–5 ngày |
| CR-02 | Nút Import/Export/Tải mẫu **ngay tại lưới** trong form Tạo/Sửa | `ChildTable.vue` + `fileToBase64` + engine backend | UI lưới chỉ có "+ Thêm dòng"; chưa có **validate+preview nạp vào lưới (chưa lưu)** | **P1** | ~4–6 ngày |
| CR-03 | "➕ Tạo nhanh" trong droplist tham chiếu | `LinkAutocomplete.allowCreate` + `DocView.onCreateNewLink` (điều hướng + prefill) **đã có sẵn nhưng chưa bật** | Chưa bật `canCreateNew` cho field nào; chưa có **modal tạo nhanh** + **giữ nháp** chắc chắn | **P2** | ~3–5 ngày |

**Khuyến nghị chủ đạo:** làm **một cơ chế cha–con dùng chung** (1 backend + 1 component lưới + 1 modal
quick-create) rồi áp cho cả 7 chứng từ — KHÔNG code lặp từng module. Engine `data_io.py` là nền tốt,
đã có dry-run/preview/partial-success/savepoint — tận dụng tối đa.

Phạm vi 7 chứng từ có lưới (CR-01/02) + mọi droplist (CR-03):

| Chứng từ | Parent DocType | Child table (item) |
|----------|----------------|--------------------|
| Hợp đồng khung | Framework Contract | `FC Item` |
| Yêu cầu mua | SC Material Request | `SC Material Request Item` |
| Đơn mua | SC Purchase Order | `SC Purchase Order Item` |
| Phiếu nhập | SC Purchase Receipt | `SC Purchase Receipt Item` |
| Chuyển kho | SC Transfer Request | `SC Transfer Request Item` |
| Cấp phát BN | SC Patient Dispensing | `SC PD Item` |
| Kiểm kê | SC Inventory Count Sheet | `SC ICS Item` |
| (QC — 1 dòng/phiếu) | SC Quality Inspection | `SC QI Reading` (ít liên quan) |

---

## CR-01 · Import/Export list-level đủ Header + Danh mục vật tư

### Yêu cầu
Export/Import một hoặc nhiều chứng từ phải tái tạo **đầy đủ** Header + tất cả dòng vật tư. Hai phương án:
(a) 1 file = 1 chứng từ (khối Header trên, bảng vật tư dưới); (b) hàng loạt = **Excel 2 sheet cố định**
(`Header` + `ChiTiet` liên kết bằng *Mã chứng từ*). Tệp đính kèm chỉ ghi **tên tệp**.

### Hiện trạng (mã nguồn)
- **Engine `supplycore/api/data_io.py` đã mạnh:** dry-run + preview + báo lỗi dòng + partial-success (savepoint),
  tôn trọng role permission. Định dạng **"3 dòng"** (dòng1 = nhãn, dòng2 = fieldname, dòng3+ = dữ liệu) đã có
  trong `_build_file()`.
- **Child table — bán phần:**
  - `get_template()` ✔ **đã** kèm dòng con dưới dạng **cột JSON-array** (`json.dumps(items …)`).
  - `import_data()` ✔ **đã** parse child từ JSON (`json.loads`) và lưu list vào doc.
  - `export_data()` ✘ **bỏ** Table fieldtype (`if df.fieldtype == "Table": continue`) → **xuất thiếu dòng vật tư**.
- **DocList.vue** gọi `dataIo.exportList(columns=…)` chỉ truyền **field phẳng** (Header) → không có cột con.
- **Chưa hỗ trợ Excel nhiều sheet:** `_build_file()` chỉ tạo **1 sheet** (`wb.active`).

### Khoảng trống
1. `export_data`/`exportList` không kèm child → **đây là nguyên nhân "mất dòng vật tư"** mà CR nêu.
2. Định dạng hiện là **child gói trong 1 ô JSON** — round-trip được nhưng **không dùng được với 300–400 dòng**
   (người dùng không đọc/sửa nổi JSON). CR chốt cần **2 sheet quan hệ** (hoặc layout Header-trên/bảng-dưới).

### Đề xuất kỹ thuật
- **Bản chốt (b):** thêm chế độ export/import **`.xlsx` 2 sheet** vào `data_io.py`:
  - `Header` (1 dòng/chứng từ, đủ field Header) + `ChiTiet` (1 dòng/vật tư, có cột *Mã chứng từ* khoá ngoại).
  - Import: đọc 2 sheet, **gom ChiTiet theo Mã chứng từ** → dựng parent+child, chạy qua dry-run sẵn có.
  - Mở rộng `_build_file()` để ghi nhiều sheet (openpyxl `wb.create_sheet`).
- **Bản (a) 1 chứng từ:** layout Header block + bảng vật tư trong 1 sheet (thuận cho sửa lẻ).
- Sửa `export_data` để **tuỳ chọn** kèm child (đừng phá luồng phẳng cũ — thêm cờ `include_children`).
- Tệp đính kèm: chỉ ghi **filename** (đã đúng chủ trương; không nhúng nhị phân).

### Tiêu chí nghiệm thu → khả thi
- Round-trip 1 chứng từ tái tạo 100% Header + dòng: **khả thi** (engine đã có import child).
- Export N chứng từ → 2 sheet → import lại đủ N + chi tiết: **khả thi** sau khi thêm multi-sheet.
- Tổng Header = Σ thành tiền sau import: phụ thuộc `validate()` parent tự tính lại total (đa số doctype đã có).
- Báo lỗi Mã chứng từ/Mã VT sai: engine đã có cơ chế lỗi-theo-dòng — chỉ cần map thông điệp.

### Rủi ro / cần chốt
- Chứng từ **submittable** (PO/PR…): import tạo **Draft** hay tự submit? → đề xuất luôn **Draft**, người dùng tự duyệt.
- Update vs insert: khớp theo cột `name`; với chứng từ chưa có `name` (tạo mới) cần quy ước rõ.
- Ràng buộc nghiệp vụ mới (L12/L14 PO theo HĐK…) vẫn áp khi import → file sai dữ liệu sẽ bị chặn (đúng).

---

## CR-02 · Import/Export ngay tại lưới "Danh mục vật tư" trong form

### Yêu cầu
Trong form Tạo/Sửa, tại lưới vật tư (300–400 dòng) bổ sung **"Tải file mẫu" / "Import Excel/CSV" / "Export"**.
Luồng: tải mẫu → điền → import → **validate từng dòng + xem trước + báo lỗi** → nạp vào lưới (vẫn sửa tay được) →
tổng tự tính.

### Hiện trạng (mã nguồn)
- `frontend/src/components/ChildTable.vue`: lưới chỉ có **"+ Thêm dòng"** (`newRow`) và xoá dòng (`removeRow`).
  **Không** có nút import/export/mẫu.
- **Không có parser Excel/CSV phía client** (chỉ `fileToBase64` trong `api.js`; mọi parse nằm ở backend Python).

### Khoảng trống
- Toàn bộ UI nút + luồng **preview-rồi-mới-nạp-vào-lưới** chưa có.
- Điểm khác CR-01: ở đây **nạp vào lưới in-memory của form đang soạn (CHƯA lưu)**, không phải insert thẳng DB.

### Đề xuất kỹ thuật
- Thêm vào `ChildTable.vue` 3 nút; dùng lại engine backend ở chế độ **"parse + validate, KHÔNG ghi DB"**:
  - Thêm API `data_io.parse_child_rows(doctype, child_field, content_b64, file_type)` → trả `{rows_ok, rows_error}`
    để frontend hiển thị **preview** + đánh dấu dòng lỗi.
  - Validate từng dòng: Mã VT tồn tại? UOM hợp lệ? SL/đơn giá là số > 0? (tái dùng `_coerce_value`/`_build_doc_dict`).
  - "Tải mẫu": tái dùng `get_template` nhưng **chỉ cột của child** (Mã VT, UOM, SL, Đơn giá…).
- Nạp `rows_ok` vào mảng items của form; giữ cho sửa tay; trigger tính lại tổng (đã có ở compute hiện tại).
- Có thể parse client-side bằng SheetJS để preview tức thì — nhưng **ưu tiên backend** (đã có sẵn, đỡ lệch logic).

### Tiêu chí nghiệm thu → khả thi
- Import ~400 dòng hợp lệ trong vài giây: khả thi (chỉ parse + validate, chưa ghi DB).
- File có dòng sai → chỉ rõ dòng, không nạp dòng lỗi, **không lưu im lặng** (đúng tinh thần fix T12 vừa làm).
- Có nút tải mẫu đúng cột từng loại chứng từ: khả thi (template theo child meta).
- Tổng tự tính sau import: dựa compute sẵn của form.

### Rủi ro / cần chốt
- "Chặn toàn bộ nếu có dòng lỗi" **hay** "nạp dòng đúng + bỏ dòng lỗi"? CR cho cả 2 — cần chốt 1 hành vi mặc định.
- Hiệu năng render lưới 400 dòng trong SPA (liên quan T02): cân nhắc ảo hoá (virtual scroll) nếu lag.

---

## CR-03 · "➕ Tạo nhanh" trong droplist tham chiếu (Quick-create)

### Yêu cầu
Trong droplist (NCC, Vật tư, Kho, Bệnh nhân, Khoa, Lô…) thêm dòng **"➕ Tạo mới"**. Ưu tiên **popup tạo nhanh**
ngay trên form (không rời trang). Nếu phải chuyển trang → **giữ nháp** chứng từ đang soạn, tạo xong tự điền.

### Hiện trạng (mã nguồn) — đã có nền, **chưa bật**
- `LinkAutocomplete.vue` đã có prop `allowCreate` + nút **"+ Tạo mới {linkTo}"** (emit `createNew`), kèm fallback
  UX-004 gợi ý tạo khi không có kết quả.
- `DocView.vue::onCreateNewLink()` đã xử lý: lưu `sessionStorage` (returnPath + field + prefill) rồi
  **điều hướng** `/doc/{linkTo}/new`. (Tức **phương án "chuyển trang + prefill"** đã tồn tại.)
- **Nhưng** `field.canCreateNew` **chưa được set ở bất kỳ schema nào** (chỉ batch trước đây) → tính năng **đang tắt**.
- **Chưa có modal tạo nhanh** (hiện là điều hướng full-page).

### Khoảng trống
1. Bật `canCreateNew` cho các Link field cần (NCC, Vật tư, Kho, Bệnh nhân, Khoa, Lô) trong `schemas.js`.
2. (Ưu tiên CR) Nâng cấp từ điều hướng → **modal tạo nhanh** (form rút gọn các field bắt buộc), tạo xong tự chọn.
3. **Bảo toàn nháp:** xác minh khi quay lại form cha, dữ liệu đang nhập dở **không mất**. Hiện `sessionStorage`
   chỉ lưu returnPath + prefill cho field đích — **CHƯA chắc** khôi phục mọi field cha đang nhập dở
   (**điểm rủi ro phải kiểm/triển khai**: lưu nháp toàn form cha trước khi điều hướng/mở modal).

### Đề xuất kỹ thuật
- **Bước 1 (rẻ, nhanh):** bật `canCreateNew` cho các field tham chiếu chính → kích hoạt luồng điều hướng + prefill
  **đã có**; bổ sung lưu **nháp toàn form cha** vào sessionStorage để quay lại không mất dữ liệu.
- **Bước 2 (đúng yêu cầu "ưu tiên"):** dựng **QuickCreateModal** dùng chung: nhận `doctype` + tập field tối thiểu
  (đọc từ `schemas.js`/meta), submit qua API tạo doc, trả `name` → component cha tự chọn. Không rời trang.
- Áp cho mọi `LinkAutocomplete` toàn hệ thống (1 component → phủ toàn bộ).

### Tiêu chí nghiệm thu → khả thi
- Mỗi droplist có "➕ Tạo mới": khả thi (set cờ schema).
- Bấm → mở tạo nhanh → lưu xong tự chọn: phương án điều hướng đã có; **modal** cần thêm.
- **Dữ liệu cha không mất:** đây là **điểm cần làm kỹ** (hiện chưa đảm bảo) — quyết định độ ưu tiên modal vs nháp.

---

## Tổng hợp khuyến nghị triển khai

1. **Một engine cha–con dùng chung** (mở rộng `data_io.py`): multi-sheet xlsx + parse-child-không-ghi-DB.
   Phủ cả CR-01 (list) và CR-02 (grid) → tránh lặp 7 module.
2. **Thứ tự:** CR-01 + CR-02 (P1, toàn vẹn dữ liệu + nhập 400 dòng) trước go-live; CR-03 (P2) sau.
3. **Tận dụng sẵn có:** dry-run/preview/partial-success của `data_io`; luồng điều hướng+prefill của `onCreateNewLink`;
   nút allowCreate của `LinkAutocomplete`.
4. **Bắt buộc:** validate + preview + báo lỗi-theo-dòng; **không lưu thất bại im lặng** (nhất quán với fix T12).
5. **Quyết định cần chủ đầu tư chốt:** (a) import chứng từ submittable → luôn Draft? (b) dòng lỗi: chặn cả file hay
   bỏ dòng lỗi? (c) CR-03 ưu tiên modal ngay hay chấp nhận điều hướng + giữ nháp ở bước 1?

### Liên hệ báo cáo lỗi trước (16/06)
- CR-01/CR-02 **chính thức hoá** L06 (import Excel danh mục) & T11 (đấu nối Nhập) — đã ghi "nghiệp vụ/cải tiến".
- CR-03 liên quan L03/T05 (tên vs mã) và quick-create Batch đã có; mở rộng ra mọi droplist.
- L05 (đính kèm nhiều tệp) **độc lập** với CR này (CR chỉ ghi *tên tệp*, không khôi phục file).
