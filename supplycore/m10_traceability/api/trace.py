"""Truy xuất nguồn gốc batch (M10)."""

import frappe


@frappe.whitelist()
def get_batch_trace(batch_no: str):
    """Trả về toàn bộ vòng đời 1 batch: PO → PR → QI → Putaway → Issue → Patient.

    Truy vấn Stock Ledger Entry + custom DocType (Patient Dispensing, Recall Notice).
    """
    return {
        "batch_no": batch_no,
        "events": [],  # TODO: aggregate Stock Ledger Entry + Patient Dispensing
    }
