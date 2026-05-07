"""WMS / PDA REST endpoints (M4) — used bởi mobile app + barcode scanner."""

import frappe
from frappe import _
from frappe.utils import flt, today


# ---------------------------------------------------------------------------
# scan_barcode — resolve barcode → Item / Batch / Bin Location
# ---------------------------------------------------------------------------
@frappe.whitelist()
def scan_barcode(barcode: str, context: str = None):
    """Trả thông tin entity theo barcode quét được.

    Thứ tự lookup:
    1. Item Barcode (tabItem Barcode)
    2. Item.name trực tiếp
    3. Batch.name (số lô)
    4. Bin Location (theo barcode hoặc name)

    Args:
        barcode: chuỗi barcode quét được
        context: 'receipt' / 'issue' / 'transfer' / 'count' (optional, ảnh hưởng suggestion)
    """
    if not barcode:
        frappe.throw(_("barcode không được rỗng"))
    barcode = barcode.strip()

    # 1. SC Item Barcode (multi-barcode per item)
    item_via_barcode = frappe.db.get_value("SC Item Barcode", {"barcode": barcode}, "parent")
    if item_via_barcode:
        return _build_item_response(item_via_barcode, context)

    # 2. SC Item code trực tiếp
    if frappe.db.exists("SC Item", barcode):
        return _build_item_response(barcode, context)

    # 3. SC Batch
    if frappe.db.exists("SC Batch", barcode):
        batch = frappe.db.get_value("SC Batch", barcode,
                                     ["name", "item", "expiry_date", "manufacturing_date"],
                                     as_dict=True)
        item_info = _build_item_response(batch.item, context)
        return {
            "type": "batch",
            "batch_no": batch.name,
            "item_code": batch.item,
            "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
            "manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else None,
            "item": item_info,
        }

    # 4. Bin Location: by barcode field hoặc by name
    bin_via_barcode = frappe.db.get_value("Bin Location", {"barcode": barcode}, "name")
    bin_loc_name = bin_via_barcode or (barcode if frappe.db.exists("Bin Location", barcode) else None)
    if bin_loc_name:
        bin_doc = frappe.get_doc("Bin Location", bin_loc_name)
        return {
            "type": "bin",
            "bin_location": bin_doc.name,
            "bin_code": bin_doc.bin_code,
            "warehouse": bin_doc.warehouse,
            "is_quarantine": bool(bin_doc.is_quarantine),
        }

    frappe.throw(_("Barcode {0} không nhận dạng được").format(barcode), title="SC-WMS-404")


def _build_item_response(item_code: str, context: str = None) -> dict:
    item = frappe.db.get_value("SC Item", item_code,
                                ["name", "item_name", "uom", "has_batch_no",
                                 "is_stock_item", "default_bin_location",
                                 "inspection_required_before_purchase"],
                                as_dict=True)
    if not item:
        frappe.throw(_("Item {0} không tồn tại").format(item_code))

    response = {
        "type": "item",
        "item_code": item.name,
        "item_name": item.item_name,
        "uom": item.uom,
        "has_batch": bool(item.has_batch_no),
        "is_stock_item": bool(item.is_stock_item),
        "qc_required": bool(item.inspection_required_before_purchase),
    }
    if item.default_bin_location:
        bin_doc = frappe.db.get_value("Bin Location", item.default_bin_location,
                                       ["name", "bin_code", "warehouse"], as_dict=True)
        if bin_doc:
            response["suggested_bin"] = bin_doc
    return response


# ---------------------------------------------------------------------------
# lookup_bin_for_item — gợi ý bin để putaway
# ---------------------------------------------------------------------------
@frappe.whitelist()
def lookup_bin_for_item(item_code: str, warehouse: str = None) -> dict:
    """Gợi ý bin theo thứ tự: Item.default → Putaway Rule → bin trống đầu tiên trong warehouse."""
    # 1. Item default
    default_bin = frappe.db.get_value("SC Item", item_code, "default_bin_location")
    if default_bin and frappe.db.exists("Bin Location", default_bin):
        bin_info = frappe.db.get_value("Bin Location", default_bin,
                                        ["name", "bin_code", "warehouse"], as_dict=True)
        if not warehouse or bin_info.warehouse == warehouse:
            return {"source": "item_default", "bin_location": bin_info.name,
                    "warehouse": bin_info.warehouse, "bin_code": bin_info.bin_code}

    # 2. Bin enabled đầu tiên trong warehouse
    if warehouse:
        bin_first = frappe.db.get_value("Bin Location",
                                         {"warehouse": warehouse, "enabled": 1, "is_quarantine": 0},
                                         ["name", "bin_code"], as_dict=True)
        if bin_first:
            return {"source": "first_available", "bin_location": bin_first.name,
                    "warehouse": warehouse, "bin_code": bin_first.bin_code}

    return {"source": "none", "warehouse": warehouse, "bin_location": None}


# ---------------------------------------------------------------------------
# get_bin_inventory — list items hiện ở bin
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_bin_inventory(bin_location: str) -> list:
    if not frappe.db.exists("Bin Location", bin_location):
        frappe.throw(_("Bin Location {0} không tồn tại").format(bin_location))
    bin_doc = frappe.get_doc("Bin Location", bin_location)
    return bin_doc.get_current_inventory()


# ---------------------------------------------------------------------------
# confirm_putaway — tạo Stock Entry Material Receipt từ PDA
# ---------------------------------------------------------------------------
@frappe.whitelist()
def confirm_putaway(item_code: str, warehouse: str, qty: float,
                    bin_location: str = None, batch_no: str = None,
                    pda_session: str = None) -> dict:
    """PDA endpoint: xác nhận putaway, tạo SC Stock Entry draft."""
    if flt(qty) <= 0:
        frappe.throw(_("qty phải > 0"))
    if not frappe.db.exists("SC Warehouse", warehouse):
        frappe.throw(_("Warehouse {0} không tồn tại").format(warehouse))

    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Receipt"
    se.posting_date = today()
    se.to_warehouse = warehouse
    se.pda_session_id = pda_session
    se.append("items", {
        "item": item_code,
        "qty": flt(qty),
        "uom": item_uom,
        "batch": batch_no,
        "target_bin": bin_location,
    })
    se.flags.ignore_permissions = True
    se.insert()
    return {"stock_entry": se.name, "status": "Draft"}


# ---------------------------------------------------------------------------
# search — tìm vật tư/bin theo keyword (cho PDA quick search)
# ---------------------------------------------------------------------------
@frappe.whitelist()
def quick_search(keyword: str, entity_type: str = "item", limit: int = 10) -> list:
    """Search Item / Bin Location theo prefix keyword."""
    keyword = (keyword or "").strip()
    if len(keyword) < 2:
        return []

    if entity_type == "item":
        return frappe.db.sql("""
            SELECT name AS item_code, item_name, uom
            FROM `tabSC Item`
            WHERE disabled = 0 AND is_stock_item = 1
              AND (name LIKE %(kw)s OR item_name LIKE %(kw)s)
            LIMIT %(limit)s
        """, {"kw": f"%{keyword}%", "limit": limit}, as_dict=True)

    if entity_type == "bin":
        return frappe.db.sql("""
            SELECT name AS bin_location, bin_code, warehouse
            FROM `tabBin Location`
            WHERE enabled = 1
              AND (bin_code LIKE %(kw)s OR name LIKE %(kw)s)
            LIMIT %(limit)s
        """, {"kw": f"%{keyword}%", "limit": limit}, as_dict=True)

    return []
