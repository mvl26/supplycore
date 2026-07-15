# M9 — Kiểm kê: Luồng thao tác nhân viên

> Mô tả từng bước nhân viên Thủ kho (SC-STOREKEEPER) + Quản lý (SC-MANAGER) thực hiện kiểm kê và đối soát kho.

---

## Tổng quan

| UC | Vai trò | Mục tiêu |
|---|---|---|
| **UC-27** | Thủ kho | Lập Phiếu kiểm kê (ICS), đếm vật tư thực tế, lập biên bản |
| **UC-28** | Thủ kho + Manager | Đối soát SR, ghi lý do per row, xử lý chênh lệch lớn → bắt buộc điều tra |
| **UC-19** | Thủ kho + Manager | Submit SR → tạo SLE đảo + bút toán GL điều chỉnh |

**Điểm truy cập:** sidebar → **M9 Kiểm kê** → list `SC Inventory Count Sheet` hoặc `SC Stock Reconciliation`.

---

## UC-27: Lập Phiếu kiểm kê (ICS) + Đếm

### Tiền điều kiện
- Có dữ liệu tồn kho (SLE) trong warehouse cần kiểm.
- Có thiết bị nhập liệu (máy tính / tablet).

### Các bước

**Bước 1. Tạo phiếu ICS mới**
- Sidebar **M9 Kiểm kê** → list `SC Inventory Count Sheet` → bấm **+ Tạo mới**.
- Form chia làm 3 section:

  **Thông tin chung:**
  - `count_date` = ngày kiểm (mặc định hôm nay).
  - `warehouse` = kho cần kiểm (bắt buộc).
  - `planned_by` = người lập phiếu (tự fill = current user).
  - `counted_by` = người đếm trực tiếp (sẽ ký phiếu).

  **Phạm vi đếm:**
  - `count_scope`:
    - `All Items` (mặc định): kiểm toàn bộ vật tư có tồn ở kho.
    - `By Item Group`: chỉ kiểm 1 nhóm vật tư cụ thể → phải nhập `item_group`.
    - `By Zone`: chỉ kiểm theo zone trên kệ → phải nhập `bin_zone` (VD: "A1").
  - `recount_threshold_pct`: % chênh lệch để bắt buộc đếm lại (mặc định **5%**).
  - `hide_system_qty`: bật ✓ nếu in phiếu "đếm mù" (không cho counter staff biết SL hệ thống).

  **Tổng hợp:** các field read-only sẽ tự fill sau khi đếm.

- Bấm **💾 Lưu** → tạo Draft.

**Bước 2. Tự nạp items theo phạm vi**
- Panel **⚡ Hành động khả dụng** → **📋 Tự nạp items theo phạm vi**.
- Hệ thống query SLE có `qty > 0` trong warehouse + filter scope, tự fill các dòng vào child table `items`:
  - `item`, `item_name`, `uom`, `batch`, `bin_location`
  - `system_qty` = SL hệ thống (sẽ ẩn nếu `hide_system_qty = 1` khi in)
  - `valuation_rate` = đơn giá tham chiếu (cho tính variance_value)
  - `is_counted = 0` (chưa đếm)

**Bước 3. (Tuỳ chọn) In phiếu để counter staff đếm**
- Panel **📊 Tổng quan kiểm kê** → bấm **🖨️ Phiếu đếm**.
- Modal hiển thị bảng có cột "SL đếm" trống, có vùng ký tên cho người đếm + manager.
- Bấm **🖨️ In** để in giấy → giao cho counter staff đi đếm từng vị trí.

**Bước 4. Nhập SL đếm thực tế (bảng nhập đếm)**
- Phía dưới form là panel **⌨️ Bảng nhập đếm** (chỉ hiển thị khi Draft).
- Top panel có:
  - **Progress bar** xanh hiển thị `% đã đếm`.
  - 4 filter chip: **Tất cả / Chưa đếm / Lệch / Đếm lại** (kèm số lượng).
  - Ô tìm kiếm theo mã/tên/lô/vị trí.
