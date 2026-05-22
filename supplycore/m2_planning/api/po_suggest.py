"""M2 → M1 wiring: suggest+tạo SC Purchase Order draft từ SC Material Request đã approved.

Endpoint:
    POST /api/method/supplycore.m2_planning.api.po_suggest.suggest_po_from_mr
    payload: {"mr_name": "SC-MR-2026-####"}

Logic chọn HĐK cho mỗi dòng MR:
    - Dòng ĐÃ gán framework_contract (tạo MR từ 1 HĐK, hoặc user chọn tay):
      BẮT BUỘC dùng đúng HĐK đó. Nếu HĐK không hợp lệ/không đủ tồn → unmatched
      (KHÔNG tự đổi sang HĐK khác — tránh PO lệch yêu cầu).
    - Dòng CHƯA gán framework_contract: suggest HĐK Active có đơn giá thấp nhất
      (FC Item.item_code == item, remaining_qty ≥ qty).
Sau đó:
    - Group MR items theo (supplier, framework_contract) → 1 draft PO/group.
    - Validate ΣPO ≤ FC.remaining_value (BR-M1-03 / SC-E002).
"""

import frappe
from frappe import _
from frappe.utils import flt, today, getdate, add_days


@frappe.whitelist()
def suggest_po_from_mr(mr_name: str, auto_create: int = 0) -> dict:
    """Trả về plan tạo PO từ MR. Nếu auto_create=1 thì insert luôn draft PO.

    Returns:
        {
          "mr": "SC-MR-...",
          "groups": [
            {"supplier": "...", "framework_contract": "SC-FC-...",
             "items": [{...}], "subtotal": float, "po_name": "SC-PO-..." (if created)}
          ],
          "unmatched_items": [{"item": "...", "qty": float, "reason": "..."}],
          "created_pos": ["SC-PO-...", ...]
        }
    """
    mr = frappe.get_doc("SC Material Request", mr_name)
    if mr.docstatus != 1:
        frappe.throw(_("MR {0} chưa submit").format(mr_name), title="SC-E-MR")

    # Group MR items theo best (supplier, FC). Track FC remaining qty/value
    # in-memory để tránh over-allocate khi MR có nhiều row cùng item.
    groups: dict = {}
    unmatched = []
    # Cache: { fc_name: { item_code: remaining_qty_left } }
    fc_qty_cache: dict = {}

    if not mr.items:
        frappe.throw(_("MR {0} không có dòng items nào").format(mr_name), title="SC-E-MR-EMPTY")

    for row in mr.items:
        # 2 nhánh theo yêu cầu nghiệp vụ:
        #  - Dòng MR ĐÃ gán HĐK (tạo MR từ 1 HĐK, hoặc user chọn tay) →
        #    BẮT BUỘC theo đúng HĐK đó, không tự đổi sang HĐK/NCC khác.
        #  - Dòng MR CHƯA gán HĐK → suggest HĐK Active có đơn giá rẻ nhất.
        if row.framework_contract:
            match = _validate_specific_fc(
                row.framework_contract, row.item, flt(row.qty), fc_qty_cache)
            reason_if_none = _(
                "HĐK {0} đã chọn không dùng được cho vật tư này "
                "(hết hiệu lực / không chứa vật tư / không đủ tồn). "
                "Điều chỉnh HĐK hoặc số lượng trên dòng MR."
            ).format(row.framework_contract)
        else:
            match = _find_best_fc_for_item(row.item, flt(row.qty), fc_qty_cache)
            reason_if_none = _("Không có HĐK Active phù hợp với vật tư + số lượng còn lại")
        if not match:
            unmatched.append({
                "mr_item": row.name,
                "row_idx": row.idx,
                "item": row.item,
                "qty": flt(row.qty),
                "uom": row.uom,
                "reason": reason_if_none,
            })
            continue
        # Cập nhật cache: trừ qty đã claim
        fc_qty_cache.setdefault(match["fc"], {})
        fc_qty_cache[match["fc"]][row.item] = match["remaining_qty"] - flt(row.qty)

        key = (match["supplier"], match["fc"])
        g = groups.setdefault(key, {
            "supplier": match["supplier"],
            "framework_contract": match["fc"],
            "items": [],
            "subtotal": 0,
        })
        amount = flt(row.qty) * flt(match["unit_price"])
        g["items"].append({
            "mr_item": row.name,
            "row_idx": row.idx,
            "item": row.item,
            "qty": flt(row.qty),
            "uom": row.uom,
            "rate": flt(match["unit_price"]),
            "amount": amount,
            "warehouse": mr.warehouse or "",
            "schedule_date": row.schedule_date or mr.schedule_date,
        })
        g["subtotal"] += amount

    # Validate ΣPO theo FC.remaining_value
    fc_subtotals = {}
    for (sup, fc), g in groups.items():
        fc_subtotals[fc] = fc_subtotals.get(fc, 0) + g["subtotal"]
    for fc, total in fc_subtotals.items():
        rem = flt(frappe.db.get_value("Framework Contract", fc, "remaining_value"))
        if total > rem + 1:  # +1 buffer chống lỗi rounding
            frappe.throw(_("HĐK {0}: tổng PO đề xuất ({1}) vượt remaining_value ({2})").format(
                fc, frappe.format(total, {"fieldtype": "Currency"}),
                frappe.format(rem, {"fieldtype": "Currency"})),
                title="SC-E002 FC_BUDGET")

    created = []
    if int(auto_create or 0) == 1:
        for (sup, fc), g in groups.items():
            po = _create_draft_po(mr, sup, fc, g["items"])
            g["po_name"] = po
            created.append(po)
        if created:
            mr.db_set("status", "Ordered")

    # === Audit: đảm bảo KHÔNG mất dòng nào ===
    mr_total = len(mr.items)
    grouped_total = sum(len(g["items"]) for g in groups.values())
    unmatched_total = len(unmatched)
    if grouped_total + unmatched_total != mr_total:
        frappe.log_error(
            f"PO suggest mismatch: MR {mr_name} có {mr_total} items, "
            f"grouped={grouped_total}, unmatched={unmatched_total}",
            title="SC-E-MR-PO-ROW-LOSS",
        )
        frappe.throw(_(
            "SC-E-MR-PO-ROW-LOSS: MR {0} có {1} dòng nhưng chỉ xử lý được {2} "
            "(group {3} + unmatched {4}). Vui lòng liên hệ admin."
        ).format(mr_name, mr_total, grouped_total + unmatched_total,
                  grouped_total, unmatched_total))

    return {
        "mr": mr_name,
        "summary": {
            "mr_items": mr_total,
            "grouped_items": grouped_total,
            "unmatched_items": unmatched_total,
            "pos_created": len(created),
            "all_accounted": grouped_total + unmatched_total == mr_total,
        },
        "groups": [
            {"supplier": k[0], "framework_contract": k[1], **v}
            for k, v in groups.items()
        ],
        "unmatched_items": unmatched,
        "created_pos": created,
    }


