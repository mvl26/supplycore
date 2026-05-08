# M6 — Luân chuyển nội bộ

Module quản lý **SC Transfer Request** (phiếu yêu cầu chuyển kho có phê duyệt) + tự sinh **SC Stock Entry Material Transfer** (M4 đã có).

> ⚠ **v0.2 — chỉ Frappe**: dùng SC Stock Entry không ERPNext.

## DocTypes

| DocType | Loại | Mô tả |
|---|---|---|
| `SC Transfer Request` | Submittable | Phiếu yêu cầu chuyển kho — link kho nguồn, kho đích, items |
| `SC Transfer Request Item` | Child | Dòng VT yêu cầu — requested_qty, approved_qty, transferred_qty |

**Master phụ thuộc:** `SC Item` · `SC UOM` · `SC Warehouse` · `SC Department` · `SC Batch` · `SC Stock Entry` (sinh ra)

## Naming series

- `SC-TR-YYYY-#####` — SC Transfer Request

## Luồng hoạt động

```
[1] SC-WARD-STAFF (khoa) hoặc SC-STOREKEEPER tạo SC Transfer Request
        │ chọn from_warehouse (Sub) → to_warehouse (Department)
        │ thêm items: requested_qty
        │ Python validate:
        │   - kho nguồn ≠ kho đích, không group
        │   - dates hợp lệ
        │   - snapshot available_at_source từ SC SLE
        │   - auto-detect cross-tier → requires_manager_approval=1
        │
[2] Submit (docstatus=1)
        │ status = Approved
        │ approved_by = current user, approved_at = now
        │ Validate: approved_qty ≤ available_at_source (else throw SC-E005)
        │
[3] Click "Tạo Stock Entry" → SC TR.make_stock_entry()
        │ Tạo SC Stock Entry Material Transfer draft
        │   - from_warehouse / to_warehouse
        │   - items: item, approved_qty, batch (FEFO sẽ pick nếu rỗng)
        │   - transfer_request link ngược về TR
        │ TR.status = "In Transit"
        │ TR.stock_entry = SE name
        │
[4] SC Stock Entry validate
        │ M5 FEFO check: nếu source warehouse có batch gần hết hạn hơn → throw
        │ M4 bin consistency check
        │
[5] SC Stock Entry submit
        │ Tạo 2 SC Stock Ledger Entry: -qty (from) + +qty (to)
        │ Hook _notify_linked_transfer_request("submit"):
        │   - update transferred_qty per item
        │   - TR.status = "Received"
        │
[5'] SC Stock Entry cancel
        │ Insert SLE đối ứng + đánh dấu is_cancelled
        │ Hook _notify_linked_transfer_request("cancel"):
        │   - reset transferred_qty = 0
        │   - TR.status revert "Approved", clear stock_entry link
```

## Validate quan trọng

| Rule | Lỗi |
|---|---|
| `from_warehouse == to_warehouse` | "Kho nguồn và kho đích phải khác nhau" |
| `from/to_warehouse.disabled` | "Warehouse đang disabled" |
| `from/to_warehouse.is_group` | "Group warehouse không thể chứa stock" |
| `required_by < request_date` | "Ngày cần phải sau ngày yêu cầu" |
| `approved_qty > available_at_source` | SC-E005 STOCK_INSUFFICIENT |
| Cross-tier (Department ↔ Sub/Main) | `requires_manager_approval = 1` (advisory) |

## Coverage Phase 1

| BR / UC | Status |
|---|---|
| UC-18 Chuyển kho nội bộ với phê duyệt | ✓ TR submit = approval; cross-tier auto detect |
| UC-19 Stock Reconciliation | ⚠ Defer M9 Kiểm kê |
| Phê duyệt theo cấp Manager | ✓ requires_manager_approval flag (workflow chính thức defer) |
| In phiếu chuyển kho | ⚠ Print format defer |

## Hooks

- **SC Stock Entry on_submit/cancel** → `update_tr_on_se_submit/cancel` đồng bộ TR.status + transferred_qty
- Field `transfer_request` trên SC Stock Entry là Link 2 chiều với SC TR

## Permissions (RBAC)

| Role | Read | Write | Submit | Cancel | Notes |
|---|---|---|---|---|---|
| System Manager | ✓ | ✓ | ✓ | ✓ | full |
| SupplyCore Manager | ✓ | ✓ | ✓ | ✓ | approve cross-tier |
| SupplyCore Storekeeper | ✓ | ✓ | ✓ | — | tạo + submit nội bộ tier |
| Warehouse Officer | ✓ | ✓ | ✓ | — | cùng SK |
| SupplyCore Ward Staff | ✓ | ✓ | ✓ | — | tạo TR yêu cầu cho khoa |
| Pharmacy Officer | ✓ | ✓ | — | — | tạo draft, MGR submit |
| SupplyCore Accountant | ✓ | — | — | — | xem audit |

## Vận hành

```
/app/sc-transfer-request/new
  → chọn from_warehouse (vd Kho Vật tư tiêu hao)
  → chọn to_warehouse (vd Kho Khoa Cấp cứu)
  → thêm items với requested_qty
  → save → submit → status = Approved
  → click "Tạo Stock Entry" → mở SE draft
  → thủ kho submit SE → tồn kho chuyển + TR.status = Received
```

## Còn lại defer

1. Frappe Workflow chính thức (Pending Approval → Manager → Approved)
2. Print format phiếu chuyển kho PDF
3. Auto-tạo TR từ alert tồn kho khoa thấp (M11)
4. SC Stock Reconciliation cho M9 (điều chỉnh tồn kho sau kiểm kê)

## Integration với module khác

**Incoming events (module này nhận trigger từ):**
- Khoa request bổ sung (UI tạo TR manual)
- M11 low_stock alert có thể trigger TR auto (Phase 1.1+)

**Outgoing events (module này trigger / cung cấp data cho):**
- TR Approved → make_stock_entry() → SC Stock Entry Material Transfer (draft)
- SE submit → 2 SLE rows ±qty (M4)
- TR.status=Received khi SE submitted

Xem [`FLOW.md`](../../FLOW.md) cho sơ đồ tổng thể.
