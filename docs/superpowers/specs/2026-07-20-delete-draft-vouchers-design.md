# Thiết kế: Xóa phiếu nháp (draft) toàn hệ thống

**Ngày:** 2026-07-20
**Yêu cầu gốc:** "Phiếu nào đang là trạng thái nháp thì có thể xóa được — check lại tất cả các module."

## Bối cảnh

- SPA Vue ở `frontend/` đã có helper `deleteDoc(doctype, name)` trong `api.js` nhưng **chưa được gọi ở đâu** — hiện không có nút xóa nào trong UI.
- Access matrix (`supplycore.api.access.menu`) đã trả sẵn `doctypes[dt].delete` và `is_submittable` cho mỗi doctype → frontend có đủ dữ liệu để gate nút.
- 21 doctype submittable ở backend (`is_submittable:1`) **khớp chính xác** với set `SUBMITTABLE_DOCTYPES` hardcode trong `frontend/src/modules.js` (0 lệch) → audit phủ hết mọi module.
- Hiện trạng quyền: hầu hết doctype **chỉ `System Manager`** có `delete`; vài doctype Sales cho thêm Manager/Purchaser/Accountant. → Tính năng thực chất là **cấp quyền delete cho role vận hành**, không phải chỉ thêm nút.
- Frappe `delete_doc` **đã tự chặn** xóa phiếu đã Submit (docstatus=1) qua `check_permission_and_not_submitted`, nhưng **cho phép** xóa phiếu đã Hủy (docstatus=2) — vi phạm "chỉ nháp".
- `on_trash`/`before_delete` **chạy cả khi `force=True`**, nhưng mọi lệnh xóa lập trình/test đều truyền `ignore_permissions=True` → guard chặn theo `not doc.flags.ignore_permissions` chỉ áp cho lệnh xóa thật của người dùng (REST), không phá test.

## Quyết định thiết kế (đã chốt với người dùng)

1. **Phạm vi:** chỉ doctype submittable ở `docstatus == 0`. Doctype không submittable không đụng.
2. **Chính sách role:** role nào có `create` → được `delete`, **trừ** `SC Customer Portal` và `SupplyCore Auditor` (read-only, kể cả khi có write). Quyền delete **đầy đủ** (không dùng `if_owner`).
3. **Vị trí nút:** cả DocView (chi tiết) **và** DocList (chọn nhiều/xóa từng dòng), làm ngay trong đợt này.

## Kiến trúc — 3 lớp tách bạch

| Lớp | Câu hỏi | Cơ chế | File |
|-----|---------|--------|------|
| **1. JSON permissions** | *Ai* được xóa | Bật `delete:1` cho role có create | 15 file `*/doctype/*/*.json` |
| **2. `before_delete` guard** | Xóa *cái gì* | Chặn nếu `docstatus != 0` | `utils/validators.py` + `hooks.py` |
| **3. Frontend** | Nút hiện *ở đâu* | Gate theo draft + quyền delete | `DocView.vue`, `DocList.vue`, `DataTable.vue` |

### Lớp 1 — Quyền role (backend)

Với mỗi doctype submittable, thêm `"delete": 1` vào block permission của mọi role đang có `"create": 1`, trừ `SC Customer Portal` và `SupplyCore Auditor`. Ma trận cụ thể (role **được thêm** delete):

| Doctype | Role thêm delete |
|---------|------------------|
| Framework Contract | Manager, Accountant |
| Procurement Plan | Manager, Storekeeper, Warehouse Officer |
| Release Order | Manager, Accountant, Purchaser |
| SC Inventory Count Sheet | Manager, Storekeeper, Warehouse Officer |
| SC Investigation Report | Manager |
| SC Material Request | Manager, Storekeeper |
| SC Payment Entry | Accountant |
| SC Purchase Invoice | Manager, Accountant |
| SC Purchase Order | Manager, Accountant, Purchaser |
| SC Purchase Receipt | Manager, Storekeeper, Warehouse Officer |
| SC Quality Inspection | Manager, QC Officer, Storekeeper |
| SC Recall Notice | Manager |
| SC Stock Entry | Manager, Storekeeper, Warehouse Officer |
| SC Stock Reconciliation | Manager |
| SC Transfer Request | Manager, Storekeeper, Warehouse Officer |

6 doctype còn lại (SC Acceptance Record, SC Delivery Note, SC Sales Framework Contract, SC Sales Invoice, SC Sales Order, SC Sales Receipt) đã cấp delete đủ cho các role create → **không đổi**.

