# Triển khai CR-03 — "➕ Tạo nhanh" trong droplist (Quick-create)

> Ngày: 25/06/2026 · Đã build frontend. Phương án: **Modal tạo nhanh** (đúng bản chốt — không rời trang).
> Phạm vi (chốt với người dùng): **SC Supplier, SC Item, SC Warehouse, SC Patient, SC Department**.
> CR-01/CR-02 (import) tạm bỏ qua theo chỉ đạo ("import hệ thống vừa sửa rồi").

## Cách hoạt động
1. Mọi **Link field** có `linkTo` nằm trong registry `QUICK_CREATE` tự hiện nút **"+ Tạo mới …"**
   trong droplist (cả field Header lẫn ô trong lưới "Danh mục vật tư").
2. Bấm → mở **modal tạo nhanh** ngay trên form (không điều hướng → **không mất dữ liệu đang nhập**).
3. Modal điền sẵn tên từ text đã gõ; người dùng nhập các field bắt buộc → **"Tạo & chọn"**.
4. Tạo xong → bản ghi mới **tự được chọn** vào đúng trường (Header hoặc đúng dòng lưới).

## Thay đổi mã (frontend)
| File | Thay đổi |
|------|----------|
| `frontend/src/schemas.js` | Thêm export **`QUICK_CREATE`** — field tối thiểu (= field bắt buộc) cho 5 doctype |
| `frontend/src/components/QuickCreateModal.vue` | **MỚI** — modal dùng chung: render field, `createDoc`, emit `created` |
| `frontend/src/components/FormField.vue` | Tự bật `allow-create` khi `linkTo ∈ QUICK_CREATE` (DRY, phủ mọi form) |
| `frontend/src/components/ChildTable.vue` | Re-emit `createNew` kèm `{childField, rowIdx, field}` (trước đây bị bỏ) |
| `frontend/src/components/DocForm.vue` | Truyền `createNew` từ ChildTable lên |
| `frontend/src/pages/DocView.vue` | Mở modal cho doctype hỗ trợ; `onQuickCreated` điền kết quả vào field/dòng; fallback điều hướng cũ cho doctype khác (vd SC Batch) |

## Field tối thiểu mỗi doctype (khớp field bắt buộc)
- **SC Supplier**: Tên NCC, Loại NCC, MST, Email, Điện thoại, Địa chỉ (6 — đều `reqd`; Email cũng cần cho gửi PO).
- **SC Item**: Mã VT, Tên VT, UOM.
- **SC Warehouse**: Tên kho.
- **SC Patient**: Mã BN, Họ tên.
- **SC Department**: Tên khoa/phòng.

## Kiểm thử
```
PASS insert 5/5 doctype với đúng field tối thiểu (rollback):
     SC Supplier→SC-SUP-####, SC Item→<item_code>, SC Warehouse→<tên>, SC Patient→<mã BN>, SC Department→<tên>
PASS frontend build OK (không lỗi import/cú pháp)
PASS createDoc = đúng path mà DocView.save() dùng (REST /api/resource) → đã được chứng minh
PASS reactivity: DocForm.doc là computed theo modelValue → reassign doc.value phản ánh ngay (Header + lưới)
```

## Tự điền cột phụ (đã làm nốt)
`onQuickCreated` lấy luôn **doc vừa tạo** (đã đủ field) để tự điền các cột khai báo `fetchFrom` — **giống hệt
khi chọn bản ghi có sẵn**:
- **Lưới chi tiết:** cột có `fetchFrom.source === field-vừa-tạo` → tự điền (vd tạo nhanh Vật tư trong dòng PO/FC
  → cột **UOM** tự điền từ item mới).
- **Header:** field vừa tạo tự khai `fetchFrom` → set `doc[target_field]`.
- Không round-trip thêm (dùng dữ liệu trả về từ `createDoc`).

**Kiểm thử:** build OK; logic companion khớp đúng `handleLinkSelected` sẵn có (ChildTable & DocForm).

## Kiểm thử trực tiếp trên trình duyệt (Playwright + Chromium)
Drive thật trên SPA đang chạy (nginx :80, đăng nhập user test tạm) tại form **Tạo Hợp đồng khung**:

| Bước | Quan sát |
|------|----------|
| Gõ "ACME Verify NCC" vào droplist NCC | Hiện đúng nút **"+ Tạo mới Supplier \"ACME Verify NCC\""** |
| Bấm "+ Tạo mới" | Mở **modal "Tạo nhanh Nhà cung cấp"** (Tên NCC điền sẵn) |
| Điền + "Tạo & chọn" | Field NCC tự nhận **`SC-SUP-…`** (bản ghi mới) |
| Lưới vật tư: "+ Thêm dòng" → tạo nhanh Vật tư | Dòng nhận **Mã VT mới** + cột **UOM tự điền `Điếu`** (companion fetchFrom) |
| Console | **0 lỗi/cảnh báo** |

> 🐞 **Bug bắt được khi kiểm thử & đã sửa:** `QuickCreateModal` không truyền prop `:open` cho `Modal.vue`
> (`Modal` render bằng `v-if="open"`) → modal **không hiện**. Đã thêm `:open="true"`. Chỉ test trình duyệt
> mới lộ (build vẫn pass). Artifacts test (user/NCC/VT) đã dọn sạch sau kiểm thử.

### Probe nhánh biên (đã chạy thật)
| Probe | Kết quả |
|-------|---------|
| **Thiếu field bắt buộc** | Bấm "Tạo & chọn" khi chưa chọn Loại NCC → toast **"Vui lòng nhập: Loại NCC"**, modal giữ nguyên, **không tạo** bản ghi ✅ |
| **Email sai định dạng** | email=`notanemail` → toast **"Tạo thất bại: Email không hợp lệ: notanemail"** (lỗi backend hiện rõ), modal giữ nguyên, **không tạo** ✅ |
| **Huỷ** | Bấm Huỷ → modal đóng, **không tạo**, field giữ text đang gõ ✅ |
| **Đóng modal** | Click nền (backdrop) → đóng ✅. **Esc → KHÔNG đóng** ⚠️ (Modal.vue chưa bắt phím Esc — gap nhỏ, dùng chung mọi modal) |
| **Tổng quát (doctype khác)** | Form **Cấp phát BN** → tạo nhanh **Bệnh nhân** (field top-level khác doctype) → tự chọn `PROBE-BN-E1` ✅ |

> ⚠️ **Finding (chưa sửa):** `Modal.vue` không đóng bằng phím **Esc** (chỉ click nền). Là component dùng chung
> toàn hệ thống nên để ngỏ, chờ quyết định có thêm Esc-to-close cho mọi modal hay không.

## Còn lại (không cần thiết với bản ghi mới)
- `autoFetch` cấp dòng qua **API** (vd kéo tồn/giá theo item) không tự chạy khi set bằng code — nhưng bản ghi
  **vừa tạo** chưa có tồn/giá nên không ảnh hưởng; người dùng nhập tay như thường.
- Mở rộng registry cho doctype khác (Lô/SC Batch, Khoa…) chỉ cần thêm mục vào `QUICK_CREATE`.
- Validate modal hiện ở mức field bắt buộc + báo lỗi backend; có thể thêm kiểm định dạng (email/MST) nếu cần.
