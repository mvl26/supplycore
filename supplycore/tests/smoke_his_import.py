"""Smoke test UC-18B — nhập phiếu chuyển kho HIS (orchestration, không cần API key).

Chạy: bench --site <site> execute supplycore.tests.smoke_his_import.run
Tự rollback, không để lại dữ liệu.
"""

import frappe
from frappe.utils import today

from supplycore.api.his_import import _process_extracted

MOCK = {
    "slip_no": "PX050626-SMOKE",
    "slip_date": "09/06/2026",
    "from_warehouse_name": "Kho Khoa Điều trị Cao Cấp",
    "to_warehouse_name": "Kho lẻ nội trú",
    "lines": [
        {"tt": 1, "name": "Betahistin 24 24mg", "his_code": "2025GE222", "uom": "Viên",
         "batch_no": "2602620", "expiry": "01/03/2029", "qty": 2, "unit_price": 2300, "amount": 4600},
        {"tt": 4, "name": "Cồn xoa bóp Jamda 50ml", "his_code": "2025GE240", "uom": "Lọ",
         "batch_no": "3925", "expiry": "07/12/2027", "qty": 1, "unit_price": 18000, "amount": 18000},
        {"tt": 9, "name": "Hoàn lục vị", "his_code": "2026TPSX10", "uom": "Gam",
         "batch_no": "080126", "expiry": "30/04/2028", "qty": 24, "unit_price": 379.12, "amount": 9098.88},
    ],
}


def run():
    out = []
    try:
        # --- Test 1: error path (chưa map gì) → Draft staging ---
        r = _process_extracted(MOCK)
        out.append(f"T1 status={r['status']} total/ok/err={r['lines_total']}/{r['lines_ok']}/{r['lines_error']}")
        out.append(f"T1 unmapped_wh={r['unmapped_warehouses']}")
        out.append(f"T1 unmapped_items={r['unmapped_items']}")
        assert r["status"] == "draft_with_errors", "expected draft_with_errors"
        assert r["lines_total"] == 3 and r["lines_error"] == 3
        assert set(r["unmapped_warehouses"]) == {"Kho Khoa Điều trị Cao Cấp", "Kho lẻ nội trú"}

        tr = frappe.get_doc("SC Transfer Request", r["transfer_request"])
        out.append(f"T1 TR docstatus={tr.docstatus} status={tr.status} source={tr.import_source} rows={len(tr.items)}")
        out.append(f"T1 row0 match={tr.items[0].his_match_status!r} item_blank={not tr.items[0].item} "
                   f"raw_code={tr.items[0].his_raw_code!r}")
        assert tr.docstatus == 0 and tr.import_source == "HIS Import"
        assert tr.items[0].his_match_status == "Item Not Found"

        # --- Test 2: idempotency ---
        dup_ok = False
        try:
            _process_extracted(MOCK)
        except frappe.ValidationError as e:
            dup_ok = "SC-E-HIS-DUPLICATE" in str(e)
        out.append(f"T2 duplicate_blocked={dup_ok}")
        assert dup_ok, "duplicate not blocked"

        # --- Test 3: clean path (auto-submit) với dữ liệu tối thiểu ---
        out.append(_clean_path_test())

        # --- Test 4: mixed path (1 OK + 1 lỗi → Draft staging) ---
        out.append(_mixed_path_test())

        # --- Test 5: luồng UC-18 thủ công còn nguyên vẹn (regression) ---
        out.append(_manual_flow_intact_test())

        # --- Test 7: force_draft (OCR) — luôn Draft, không chuyển tồn ---
        out.append(_force_draft_test())

        # --- Test 8: đọc file bàn giao JSON + Excel → canonical dict ---
        out.append(_file_read_test())

        # --- Test 9: import_slip_file (JSON) đi qua _read_and_process/_process_extracted ---
        out.append(_import_file_test())

        out.append("ALL TESTS PASSED")
    except Exception as e:
        out.append(f"FAIL: {type(e).__name__}: {e}")
        import traceback
        out.append(traceback.format_exc()[-1500:])
    finally:
        frappe.db.rollback()
        out.append("ROLLED BACK")
    print("\n".join(out))


