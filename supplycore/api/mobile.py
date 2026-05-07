"""REST endpoints cho PDA / Mobile (M4)."""

import frappe


@frappe.whitelist()
def scan_barcode(barcode: str):
    """Trả về Item / Batch / Bin Location khớp barcode."""
    return {}


@frappe.whitelist()
def confirm_putaway(batch_no: str, bin_location: str, qty: float):
    """Xác nhận putaway từ PDA — tạo Stock Entry Material Transfer."""
    return {"ok": True}
