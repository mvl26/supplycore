"""Finalize seed E2E: duyệt MR còn Pending + xếp hàng lên kệ (putaway).

Sau khi chạy seed_10_full_flow, các MR đang ở status Pending (đã submit nhưng
chưa được Manager Duyệt YCMH theo UC-07) và 42 SLE +qty (PR + SE Material
Transfer) chưa có bin_location. Script này xử lý cả 2:

1. **MR approval** — gọi `mr.approve()` để chuyển Pending → Approved
2. **Putaway** — gán `bin_location` round-robin cho SLE chưa xếp kệ ở
   `Kho Trung chuyển` (PR) + `Kho Giao hàng` (SE)
3. **Recompute bin occupancy** — cập nhật `current_qty` + `status` cho mọi bin

Usage:
    bench --site supplycore execute supplycore.setup.seed_10_finalize.run
"""

import frappe
from frappe.utils import flt


WAREHOUSES_TO_PUTAWAY = ["Kho Trung chuyển", "Kho Giao hàng"]


def run() -> dict:
    result = {
        "mrs_approved": [],
        "mrs_skipped": [],
        "putaway_assigned": 0,
        "bins_used": {},
        "bins_recomputed": 0,
        "errors": [],
    }

    _approve_pending_mrs(result)
    _assign_putaway_bins(result)
    _recompute_bin_occupancy(result)

    frappe.db.commit()
    result["summary"] = {
        "mrs_approved": len(result["mrs_approved"]),
        "mrs_skipped": len(result["mrs_skipped"]),
        "putaway_assigned": result["putaway_assigned"],
        "bins_used": result["bins_used"],
        "bins_recomputed": result["bins_recomputed"],
        "errors": len(result["errors"]),
    }
    return result


# =====================================================================
# 1. Duyệt MR Pending (UC-07 bước 5)
# =====================================================================
def _approve_pending_mrs(result):
    pending = frappe.get_all(
        "SC Material Request",
        filters={"docstatus": 1, "status": "Pending"},
        pluck="name",
    )
    for mr_name in pending:
        try:
            mr = frappe.get_doc("SC Material Request", mr_name)
            mr.flags.ignore_permissions = True
            mr.approve()
            result["mrs_approved"].append(mr_name)
        except Exception as e:
            result["errors"].append({
                "stage": "mr_approve", "mr": mr_name, "error": str(e)[:200],
            })
            frappe.log_error(message=f"MR approve {mr_name}: {str(e)[:500]}",
                              title="seed_10_finalize mr")

    # MR đã Approved sẵn → skip
    already_approved = frappe.db.count(
        "SC Material Request", {"docstatus": 1, "status": "Approved"},
    )
    result["mrs_skipped"].append({"already_approved": already_approved})


# =====================================================================
# 2. Xếp hàng lên kệ — gán bin_location round-robin
# =====================================================================
def _assign_putaway_bins(result):
    # Cache bins per warehouse
    bins_by_wh = {}
    for wh in WAREHOUSES_TO_PUTAWAY:
        rows = frappe.get_all(
            "Bin Location",
            filters={"warehouse": wh, "enabled": ["!=", 0],
                      "is_quarantine": 0},
            fields=["name", "bin_code"],
            order_by="bin_code",
        )
        if not rows:
            # Fallback: include disabled-bins-by-default (enabled=NULL/0 are still usable)
            rows = frappe.get_all(
                "Bin Location",
                filters={"warehouse": wh, "is_quarantine": 0},
                fields=["name", "bin_code"],
                order_by="bin_code",
            )
        bins_by_wh[wh] = rows
        if not rows:
            result["errors"].append({
                "stage": "putaway", "warehouse": wh,
                "error": "Không có Bin Location nào ở kho này",
            })

    # Lấy SLE chưa có bin_location, qty_change > 0
    sles = frappe.db.sql("""
        SELECT name, item, warehouse, batch, voucher_type, voucher_no
        FROM `tabSC Stock Ledger Entry`
        WHERE warehouse IN %(whs)s
          AND qty_change > 0
          AND is_cancelled = 0
          AND (bin_location IS NULL OR bin_location = '')
        ORDER BY warehouse, item, posting_date, creation
    """, {"whs": tuple(WAREHOUSES_TO_PUTAWAY)}, as_dict=True)

    # Group theo (warehouse, item) để cùng item đi cùng 1 bin (gọn gàng)
    item_bin_map = {}   # (wh, item) → bin
    rr_idx = {wh: 0 for wh in WAREHOUSES_TO_PUTAWAY}
    counts = {}

    for sle in sles:
        wh = sle.warehouse
        bins = bins_by_wh.get(wh) or []
        if not bins:
            continue

        key = (wh, sle.item)
        if key not in item_bin_map:
            item_bin_map[key] = bins[rr_idx[wh] % len(bins)].name
            rr_idx[wh] += 1

        bin_name = item_bin_map[key]
        try:
            frappe.db.sql("""
                UPDATE `tabSC Stock Ledger Entry`
                SET bin_location = %s
                WHERE name = %s
            """, (bin_name, sle.name))
            result["putaway_assigned"] += 1
            counts[bin_name] = counts.get(bin_name, 0) + 1
        except Exception as e:
            result["errors"].append({
                "stage": "putaway_update", "sle": sle.name,
                "error": str(e)[:200],
            })

    result["bins_used"] = counts


# =====================================================================
# 3. Recompute Bin Location occupancy
# =====================================================================
def _recompute_bin_occupancy(result):
    bins = frappe.get_all("Bin Location",
        filters={"warehouse": ["in", WAREHOUSES_TO_PUTAWAY]},
        pluck="name")
    for b in bins:
        try:
            doc = frappe.get_doc("Bin Location", b)
            doc.recompute_occupancy()
            result["bins_recomputed"] += 1
        except Exception as e:
            result["errors"].append({
                "stage": "bin_recompute", "bin": b,
                "error": str(e)[:200],
            })