def _clean_path_test():
    """Tạo item + 2 kho + batch + tồn rồi import 1 dòng khớp 100% → submit + SLE."""
    wh_from = _ensure_warehouse("SMOKE Kho Nguồn")
    wh_to = _ensure_warehouse("SMOKE Kho Đích")
    item = _ensure_item("SMOKE-HIS-IT1", "Smoke VT HIS", his_code="SMOKEHIS1", has_batch=1)
    batch = _ensure_batch(item, "SMOKELOT1")
    _ensure_map("HIS Kho Nguồn Smoke", wh_from)
    _ensure_map("HIS Kho Đích Smoke", wh_to)
    _seed_stock(item, wh_from, batch, 50)

    data = {
        "slip_no": "PX-SMOKE-CLEAN", "slip_date": "09/06/2026",
        "from_warehouse_name": "HIS Kho Nguồn Smoke",
        "to_warehouse_name": "HIS Kho Đích Smoke",
        "lines": [{"tt": 1, "name": "Smoke VT HIS", "his_code": "SMOKEHIS1", "uom": "",
                   "batch_no": "SMOKELOT1", "expiry": "01/01/2030", "qty": 10,
                   "unit_price": 0, "amount": 0}],
    }
    r = _process_extracted(data)
    tr = frappe.get_doc("SC Transfer Request", r["transfer_request"])
    se_qty_from = _stock(item, wh_from, batch)
    se_qty_to = _stock(item, wh_to, batch)
    assert r["status"] == "submitted", f"expected submitted, got {r['status']}"
    assert tr.docstatus == 1 and tr.status == "Received", f"TR {tr.docstatus}/{tr.status}"
    assert tr.stock_entry, "no stock entry linked"
    assert se_qty_from == 40, f"from stock should be 40, got {se_qty_from}"
    assert se_qty_to == 10, f"to stock should be 10, got {se_qty_to}"
    return (f"T3 status={r['status']} TR={tr.docstatus}/{tr.status} SE={tr.stock_entry} "
            f"from_stock={se_qty_from} to_stock={se_qty_to}")


def _mixed_path_test():
    """1 dòng khớp + 1 dòng sai mã → draft_with_errors, dòng OK populate, dòng lỗi blank."""
    wh_from = _ensure_warehouse("SMOKE Kho Nguồn")
    wh_to = _ensure_warehouse("SMOKE Kho Đích")
    item = _ensure_item("SMOKE-HIS-IT1", "Smoke VT HIS", his_code="SMOKEHIS1", has_batch=1)
    batch = _ensure_batch(item, "SMOKELOT1")
    _ensure_map("HIS Kho Nguồn Smoke", wh_from)
    _ensure_map("HIS Kho Đích Smoke", wh_to)
    _seed_stock(item, wh_from, batch, 50)
    data = {
        "slip_no": "PX-SMOKE-MIXED", "slip_date": "09/06/2026",
        "from_warehouse_name": "HIS Kho Nguồn Smoke", "to_warehouse_name": "HIS Kho Đích Smoke",
        "lines": [
            {"tt": 1, "name": "Smoke VT HIS", "his_code": "SMOKEHIS1", "uom": "",
             "batch_no": "SMOKELOT1", "expiry": "", "qty": 5, "unit_price": 0, "amount": 0},
            {"tt": 2, "name": "Hàng lạ", "his_code": "KHONGCO999", "uom": "",
             "batch_no": "X", "expiry": "", "qty": 1, "unit_price": 0, "amount": 0},
        ],
    }
    r = _process_extracted(data)
    tr = frappe.get_doc("SC Transfer Request", r["transfer_request"])
    ok_row = tr.items[0]
    err_row = tr.items[1]
    assert r["status"] == "draft_with_errors", r["status"]
    assert r["lines_ok"] == 1 and r["lines_error"] == 1, (r["lines_ok"], r["lines_error"])
    assert ok_row.his_match_status == "OK" and ok_row.item == item and ok_row.approved_qty == 5
    assert err_row.his_match_status == "Item Not Found" and not err_row.item
    assert tr.docstatus == 0
    return (f"T4 status={r['status']} ok={r['lines_ok']} err={r['lines_error']} "
            f"okrow_item={bool(ok_row.item)} errrow_blank={not err_row.item}")