Role name viết đầy đủ trong JSON là `SupplyCore Manager`, `SupplyCore Storekeeper`, `SupplyCore Accountant`, `SupplyCore Purchaser`, `Warehouse Officer`, `QC Officer`.

Nguồn sự thật là JSON; cần `bench migrate` để đồng bộ vào DB.

### Lớp 2 — Guard `before_delete`

Một hàm dùng chung `block_non_draft_delete` đặt trong `supplycore/utils/validators.py`, đăng ký cho cả 21 doctype trong `hooks.py doc_events["<dt>"]["before_delete"] = "supplycore.utils.validators.block_non_draft_delete"`. (Khác với `before_cancel` BRU-PAY-001 vốn là method trên từng controller — ở đây dùng 1 hàm hook chung để khỏi sửa 21 controller.)

```python
def block_non_draft_delete(doc, method=None):
    # Lệnh xóa lập trình/test (ignore_permissions) được bỏ qua guard.
    if doc.flags.ignore_permissions:
        return
    if (doc.docstatus or 0) != 0:
        frappe.throw(_("Chỉ xóa được phiếu ở trạng thái Nháp. "
                       "Phiếu đã gửi hoặc đã hủy phải giữ lại."))
```

Chặn cả xóa phiếu **đã hủy (docstatus=2)** mà Frappe mặc định cho phép. Với phiếu đã Submit (docstatus=1) Frappe đã tự chặn ở tầng trên — guard này là lớp phòng thủ thứ hai và thông điệp rõ ràng bằng tiếng Việt.

### Lớp 3a — DocView (màn chi tiết)

Thêm nút "Xóa" (đỏ, icon `trash-2`) vào thanh action trong DocView.vue, **chỉ hiện khi**:

```
doc.docstatus === 0 && !isNew && isSubmittable(doctype) && access.canDoctype(doctype, 'delete')
```

Luồng: bấm → `Confirm` modal ("Xóa vĩnh viễn phiếu nháp này?") → `deleteDoc(doctype, doc.name)` → toast thành công → `router` về trang list của doctype. Bắt lỗi → toast lỗi (thông điệp guard hiện ra nếu vi phạm).

### Lớp 3b — DocList (danh sách)

- **DataTable.vue**: thêm khả năng chọn dòng **opt-in** qua prop mới (vd `:selectable`, `:rowSelectable`, `selectedKeys`), mặc định tắt để **không regress** mọi list view khác đang dùng DataTable. Khi bật: cột checkbox đầu, checkbox "chọn tất cả", emit `update:selected`. Dòng không đủ điều kiện (docstatus != 0) bị disable checkbox.
- **DocList.vue**: chỉ bật selection khi `isSubmittable(doctype) && access.canDoctype(doctype,'delete')`. Query list phải có field `docstatus` để gate per-row (kiểm tra & thêm nếu thiếu). Thanh công cụ hiện nút "Xóa (n)" khi có dòng chọn → `Confirm` → xóa tuần tự bằng `deleteDoc`, gom kết quả, toast tổng kết ("Đã xóa x/n; y lỗi"), `load()` lại danh sách.

## Ảnh hưởng & rủi ro

- **DataTable dùng chung**: bắt buộc opt-in để không đổi hành vi các list khác (StockBalance, WarehouseList, RelatedDocs...). Cần verify lại các consumer sau khi sửa.
- **Access matrix mức doctype**: vì không dùng `if_owner`, nút hiện cho mọi phiếu nháp của doctype mà role có quyền — đúng ý đồ đã chốt.
- **Test cleanup**: guard bỏ qua khi `ignore_permissions=True` → 100% lệnh xóa trong `tests/`, `setup/`, `patches/` không bị ảnh hưởng.

## Vận hành (bắt buộc)

1. `bench --site <site> migrate` — đồng bộ JSON permission vào DB.
2. Trong `frontend/`: `yarn build` (KHÔNG phải `bench build`), rồi hard-refresh trình duyệt (PWA/service worker cache).

## Kiểm thử

- **Backend guard:** unit — xóa doc docstatus 0 (pass), docstatus 1 (Frappe chặn), docstatus 2 (guard chặn); xóa với `ignore_permissions=True` docstatus 2 (pass, không bị guard).
- **Quyền:** với từng role vận hành, `frappe.has_permission(dt,'delete')` = 1 sau migrate; Auditor & Portal = 0.
- **Frontend (thủ công):** nút Xóa chỉ hiện ở phiếu nháp; xóa DocView về list; chọn nhiều + xóa hàng loạt ở DocList; list khác không mọc checkbox.
