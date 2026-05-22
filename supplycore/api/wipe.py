"""Destructive wipe helpers — chỉ chạy thủ công khi user uỷ quyền.

KHÔNG đăng ký vào hooks. Chỉ gọi qua `bench execute supplycore.api.wipe.<func>`.
"""

import frappe


# Mapping parent doctype → child table doctypes
PARENT_CHILDREN = {
    "SC Purchase Receipt": ["SC Purchase Receipt Item"],
    "SC Purchase Order":   ["SC Purchase Order Item"],
    "SC Stock Entry":      ["SC Stock Entry Item"],
}

# Bảng leaf không có child
LEAVES = ["SC Stock Ledger Entry", "SC Batch"]

# M1/M2/M3/M6/M7 transactional doctypes — child auto-detect qua frappe.get_meta()
MODULE_TRANSACTIONALS = (
    # M1 Hợp đồng
    "Framework Contract",
    # M2 Kế hoạch & Mua (PO đã wipe ở wipe_transactions)
    "SC Material Request",
    # M3 Tiếp nhận (PR đã wipe)
    "SC Quality Inspection",
    # M6 Chuyển kho (SE đã wipe)
    "SC Transfer Request",
    # M7 Cấp phát
    "SC Patient Dispensing",
    "SC Dispensing Request",
)

# M8/M9/M10 transactional doctypes
MODULE_TRANSACTIONALS_8_10 = (
    # M8 Kế toán
    "SC Purchase Invoice",
    "SC Payment Entry",
    "SC GL Entry",
    # M9 Kiểm kê
    "SC Stock Reconciliation",
    "SC Inventory Count Sheet",
    # M10 Truy xuất & Thu hồi
    "SC Recall Notice",
    "SC Investigation Report",
)


def count_targets():
    """Đếm số record các doctype giao dịch sẽ bị xóa."""
    out = {}
    for dt in list(PARENT_CHILDREN.keys()) + LEAVES:
        try:
            out[dt] = frappe.db.count(dt)
        except Exception as e:
            out[dt] = f"err: {e}"
    return out


def count_masters():
    """Đếm master — verify KHÔNG bị động sau khi wipe."""
    out = {}
    for dt in ("SC Item", "SC Supplier", "SC Warehouse", "SC Patient", "SC UOM",
               "SC Department", "SC Item Group"):
        try:
            out[dt] = frappe.db.count(dt)
        except Exception:
            out[dt] = 0
    return out


def wipe_transactions(confirm: str = ""):
    """Xóa toàn bộ PR/PO/SE/Batch/SLE bằng SQL trực tiếp.

    Yêu cầu confirm == 'YES-WIPE-ALL-TRANSACTIONS'.

    Bypass:
      - docstatus check (xóa cả submitted)
      - on_cancel/on_trash hooks (không sinh SLE ngược)
      - link integrity validation (frappe soft links)

    Trả về dict {before, after, masters_before, masters_after}.
    """
    if confirm != "YES-WIPE-ALL-TRANSACTIONS":
        return {"error": "Pass confirm='YES-WIPE-ALL-TRANSACTIONS' to proceed."}

    before = count_targets()
    masters_before = count_masters()

    # 1) Xóa SLE trước — leaf, không link ngoài
    frappe.db.sql("DELETE FROM `tabSC Stock Ledger Entry`")

    # 2) Xóa parent + child tables (SE, PR, PO)
    for parent_dt, child_dts in PARENT_CHILDREN.items():
        for child_dt in child_dts:
            frappe.db.sql(
                f"DELETE FROM `tab{child_dt}` WHERE parenttype = %s",
                (parent_dt,),
            )
        frappe.db.sql(f"DELETE FROM `tab{parent_dt}`")

    # 3) Xóa Batch — sau cùng vì nhiều doc khác có thể ref tới Batch
    frappe.db.sql("DELETE FROM `tabSC Batch`")

    # 4) Dọn naming series counters để chuỗi mới bắt đầu từ 0
    series_to_reset = (
        "SC-PR-%", "SC-PO-%", "SC-SE-%", "SC-BAT-%", "SC-SLE-%",
    )
    for pat in series_to_reset:
        frappe.db.sql(
            "DELETE FROM `tabSeries` WHERE name LIKE %s",
            (pat,),
        )

    frappe.db.commit()

    after = count_targets()
    masters_after = count_masters()
    return {
        "before": before,
        "after": after,
        "masters_before": masters_before,
        "masters_after": masters_after,
        "masters_unchanged": masters_before == masters_after,
    }


def count_modules():
    """Đếm record các transactional M1/M2/M3/M6/M7."""
    out = {}
    for dt in MODULE_TRANSACTIONALS:
        try:
            out[dt] = frappe.db.count(dt)
        except Exception as e:
            out[dt] = f"err: {str(e)[:60]}"
    return out