def _manual_flow_intact_test():
    """TR thủ công (import_source=Manual) vẫn chạy validate cứng + submit chuẩn."""
    wh_from = _ensure_warehouse("SMOKE Kho Nguồn")
    wh_to = _ensure_warehouse("SMOKE Kho Đích")
    item = _ensure_item("SMOKE-HIS-IT1", "Smoke VT HIS", his_code="SMOKEHIS1", has_batch=1)
    batch = _ensure_batch(item, "SMOKELOT1")
    _seed_stock(item, wh_from, batch, 50)

    # 5a: validate cứng vẫn áp dụng (from==to → SC-E024)
    same_blocked = False
    try:
        tr = frappe.new_doc("SC Transfer Request")
        tr.transfer_type = "Routine"; tr.request_date = today(); tr.required_by = today()
        tr.from_warehouse = wh_from; tr.to_warehouse = wh_from
        tr.append("items", {"item": item, "uom": frappe.db.get_value("SC Item", item, "uom"),
                            "requested_qty": 1, "approved_qty": 1, "batch": batch})
        tr.flags.ignore_permissions = True
        tr.insert()
    except frappe.ValidationError as e:
        same_blocked = "SC-E024" in str(e)

    # 5b: TR thủ công hợp lệ submit chuẩn (import_source mặc định = Manual)
    tr2 = frappe.new_doc("SC Transfer Request")
    tr2.transfer_type = "Routine"; tr2.request_date = today(); tr2.required_by = today()
    tr2.from_warehouse = wh_from; tr2.to_warehouse = wh_to
    tr2.append("items", {"item": item, "uom": frappe.db.get_value("SC Item", item, "uom"),
                        "requested_qty": 3, "approved_qty": 3, "batch": batch})
    tr2.flags.ignore_permissions = True
    tr2.insert()
    src = tr2.import_source
    tr2.submit()
    assert same_blocked, "manual same-warehouse not blocked (validate bypassed!)"
    assert src == "Manual", f"manual TR import_source={src}"
    assert tr2.docstatus == 1 and tr2.status == "Approved", f"{tr2.docstatus}/{tr2.status}"
    return f"T5 manual same_blocked={same_blocked} source={src} submit={tr2.docstatus}/{tr2.status}"


def _force_draft_test():
    """force_draft (OCR) — kể cả khớp 100% vẫn tạo Draft, KHÔNG chuyển tồn."""
    wh_from = _ensure_warehouse("SMOKE Kho Nguồn")
    wh_to = _ensure_warehouse("SMOKE Kho Đích")
    item = _ensure_item("SMOKE-HIS-IT1", "Smoke VT HIS", his_code="SMOKEHIS1", has_batch=1)
    batch = _ensure_batch(item, "SMOKELOT1")
    _ensure_map("HIS Kho Nguồn Smoke", wh_from)
    _ensure_map("HIS Kho Đích Smoke", wh_to)
    _seed_stock(item, wh_from, batch, 50)
    data = {
        "slip_no": "PX-SMOKE-OCR", "slip_date": "09/06/2026",
        "from_warehouse_name": "HIS Kho Nguồn Smoke", "to_warehouse_name": "HIS Kho Đích Smoke",
        "lines": [{"tt": 1, "name": "Smoke VT HIS", "his_code": "SMOKEHIS1", "uom": "",
                   "batch_no": "SMOKELOT1", "expiry": "", "qty": 10, "unit_price": 0, "amount": 0}],
    }
    from supplycore.api.his_import import _stock
    before = _stock(item, wh_from, batch)
    r = _process_extracted(data, force_draft=True)
    after = _stock(item, wh_from, batch)
    tr = frappe.get_doc("SC Transfer Request", r["transfer_request"])
    assert r["status"] == "draft_review", r["status"]
    assert tr.docstatus == 0 and not tr.stock_entry, "force_draft created/submitted SE!"
    assert after == before, f"stock moved despite force_draft ({before}→{after})"
    assert tr.items[0].his_match_status == "OK" and tr.items[0].item == item
    return f"T7 status={r['status']} TR_docstatus={tr.docstatus} no_SE={not tr.stock_entry} stock_delta={after-before}"


