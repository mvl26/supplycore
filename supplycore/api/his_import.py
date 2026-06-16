"""Nhập phiếu chuyển kho tự động từ phiếu HIS — UC-18B / M6 Transfer.

Luồng (xem m6_transfer/HIS_IMPORT_FLOW.md):
  Tool his-slip-extractor → file .json/.xlsx → _read_and_process → _process_extracted:
    - chống import trùng (his_slip_no unique)
    - map kho HIS → SC Warehouse, match item theo his_code, match lô, check tồn
    - .json khớp 100% → tạo TR → submit → make_stock_entry → submit SE → SLE (Received)
    - .xlsx / có lỗi → tạo TR Draft staging, tô dòng lỗi, KHÔNG submit

`_process_extracted` chỉ phụ thuộc DB (không gọi Claude) → unit-test được bằng
dữ liệu phiếu mẫu mà không cần API key.
"""

import datetime

import frappe
from frappe import _
from frappe.utils import flt, today

from supplycore.m6_transfer.doctype.sc_his_warehouse_map.sc_his_warehouse_map import (
    resolve_warehouse,
)


# ---------------------------------------------------------------------------
# Helpers đối chiếu (thuần DB)
# ---------------------------------------------------------------------------
def _parse_date(s):
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _match_item(his_code: str):
    code = (his_code or "").strip()
    if not code:
        return None
    return frappe.db.get_value("SC Item", {"his_code": code, "disabled": 0}, "name") \
        or frappe.db.get_value("SC Item", {"his_code": code}, "name")


def _match_batch(item: str, batch_no: str):
    """Match SC Batch theo (item) + (batch_id HOẶC supplier_batch_no = số lô HIS)."""
    bn = (batch_no or "").strip()
    if not item or not bn:
        return None
    found = frappe.db.get_value("SC Batch", {"item": item, "batch_id": bn}, "name")
    if found:
        return found
    return frappe.db.get_value("SC Batch", {"item": item, "supplier_batch_no": bn}, "name")


def _stock(item: str, warehouse: str, batch=None) -> float:
    if not item or not warehouse:
        return 0.0
    if batch:
        v = frappe.db.sql(
            """SELECT COALESCE(SUM(qty_change),0) FROM `tabSC Stock Ledger Entry`
               WHERE item=%s AND warehouse=%s AND batch=%s AND is_cancelled=0""",
            (item, warehouse, batch))
    else:
        v = frappe.db.sql(
            """SELECT COALESCE(SUM(qty_change),0) FROM `tabSC Stock Ledger Entry`
               WHERE item=%s AND warehouse=%s AND is_cancelled=0""",
            (item, warehouse))
    return flt(v[0][0]) if v else 0.0


def _match_line(line: dict, from_warehouse):
    """Đối chiếu 1 dòng phiếu → dict đã match + his_match_status + his_note."""
    his_code = (line.get("his_code") or "").strip()
    name = (line.get("name") or "").strip()
    batch_no = (line.get("batch_no") or "").strip()
    qty = flt(line.get("qty"))

    out = {
        "his_raw_code": his_code,
        "his_raw_name": name,
        "his_note": "",
        "his_match_status": "OK",
        "item": None,
        "item_uom": None,
        "batch": None,
        "qty": qty,
        "batch_no": batch_no,
    }

    item = _match_item(his_code)
    if not item:
        out["his_match_status"] = "Item Not Found"
        out["his_note"] = _("Không tìm thấy SC Item với Mã HIS '{0}'").format(his_code)
        return out
    out["item"] = item
    out["item_uom"] = frappe.db.get_value("SC Item", item, "uom")
    has_batch = frappe.db.get_value("SC Item", item, "has_batch_no")

    if batch_no:
        batch = _match_batch(item, batch_no)
        if not batch:
            out["his_match_status"] = "Batch Not Found"
            out["his_note"] = _("Không tìm thấy lô '{0}' cho VT {1}").format(batch_no, item)
            return out
        out["batch"] = batch
    elif has_batch:
        out["his_match_status"] = "Batch Not Found"
        out["his_note"] = _("Phiếu không có số lô cho VT quản lý lô {0}").format(item)
        return out

    # Check tồn KHẢ DỤNG (chỉ khi đã xác định được kho nguồn). Dùng đúng hàm
    # SE dùng khi submit (get_available_qty) — loại trừ lô QC Pending/Rejected/
    # blocked — để dòng "OK" thật sự submit được, không văng lỗi giữa chừng.
    if from_warehouse:
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import (
            SCStockLedgerEntry,
        )
        avail = SCStockLedgerEntry.get_available_qty(item, from_warehouse, out["batch"])
        if avail < qty:
            out["his_match_status"] = "Insufficient Stock"
            out["his_note"] = _("Tồn khả dụng {0} < SL phiếu {1} tại kho nguồn "
                                "(loại trừ QC Pending/Rejected/blocked)").format(avail, qty)
    return out


