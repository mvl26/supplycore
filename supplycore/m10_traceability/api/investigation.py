"""UC-31 — Investigation API: audit trail + anomaly detection.

Read-only audit on SC Stock Ledger Entry + Frappe Version.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, get_datetime, time_diff_in_seconds


# -----------------------------------------------------------------------
# UC-31 step 1-3: audit trail
# -----------------------------------------------------------------------
@frappe.whitelist()
def get_audit_trail(item=None, warehouse=None, start_date=None, end_date=None,
                     user=None, limit=500) -> list:
    """Trả audit trail SLE filtered + IP best-effort từ Activity Log."""
    conds = ["1=1"]
    params = {}
    if item:
        conds.append("sle.item = %(item)s")
        params["item"] = item
    if warehouse:
        conds.append("sle.warehouse = %(wh)s")
        params["wh"] = warehouse
    if start_date:
        conds.append("sle.posting_date >= %(start)s")
        params["start"] = start_date
    if end_date:
        conds.append("sle.posting_date <= %(end)s")
        params["end"] = end_date
    if user:
        conds.append("sle.owner = %(user)s")
        params["user"] = user
    where = " AND ".join(conds)
    rows = frappe.db.sql(f"""
        SELECT sle.name, sle.posting_date, sle.posting_time,
               sle.item, sle.warehouse, sle.batch,
               sle.voucher_type, sle.voucher_no,
               sle.qty_change, sle.balance_qty, sle.valuation_rate,
               sle.is_cancelled, sle.owner AS creator,
               sle.creation, sle.modified, sle.modified_by, sle.remarks
        FROM `tabSC Stock Ledger Entry` sle
        WHERE {where}
        ORDER BY sle.posting_date DESC, sle.creation DESC
        LIMIT %(lim)s
    """, {**params, "lim": int(limit)}, as_dict=True)
    # Annotate IP best-effort qua Activity Log (Login event nearest)
    for r in rows:
        r["ip_address"] = _lookup_ip_for_user_near_time(r["creator"], r["creation"])
        r["posting_date"] = str(r["posting_date"]) if r["posting_date"] else None
        r["creation"] = str(r["creation"]) if r["creation"] else None
        r["modified"] = str(r["modified"]) if r["modified"] else None
    return rows


def _lookup_ip_for_user_near_time(user, ts):
    """Best-effort: tìm Activity Log Login gần thời điểm SLE created."""
    if not user or not ts or user in ("Administrator", "Guest"):
        return None
    try:
        row = frappe.db.sql("""
            SELECT ip_address
            FROM `tabActivity Log`
            WHERE user = %s AND operation = 'Login'
              AND creation <= %s
            ORDER BY creation DESC LIMIT 1
        """, (user, ts))
        return row[0][0] if row else None
    except Exception:
        return None


# -----------------------------------------------------------------------
# UC-31 step 4: so sánh tồn lý thuyết vs thực tế
# -----------------------------------------------------------------------
@frappe.whitelist()
def compare_theoretical_vs_actual(item, warehouse=None, batch=None) -> dict:
    """Sum SLE.qty_change (theoretical). Caller cung cấp actual_qty riêng."""
    conds = ["item = %(item)s", "is_cancelled = 0"]
    params = {"item": item}
    if warehouse:
        conds.append("warehouse = %(wh)s")
        params["wh"] = warehouse
    if batch:
        conds.append("batch = %(batch)s")
        params["batch"] = batch
    where = " AND ".join(conds)
    theoretical = flt(frappe.db.sql(f"""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE {where}
    """, params)[0][0])
    return {
        "theoretical_qty": theoretical,
        "item": item, "warehouse": warehouse, "batch": batch,
    }


# -----------------------------------------------------------------------
# UC-31 step 5: detect anomalies
# -----------------------------------------------------------------------
@frappe.whitelist()
def detect_anomalies(item=None, warehouse=None, start_date=None, end_date=None,
                      user=None, large_qty_threshold=1000) -> list:
    """Apply heuristics → trả list findings (chưa append vào doc)."""
    rows = get_audit_trail(item=item, warehouse=warehouse,
                            start_date=start_date, end_date=end_date,
                            user=user, limit=5000)
    findings = []
    user_neg_count = {}

    for r in rows:
        qty = flt(r.get("qty_change"))
        is_cancelled = int(r.get("is_cancelled") or 0)
        owner = r.get("creator")
        creation = r.get("creation")
        posting_date = r.get("posting_date")
        modified = r.get("modified")

        base = {
            "voucher_type": r.get("voucher_type"),
            "voucher_no": r.get("voucher_no"),
            "voucher_date": r.get("posting_date"),
            "user_suspected": owner,
            "qty_change": qty,
            "balance_after": flt(r.get("balance_qty")),
            "ip_address": r.get("ip_address"),
        }

        # 1. Large Qty Change
        if abs(qty) > flt(large_qty_threshold):
            findings.append({
                **base,
                "finding_type": "Large Qty Change",
                "severity": "Medium" if abs(qty) <= flt(large_qty_threshold) * 5 else "High",
                "evidence": f"|qty_change|={abs(qty)} > threshold {large_qty_threshold}",
            })

        # 2. Off-Hours (creation outside 06:00-22:00 UTC+7 — heuristic)
        if creation:
            try:
                hour = get_datetime(creation).hour
                if hour < 6 or hour >= 22:
                    findings.append({
                        **base,
                        "finding_type": "Off-Hours",
                        "severity": "Low",
                        "evidence": f"creation hour={hour} (outside 06-22)",
                    })
            except Exception:
                pass

        # 3. Cancelled Without Reason
        if is_cancelled and not (r.get("remarks") or "").strip():
            findings.append({
                **base,
                "finding_type": "Cancelled Without Reason",
                "severity": "High",
                "evidence": "is_cancelled=1, remarks rỗng",
            })

        # 4. Modified After Submit (modified > creation + 1s and modified_by != creator)
        try:
            if creation and modified:
                delta = time_diff_in_seconds(modified, creation)
                if delta and delta > 60 and r.get("modified_by") and r.get("modified_by") != owner:
                    findings.append({
                        **base,
                        "finding_type": "Modified After Submit",
                        "severity": "High",
                        "evidence": f"modified_by={r.get('modified_by')} ≠ creator={owner}; Δ={int(delta)}s",
                    })
        except Exception:
            pass

        # 5. Backdated Entry (posting_date < creation - 7 days)
        try:
            if creation and posting_date:
                creation_d = getdate(creation.split(" ")[0] if isinstance(creation, str) else creation)
                pd = getdate(posting_date)
                if (creation_d - pd).days > 7:
                    findings.append({
                        **base,
                        "finding_type": "Backdated Entry",
                        "severity": "High",
                        "evidence": f"posting_date={pd}, created={creation_d}, Δ={(creation_d - pd).days}d",
                    })
        except Exception:
            pass

        # 6. Accumulate negative SLE per user for Repeated User Pattern
        if qty < 0 and owner:
            user_neg_count[owner] = user_neg_count.get(owner, 0) + 1

    # 7. Repeated User Pattern (>10 SLE âm cùng user)
    for u, n in user_neg_count.items():
        if n > 10:
            findings.append({
                "finding_type": "Repeated User Pattern",
                "severity": "Medium",
                "user_suspected": u,
                "voucher_type": "(aggregate)",
                "voucher_no": f"{n} negative SLE",
                "evidence": f"User {u} có {n} SLE âm trong period",
            })

    # 8. Balance Mismatch — replay cumulative theo (item, warehouse, batch)
    findings.extend(_detect_balance_mismatch(item, warehouse, start_date, end_date))

    return findings


def _detect_balance_mismatch(item, warehouse, start_date, end_date):
    """Replay SLE per (item, warehouse, batch) sorted by time và so balance_qty.
    Phát hiện row có balance_qty không khớp cumulative."""
    if not item:
        return []
    conds = ["item = %(item)s", "is_cancelled = 0"]
    params = {"item": item}
    if warehouse:
        conds.append("warehouse = %(wh)s")
        params["wh"] = warehouse
    if start_date:
        conds.append("posting_date >= %(start)s")
        params["start"] = start_date
    if end_date:
        conds.append("posting_date <= %(end)s")
        params["end"] = end_date
    where = " AND ".join(conds)
    rows = frappe.db.sql(f"""
        SELECT name, posting_date, posting_time, warehouse, batch,
               qty_change, balance_qty, voucher_type, voucher_no,
               owner, creation
        FROM `tabSC Stock Ledger Entry`
        WHERE {where}
        ORDER BY warehouse, COALESCE(batch, ''), posting_date, posting_time, creation
    """, params, as_dict=True)

    mismatches = []
    running = {}
    for r in rows:
        key = (r["warehouse"], r["batch"] or "")
        running[key] = running.get(key, 0) + flt(r["qty_change"])
        expected = running[key]
        recorded = flt(r["balance_qty"])
        if abs(expected - recorded) > 0.01:
            mismatches.append({
                "finding_type": "Balance Mismatch",
                "severity": "Critical",
                "voucher_type": r["voucher_type"],
                "voucher_no": r["voucher_no"],
                "voucher_date": str(r["posting_date"]),
                "user_suspected": r["owner"],
                "qty_change": flt(r["qty_change"]),
                "balance_after": recorded,
                "evidence": f"expected balance={expected:.2f} ≠ recorded={recorded:.2f} "
                             f"@ SLE {r['name']}",
            })
    return mismatches


# -----------------------------------------------------------------------
# UC-31 ngoại lệ: verify audit integrity
# -----------------------------------------------------------------------
@frappe.whitelist()
def verify_audit_integrity(doctype, docname) -> dict:
    """Đếm Frappe Version rows cho 1 document.
    Trả expected_min=0 (mọi doc có create event = 1 version) và actual_count.
    Spec: 'audit log không thể sửa' — Frappe Version table không bị xóa
    bởi user thông thường."""
    count = frappe.db.count("Version", filters={
        "ref_doctype": doctype, "docname": docname
    })
    earliest = frappe.db.get_value("Version",
        {"ref_doctype": doctype, "docname": docname},
        "creation", order_by="creation ASC")
    latest = frappe.db.get_value("Version",
        {"ref_doctype": doctype, "docname": docname},
        "creation", order_by="creation DESC")
    return {
        "doctype": doctype, "docname": docname,
        "version_count": count,
        "earliest_version_at": str(earliest) if earliest else None,
        "latest_version_at": str(latest) if latest else None,
    }