def _validate_specific_fc(fc_name: str, item: str, qty: float,
                           fc_qty_cache: dict = None) -> dict:
    """Kiểm tra FC user đã chọn trên dòng MR có dùng được cho item+qty không.

    Trả {supplier, fc, unit_price, fc_item_name, remaining_qty} nếu FC:
    - docstatus=1, status=Active, còn hiệu lực (valid_to >= hôm nay)
    - có FC Item khớp item_code
    - remaining_qty (đã trừ phần claim trong cùng MR) >= qty
    Ngược lại trả None để caller fallback sang FC khác.
    """
    if not fc_name:
        return None
    rows = frappe.db.sql("""
        SELECT fc.name AS fc, fc.supplier, fci.name AS fci_name,
               fci.unit_price, fci.remaining_qty
        FROM `tabFramework Contract` fc
        JOIN `tabFC Item` fci ON fci.parent = fc.name
        WHERE fc.name = %s
          AND fc.docstatus = 1
          AND fc.status = 'Active'
          AND fc.valid_to >= CURDATE()
          AND fci.item_code = %s
    """, (fc_name, item), as_dict=True)
    fc_qty_cache = fc_qty_cache or {}
    for r in rows:
        effective_remain = flt(r.remaining_qty)
        if r.fc in fc_qty_cache and item in fc_qty_cache[r.fc]:
            effective_remain = fc_qty_cache[r.fc][item]
        if effective_remain >= qty:
            return {"supplier": r.supplier, "fc": r.fc,
                    "unit_price": flt(r.unit_price), "fc_item_name": r.fci_name,
                    "remaining_qty": effective_remain}
    return None


def _find_best_fc_for_item(item: str, qty: float, fc_qty_cache: dict = None) -> dict:
    """Trả {supplier, fc, unit_price, fc_item_name, remaining_qty} cho FC Active
    rẻ nhất phù hợp. fc_qty_cache (optional) chứa qty đã claim trong cùng MR
    để tránh over-allocate khi MR có nhiều row cùng item.
    """
    rows = frappe.db.sql("""
        SELECT fc.name AS fc, fc.supplier, fci.name AS fci_name,
               fci.unit_price, fci.remaining_qty
        FROM `tabFramework Contract` fc
        JOIN `tabFC Item` fci ON fci.parent = fc.name
        WHERE fc.docstatus = 1
          AND fc.status = 'Active'
          AND fc.valid_to >= CURDATE()
          AND fci.item_code = %s
        ORDER BY fci.unit_price ASC
    """, (item,), as_dict=True)
    fc_qty_cache = fc_qty_cache or {}
    for r in rows:
        effective_remain = flt(r.remaining_qty)
        # Trừ phần đã claim trong cùng MR
        if r.fc in fc_qty_cache and item in fc_qty_cache[r.fc]:
            effective_remain = fc_qty_cache[r.fc][item]
        if effective_remain >= qty:
            return {"supplier": r.supplier, "fc": r.fc,
                    "unit_price": flt(r.unit_price), "fc_item_name": r.fci_name,
                    "remaining_qty": effective_remain}
    return None


def _create_draft_po(mr, supplier: str, fc: str, items: list) -> str:
    """Tạo SC Purchase Order draft. Không submit — user review rồi submit."""
    po = frappe.new_doc("SC Purchase Order")
    po.supplier = supplier
    po.framework_contract = fc
    po.material_request = mr.name
    po.transaction_date = today()
    po.schedule_date = add_days(today(), 14)  # default 14d delivery
    po.remarks = f"Tự tạo từ MR {mr.name}"
    for it in items:
        po.append("items", {
            "item": it["item"],
            "qty": it["qty"],
            "uom": it["uom"],
            "rate": it["rate"],
            "amount": it["amount"],
            "warehouse": it["warehouse"] or mr.warehouse,
            "schedule_date": it.get("schedule_date") or po.schedule_date,
        })
    po.flags.ignore_permissions = True
    po.insert()
    return po.name


@frappe.whitelist()
def get_po_suggestion_preview(mr_name: str) -> dict:
    """Alias không auto-create — UI hiển thị preview."""
    return suggest_po_from_mr(mr_name, auto_create=0)