# ---------------------------------------------------------------------------
# Orchestration (testable)
# ---------------------------------------------------------------------------
def _process_extracted(data: dict, pdf_file_url=None, force_draft=False, force_draft_note=None) -> dict:
    slip_no = (data.get("slip_no") or "").strip()
    if not slip_no:
        frappe.throw(_("SC-E-HIS-EXTRACT: Phiếu không có Số phiếu (slip_no)"),
                     title="SC-E-HIS-EXTRACT")

    # Idempotency — chống import trùng
    existing = frappe.db.get_value("SC Transfer Request", {"his_slip_no": slip_no}, "name")
    if existing:
        frappe.throw(
            _("SC-E-HIS-DUPLICATE: Phiếu {0} đã được import (TR {1}).").format(slip_no, existing),
            title="SC-E-HIS-DUPLICATE")

    slip_date = _parse_date(data.get("slip_date"))
    from_name = (data.get("from_warehouse_name") or "").strip()
    to_name = (data.get("to_warehouse_name") or "").strip()
    from_wh = resolve_warehouse(from_name)
    to_wh = resolve_warehouse(to_name)

    unmapped_warehouses = []
    if from_name and not from_wh:
        unmapped_warehouses.append(from_name)
    if to_name and not to_wh:
        unmapped_warehouses.append(to_name)

    lines = data.get("lines") or []
    matched = [_match_line(ln, from_wh) for ln in lines]

    has_line_error = any(m["his_match_status"] != "OK" for m in matched)
    has_error = has_line_error or bool(unmapped_warehouses) or not from_wh or not to_wh or not matched

    unmapped_items = sorted({m["his_raw_code"] for m in matched
                             if m["his_match_status"] == "Item Not Found" and m["his_raw_code"]})

    ctx = {
        "slip_no": slip_no, "slip_date": slip_date, "from_wh": from_wh, "to_wh": to_wh,
        "pdf_file_url": pdf_file_url, "matched": matched,
        "unmapped_items": unmapped_items, "unmapped_warehouses": unmapped_warehouses,
    }

    # force_draft: nguồn dễ sai (Excel sửa tay / OCR) → KHÔNG auto-submit, luôn tạo
    # Draft điền sẵn để người dùng đối chiếu rồi submit tay.
    if force_draft:
        note = force_draft_note or _("Nguồn tệp bàn giao — vui lòng đối chiếu trước khi submit.")
        return _do_draft_import(ctx, extra_note=note, forced=True)

    if not has_error:
        # Khớp 100% → thử ghi nhận + auto-submit. Nếu submit thất bại vì bất kỳ
        # lý do nào (validation SE/expiry/bin...) → rollback, hạ xuống Draft an
        # toàn thay vì văng lỗi thô (tuân QĐ#3: lỗi → Draft).
        try:
            return _do_clean_import(ctx)
        except Exception as e:
            frappe.db.rollback()
            return _do_draft_import(ctx, extra_note=_(
                "Auto-submit thất bại → chuyển Draft: {0}").format(str(e)[:200]))

    return _do_draft_import(ctx)


def _new_tr(ctx):
    tr = frappe.new_doc("SC Transfer Request")
    tr.import_source = "HIS Import"
    tr.his_slip_no = ctx["slip_no"]
    tr.his_slip_date = ctx["slip_date"]
    tr.transfer_type = "Routine"
    tr.request_date = ctx["slip_date"] or today()
    tr.required_by = ctx["slip_date"] or today()
    tr.from_warehouse = ctx["from_wh"]
    tr.to_warehouse = ctx["to_wh"]
    if ctx["pdf_file_url"]:
        tr.his_pdf = ctx["pdf_file_url"]
    for m in ctx["matched"]:
        tr.append("items", {
            "item": m["item"],
            "uom": m["item_uom"],
            "requested_qty": m["qty"],
            "approved_qty": m["qty"] if m["his_match_status"] == "OK" else 0,
            "batch": m["batch"],
            "his_match_status": m["his_match_status"],
            "his_raw_code": m["his_raw_code"],
            "his_raw_name": m["his_raw_name"],
            "his_note": m["his_note"],
        })
    return tr


def _do_clean_import(ctx):
    tr = _new_tr(ctx)
    tr.his_import_log = _build_log(ctx["slip_no"], ctx["matched"], ctx["unmapped_warehouses"])
    tr.flags.ignore_permissions = True
    tr.insert()
    tr.submit()
    se_name = tr.make_stock_entry()
    se = frappe.get_doc("SC Stock Entry", se_name)
    se.flags.ignore_permissions = True
    se.submit()
    return _report("submitted", tr, ctx)