- Table cột "SL đếm" là ô input numeric:
  - Gõ số → tự lưu sau **500ms** (debounce).
  - Bấm **Enter** hoặc **↓** để chuyển ô tiếp theo (bàn phím-first, không cần chuột).
  - Bấm **↑** để quay lại ô trước.
  - Row màu:
    - 🟢 Xanh nhẹ: đếm khớp SL hệ thống.
    - 🟡 Vàng: lệch nhỏ (< threshold).
    - 🔴 Đỏ nhẹ: lệch > threshold → cờ "Đếm lại" tự bật.
- Cột "% lệch" hiển thị tỷ lệ chênh lệch.

**Bước 5. Đếm lại lần 2 (nếu cờ "Đếm lại" bật)**
- Filter chip **Đếm lại** → table chỉ còn items cần recount.
- Cột "SL đếm L2" hiện ô input. Counter staff đếm lại → nhập vào ô này.
- Auto-save tương tự.

**Bước 6. Đếm lại lần 3 — cần Manager chứng kiến**
- Nếu lần 2 vẫn lệch > threshold (UC-27 6a):
  - Counter cần manager đứng cạnh chứng kiến.
  - Nhập `manager_witness` (Link user) vào section "Tổng hợp".
  - Nhập SL vào cột "SL đếm L3" cho từng item.
- Hệ thống `before_submit` sẽ chặn submit nếu có L3 nhưng thiếu `manager_witness`.

**Bước 7. Submit phiếu (Counted)**
- Khi `progress = 100%` và mọi item cần đếm lại đã có L2/L3:
  - Banner "✓ Đã đếm xong" hiện trong **Tổng quan kiểm kê**.
- Bấm **📤 Submit**.
- Hệ thống snapshot `system_qty` lần cuối, set `status = 'Counted'`.

**Bước 8. Tạo SR đối soát**
- Sau submit, panel **⚡ Hành động khả dụng** xuất hiện **🔧 Tạo SR đối soát**.
- Bấm → hệ thống lọc items có `|difference| > 0.01`, tạo `SC Stock Reconciliation` Draft, tự navigate sang SR.
- Nếu không có item nào lệch → chặn (`Không có item nào có chênh lệch — không cần reconcile`).

### Lưu ý nhân viên
- ⚠️ Mỗi item có cờ `is_counted` riêng để **phân biệt "chưa đếm" với "đếm = 0"** — đừng để trống ô SL đếm nếu thực tế đếm là 0.
- 🔵 In phiếu chế độ "ẩn SL hệ thống" → counter staff đếm "mù" → kết quả khách quan hơn.
- ❌ Không xoá hoặc sửa `system_qty` thủ công — đây là snapshot từ SLE.

---

## UC-28: Đối soát SR + xử lý chênh lệch lớn

### Tiền điều kiện
- Có SR Draft (vừa tạo từ ICS hoặc tạo trực tiếp).

### Các bước

**Bước 1. Mở SR Draft**
- Sidebar **M9 Kiểm kê** → list `SC Stock Reconciliation` → click SR draft (badge `Nháp`).

**Bước 2. (Nếu tạo SR trực tiếp, không qua ICS) Tải từ ICS**
- Section "Thông tin" nhập `count_sheet` = mã ICS đã Counted.
- Panel **⚡ Hành động khả dụng** → **⬇️ Tải từ phiếu kiểm**.
- Hệ thống auto-fill items với `system_qty` snapshot + `actual_qty` từ ICS.

**Bước 3. Nhập lý do per row**
- Trong child table "Items điều chỉnh", mỗi dòng có cột `reason`:
  - `Counting Error` — lỗi đếm
  - `Damage` — hư hỏng
  - `Theft` — mất cắp
  - `Expiry` — hết hạn
  - `Other` — khác
- Cột `remarks` (optional) — ghi chú chi tiết.
- Hệ thống `before_submit` chặn nếu thiếu `reason` ở dòng có chênh lệch.

**Bước 4. Xử lý chênh lệch lớn (cần điều tra)**
- Nếu |Δ giá trị| > Settings.`large_variance_threshold` (mặc định 10tr):
  - `requires_investigation` tự bật = 1.
  - `investigation_notes` trở thành **bắt buộc** (UC-28).
  - Section "Điều tra" hiển thị → nhập:
    - `investigation_notes`: mô tả điều tra (vì sao có chênh lệch lớn, đã hỏi ai, kết luận gì).
  - Có thể link sang Investigation Report (M10 UC-31) để điều tra sâu hơn.