def _file_read_test():
    import os
    from supplycore.api.his_file_read import read_json_file, read_xlsx_file
    base = os.path.join(os.path.dirname(__file__), "fixtures")
    dj = read_json_file(os.path.join(base, "sample_slip.json"))
    dx = read_xlsx_file(os.path.join(base, "sample_slip.xlsx"))
    for d in (dj, dx):
        assert d["slip_no"] == "PX-FIX", d.get("slip_no")
        assert d["from_warehouse_name"] == "HIS Kho Nguồn Smoke"
        assert len(d["lines"]) == 1
        ln = d["lines"][0]
        assert ln["his_code"] == "SMOKEHIS1" and ln["qty"] == 10.0
    return f"T8 json_lines={len(dj['lines'])} xlsx_lines={len(dx['lines'])} ok"


def _import_file_test():
    """import_slip_file(JSON) khi chưa seed map/item → đi qua _read_and_process/_process_extracted."""
    import os
    from supplycore.api.his_import import _read_and_process
    base = os.path.join(os.path.dirname(__file__), "fixtures")
    r = _read_and_process(os.path.join(base, "sample_slip.json"))
    assert r["status"] in ("draft_with_errors", "draft_review", "submitted"), r["status"]
    assert r["his_slip_no"] == "PX-FIX"
    return f"T9 import_file status={r['status']} slip={r['his_slip_no']}"


# --- minimal data helpers ---
def _stock(item, wh, batch):
    from supplycore.api.his_import import _stock as s
    return s(item, wh, batch)


def _ensure_warehouse(name):
    if frappe.db.exists("SC Warehouse", name):
        return name
    wh = frappe.new_doc("SC Warehouse")
    wh.warehouse_name = name
    wh.flags.ignore_permissions = True
    wh.flags.ignore_mandatory = True
    wh.insert()
    return wh.name


def _ensure_uom(name="Viên"):
    if frappe.db.exists("SC UOM", name):
        return name
    u = frappe.new_doc("SC UOM")
    u.uom_name = name
    u.flags.ignore_permissions = True
    u.flags.ignore_mandatory = True
    u.insert()
    return u.name


def _ensure_item(code, name, his_code, has_batch):
    if frappe.db.exists("SC Item", code):
        return code
    uom = _ensure_uom()
    it = frappe.new_doc("SC Item")
    it.item_code = code
    it.item_name = name
    it.his_code = his_code
    it.uom = uom
    it.has_batch_no = has_batch
    it.is_stock_item = 1
    it.flags.ignore_permissions = True
    it.flags.ignore_mandatory = True
    it.insert()
    return it.name


def _ensure_batch(item, lot):
    if frappe.db.exists("SC Batch", lot):
        return lot
    b = frappe.new_doc("SC Batch")
    b.batch_id = lot
    b.item = item
    b.expiry_date = "2030-01-01"
    b.qc_status = "Accepted"  # nếu Pending → get_available_qty loại trừ
    b.flags.ignore_permissions = True
    b.flags.ignore_mandatory = True
    b.insert()
    return b.name


def _ensure_map(his_name, warehouse):
    if frappe.db.exists("SC HIS Warehouse Map", his_name):
        return his_name
    m = frappe.new_doc("SC HIS Warehouse Map")
    m.his_warehouse_name = his_name
    m.warehouse = warehouse
    m.flags.ignore_permissions = True
    m.insert()
    return m.name


def _seed_stock(item, warehouse, batch, qty):
    """Seed tồn nguồn bằng raw SQL (SLE là immutable, không insert qua ORM được)."""
    name = frappe.generate_hash(length=12)
    frappe.db.sql(
        """INSERT INTO `tabSC Stock Ledger Entry`
           (name, creation, modified, modified_by, owner, docstatus, idx,
            posting_date, item, warehouse, batch, qty_change, is_cancelled)
           VALUES (%s, NOW(), NOW(), 'Administrator', 'Administrator', 1, 0,
            %s, %s, %s, %s, %s, 0)""",
        (name, today(), item, warehouse, batch, qty))