def _do_draft_import(ctx, extra_note=None, forced=False):
    tr = _new_tr(ctx)
    log = _build_log(ctx["slip_no"], ctx["matched"], ctx["unmapped_warehouses"])
    if extra_note:
        log = (extra_note + "\n" + log)[:1400]
    tr.his_import_log = log
    tr.flags.his_import_staging = True
    tr.flags.ignore_mandatory = True
    tr.flags.ignore_permissions = True
    tr.insert()
    n_err = sum(1 for m in ctx["matched"] if m["his_match_status"] != "OK")
    # forced + không lỗi đối chiếu → "draft_review" (chờ người đối chiếu rồi submit)
    status = "draft_review" if (forced and n_err == 0 and not ctx["unmapped_warehouses"]) \
        else "draft_with_errors"
    return _report(status, tr, ctx)


def _report(status, tr, ctx):
    matched = ctx["matched"]
    return {
        "status": status,
        "transfer_request": tr.name,
        "his_slip_no": ctx["slip_no"],
        "from_warehouse": ctx["from_wh"],
        "to_warehouse": ctx["to_wh"],
        "lines_total": len(matched),
        "lines_ok": sum(1 for m in matched if m["his_match_status"] == "OK"),
        "lines_error": sum(1 for m in matched if m["his_match_status"] != "OK"),
        "errors": [
            {"tt": i + 1, "his_code": m["his_raw_code"], "name": m["his_raw_name"],
             "status": m["his_match_status"], "note": m["his_note"]}
            for i, m in enumerate(matched) if m["his_match_status"] != "OK"
        ],
        "unmapped_items": ctx["unmapped_items"],
        "unmapped_warehouses": ctx["unmapped_warehouses"],
    }


def _build_log(slip_no, matched, unmapped_warehouses) -> str:
    lines = [f"Phiếu HIS: {slip_no}",
             f"Tổng dòng: {len(matched)} | "
             f"OK: {sum(1 for m in matched if m['his_match_status']=='OK')} | "
             f"Lỗi: {sum(1 for m in matched if m['his_match_status']!='OK')}"]
    if unmapped_warehouses:
        lines.append("Kho chưa map: " + ", ".join(unmapped_warehouses))
    for i, m in enumerate(matched):
        if m["his_match_status"] != "OK":
            lines.append(f"  Dòng {i+1} [{m['his_raw_code']}] {m['his_raw_name']}: "
                         f"{m['his_match_status']} — {m['his_note']}")
    return "\n".join(lines)[:1400]


# ---------------------------------------------------------------------------
# Đọc + xử lý file bàn giao từ tool his-slip-extractor
# ---------------------------------------------------------------------------
def _read_and_process(path: str, pdf_file_url=None) -> dict:
    from supplycore.api.his_file_read import read_json_file, read_xlsx_file
    lower = path.lower()
    if lower.endswith(".json"):
        data = read_json_file(path)
    elif lower.endswith((".xlsx", ".xls")):
        data = read_xlsx_file(path)
    else:
        frappe.throw(_("SC-E-HIS-EXTRACT: Chỉ nhận file .json hoặc .xlsx"),
                     title="SC-E-HIS-EXTRACT")
    # Excel có thể được sửa tay (nguồn sự thật) → KHÔNG auto-submit, luôn Draft đối chiếu.
    force_draft = lower.endswith((".xlsx", ".xls"))
    note = _("File Excel đã đối chiếu/sửa tay — kiểm tra lại rồi submit.") if force_draft else None
    return _process_extracted(data, pdf_file_url=pdf_file_url, force_draft=force_draft,
                              force_draft_note=note)


@frappe.whitelist()
def import_slip_file(file_url: str) -> dict:
    """Nhập 1 phiếu chuyển kho từ FILE do tool his-slip-extractor sinh ra.

    file_url: URL file .json (máy) hoặc .xlsx (người đã đối chiếu/sửa). Trả report
    dict (xem _process_extracted).
    """
    _check_permission()
    if not file_url:
        frappe.throw(_("SC-E-HIS-EXTRACT: Thiếu file_url"), title="SC-E-HIS-EXTRACT")
    try:
        file_doc = frappe.get_doc("File", {"file_url": file_url})
    except frappe.DoesNotExistError:
        frappe.throw(_("Không tìm thấy file: {0}").format(file_url))
    return _read_and_process(file_doc.get_full_path(), pdf_file_url=file_url)


def _check_permission():
    allowed = {"System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
               "Warehouse Officer"}
    if not (set(frappe.get_roles(frappe.session.user)) & allowed):
        frappe.throw(_("Bạn không có quyền nhập phiếu chuyển kho HIS"),
                     frappe.PermissionError)