**Bước 5. Xem biên bản đối soát + xin chữ ký**
- Panel **⚡ Hành động khả dụng** → **📄 Xem biên bản đối soát**.
- Result Modal hiển thị biên bản với:
  - Header: SR name, kho, ngày, tổng Δ qty + Δ value.
  - Table chi tiết items + reason + remarks.
  - Vùng ký: Thủ kho + Manager + (Audit nếu có investigation).
- In ra giấy → xin chữ ký các bên.

**Bước 6. Manager review + reject (nếu không hợp lý)**
- Vai trò Manager mở SR Draft.
- Panel **⚡ Hành động khả dụng** → **✕ Manager từ chối** (nếu thấy lý do không hợp lý).
- Nhập `reason` từ chối → SR set `status = 'Rejected'`, không submit.
- Hoặc Manager submit luôn nếu đồng ý.

**Bước 7. Submit SR (Manager-only)**
- Bấm **📤 Submit** (chỉ role `SupplyCore Manager` hoặc cao hơn).
- Hệ thống `before_submit`:
  - Check role.
  - Check items có `system_qty + difference < 0` (âm tồn) → chặn nếu có.
  - Check `requires_investigation = 1` AND `investigation_notes` rỗng → chặn.
- Sau submit (UC-19 thực thi):
  - Post SLE đảo: với mỗi item, tạo 1 SLE với `qty_change = difference` (dương = thêm, âm = bớt).
  - Post GL: chênh lệch giá trị → `Dr/Cr 632 Chi phí điều chỉnh tồn / Cr/Dr 152 Hàng tồn` tuỳ dấu Δ.
  - Set `status = 'Reconciled'`. Nếu link từ ICS → cập nhật `ICS.status = 'Reconciled'`.

**Bước 8. Theo dõi list**
- List `SC Stock Reconciliation` có cột:
  - `Δ Qty`, `Δ Giá trị` — tổng chênh lệch.
  - `Điều tra` — checkmark nếu `requires_investigation`.
  - `Trạng thái` — badge.

### Lưu ý nhân viên
- ⚠️ SR có `requires_investigation` thường gắn với điều tra M10 UC-31 (lập Investigation Report) — không bỏ qua.
- ❌ Submit SR sẽ **đổi tồn kho thật** — kiểm tra kỹ trước khi submit, đặc biệt với items giá trị lớn.

---

## Map vai trò ↔ hành động

| Vai trò | Tạo ICS | Đếm | Submit ICS | Tạo SR | Submit SR | Reject SR |
|---|---|---|---|---|---|---|
| SC-STOREKEEPER | ✓ | ✓ | ✓ | ✓ | — | — |
| SC-MANAGER | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| SC-AUDITOR | đọc | — | — | — | — | — |

---

## Phím tắt khi đếm (UC-27)

| Phím | Hành động |
|---|---|
| `Enter` hoặc `↓` | Chuyển ô SL đếm tiếp theo |
| `↑` | Quay lại ô trước |
| `Tab` | Chuyển field bình thường (browser default) |

Tự lưu sau **500ms** không gõ — không cần bấm "Lưu" sau mỗi item.

---

## Error codes thường gặp

| Code | Ý nghĩa | Xử lý |
|---|---|---|
| `Phạm vi cannot be "X"` | `count_scope` sai giá trị | Chọn 1 trong: All Items / By Item Group / By Zone |
| `Không có item nào có chênh lệch` | Tạo SR khi mọi item match | Đóng phiếu, không cần SR |
| `Cần Manager chứng kiến lần 3` | Có L3 nhưng thiếu `manager_witness` | Nhập Manager email trước khi submit |
| `requires_investigation` chưa fill notes | SR Δ value > 10tr nhưng thiếu ghi chú điều tra | Nhập `investigation_notes` |
| `Stock cannot go negative` | Submit SR khiến tồn âm | Đếm lại / kiểm tra số liệu |