def count_modules_8_10():
    """Đếm record các transactional M8/M9/M10."""
    out = {}
    for dt in MODULE_TRANSACTIONALS_8_10:
        try:
            out[dt] = frappe.db.count(dt)
        except Exception as e:
            out[dt] = f"err: {str(e)[:60]}"
    return out


def _child_tables_of(parent_dt: str):
    """Trả về list child doctype name (Table fields) của 1 doctype."""
    try:
        meta = frappe.get_meta(parent_dt)
    except Exception:
        return []
    return [df.options for df in meta.fields
            if df.fieldtype in ("Table", "Table MultiSelect") and df.options]


def wipe_modules(confirm: str = ""):
    """Xóa transactional M1/M2/M3/M6/M7 (giữ nguyên master).

    Yêu cầu confirm == 'YES-WIPE-MODULES-1-2-3-6-7'.

    Tự dò child tables qua frappe.get_meta. Bypass docstatus + hook.
    """
    if confirm != "YES-WIPE-MODULES-1-2-3-6-7":
        return {"error": "Pass confirm='YES-WIPE-MODULES-1-2-3-6-7' to proceed."}

    before = count_modules()
    masters_before = count_masters()
    deleted_tables = {}

    for parent_dt in MODULE_TRANSACTIONALS:
        # Kiểm tra doctype tồn tại trong DB
        if not frappe.db.exists("DocType", parent_dt):
            deleted_tables[parent_dt] = "doctype not installed"
            continue
        # Child tables (xóa bằng parenttype filter để không động data khác)
        children = _child_tables_of(parent_dt)
        for child_dt in children:
            try:
                frappe.db.sql(
                    f"DELETE FROM `tab{child_dt}` WHERE parenttype = %s",
                    (parent_dt,),
                )
            except Exception as e:
                deleted_tables.setdefault("errors", []).append(
                    f"{child_dt}: {str(e)[:60]}")
        # Parent table
        try:
            frappe.db.sql(f"DELETE FROM `tab{parent_dt}`")
            deleted_tables[parent_dt] = f"OK (children: {children})"
        except Exception as e:
            deleted_tables[parent_dt] = f"err: {str(e)[:60]}"

    # Naming series reset cho các series có thể có
    series_to_reset = (
        "FC-%", "SC-MR-%", "SC-QI-%", "SC-TR-%", "SC-PD-%", "SC-DR-%",
    )
    for pat in series_to_reset:
        try:
            frappe.db.sql("DELETE FROM `tabSeries` WHERE name LIKE %s", (pat,))
        except Exception:
            pass

    frappe.db.commit()

    after = count_modules()
    masters_after = count_masters()
    return {
        "before": before,
        "after": after,
        "masters_before": masters_before,
        "masters_after": masters_after,
        "masters_unchanged": masters_before == masters_after,
        "deleted_tables": deleted_tables,
    }


def wipe_modules_8_10(confirm: str = ""):
    """Xóa transactional M8/M9/M10 (giữ nguyên master).

    Yêu cầu confirm == 'YES-WIPE-MODULES-8-9-10'.

    Tự dò child tables qua frappe.get_meta. Bypass docstatus + hook.
    """
    if confirm != "YES-WIPE-MODULES-8-9-10":
        return {"error": "Pass confirm='YES-WIPE-MODULES-8-9-10' to proceed."}

    before = count_modules_8_10()
    masters_before = count_masters()
    deleted_tables = {}

    for parent_dt in MODULE_TRANSACTIONALS_8_10:
        if not frappe.db.exists("DocType", parent_dt):
            deleted_tables[parent_dt] = "doctype not installed"
            continue
        children = _child_tables_of(parent_dt)
        for child_dt in children:
            try:
                frappe.db.sql(
                    f"DELETE FROM `tab{child_dt}` WHERE parenttype = %s",
                    (parent_dt,),
                )
            except Exception as e:
                deleted_tables.setdefault("errors", []).append(
                    f"{child_dt}: {str(e)[:60]}")
        try:
            frappe.db.sql(f"DELETE FROM `tab{parent_dt}`")
            deleted_tables[parent_dt] = f"OK (children: {children})"
        except Exception as e:
            deleted_tables[parent_dt] = f"err: {str(e)[:60]}"

    # Naming series reset
    series_to_reset = (
        "SC-PI-%", "SC-PE-%", "SC-GL-%",
        "SC-SR-%", "SC-ICS-%",
        "SC-RCL-%", "SC-INV-%",
    )
    for pat in series_to_reset:
        try:
            frappe.db.sql("DELETE FROM `tabSeries` WHERE name LIKE %s", (pat,))
        except Exception:
            pass

    frappe.db.commit()

    after = count_modules_8_10()
    masters_after = count_masters()
    return {
        "before": before,
        "after": after,
        "masters_before": masters_before,
        "masters_after": masters_after,
        "masters_unchanged": masters_before == masters_after,
        "deleted_tables": deleted_tables,
    }
