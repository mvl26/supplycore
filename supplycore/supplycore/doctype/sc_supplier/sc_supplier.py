"""SC Supplier — NCC + scorecard cho UC-01 + validate UC-02.

API:
- get_scorecard(supplier) — instance method gọi qua frm.call
- supplycore.supplycore.doctype.sc_supplier.sc_supplier.get_scorecard — module-level (REST)
"""

import re
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, add_months, getdate

from supplycore.utils.permissions import block_portal


class SCSupplier(Document):

    def validate(self):
        self._validate_tax_id_format()
        self._validate_tax_id_unique()
        self._validate_email_format()
        self._normalize_bank_holder()
        self._validate_supplied_item_groups()

    def _validate_tax_id_format(self):
        """QA-BUG-M0-02: MST Việt Nam phải đúng định dạng theo Thông tư
        105/2020/TT-BTC: 10 chữ số (NCC chính) hoặc 13 chữ số (10-3 cho
        đơn vị phụ thuộc, viết liền hoặc cách bằng dấu '-').

        Regex chấp nhận:
          - 1234567890        (10 chữ số)
          - 1234567890001     (13 chữ số liền)
          - 1234567890-001    (10-3 cách bằng dấu)
        """
        if not self.tax_id:
            return
        clean = self.tax_id.strip().replace(" ", "")
        if not re.match(r"^[0-9]{10}(-?[0-9]{3})?$", clean):
            frappe.throw(_(
                "SC-E021 INVALID_TAX_ID: MST '{0}' không đúng định dạng VN. "
                "Phải là 10 chữ số (vd: 0301110116) hoặc 13 chữ số "
                "(vd: 0301110116001 hoặc 0301110116-001) theo Thông tư "
                "105/2020/TT-BTC."
            ).format(self.tax_id), title="SC-E021 INVALID_TAX_ID")
        # Normalize: bỏ '-' để lưu thống nhất
        self.tax_id = clean.replace("-", "")

    def _validate_tax_id_unique(self):
        """UC-02 step 7: kiểm tra trùng MST."""
        if not self.tax_id:
            return
        # Check duplicate (trừ chính nó)
        existing = frappe.db.get_value("SC Supplier",
            {"tax_id": self.tax_id, "name": ["!=", self.name or ""]}, "name")
        if existing:
            frappe.throw(
                _("MST {0} đã tồn tại ở NCC khác: {1}").format(self.tax_id, existing),
                title="SC-E-DUPLICATE-TAX-ID")

    def _validate_email_format(self):
        if not self.email_id:
            return
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", self.email_id):
            frappe.throw(_("Email không hợp lệ: {0}").format(self.email_id),
                          title="SC-E-EMAIL")

    def _normalize_bank_holder(self):
        """Default bank_account_holder = supplier_name nếu để trống."""
        if self.bank_account_no and not self.bank_account_holder:
            self.bank_account_holder = self.supplier_name

    def _validate_supplied_item_groups(self):
        """Dedup item_groups child table."""
        seen = set()
        for row in (self.supplied_item_groups or []):
            if row.item_group in seen:
                frappe.throw(_("Item Group {0} bị trùng trong danh sách cung ứng")
                              .format(row.item_group),
                              title="SC-E-DUPLICATE-ITEM-GROUP")
            seen.add(row.item_group)

    @frappe.whitelist()
    def get_scorecard(self):
        """Trả scorecard hiện tại của NCC này."""
        return get_scorecard(self.name)


@frappe.whitelist()
def get_scorecard(supplier: str) -> dict:
    """Compute scorecard 12 tháng gần nhất cho NCC.

    Returns:
      {
        supplier, supplier_name, rating, blacklist_flag,
        active_contracts, active_contracts_remaining_value,
        total_pos_12m, total_value_12m,
        on_time_delivery_pct,    # PR.posting_date ≤ PO.schedule_date
        qc_pass_pct,             # QI Accepted / total QI submit
        ap_outstanding,          # SUM PI outstanding
        open_alerts              # SC Alert count với supplier reference
      }

    GĐ4 Task 5 (security sweep): hàm module-level, KHÔNG qua `run_doc_method`
    (không tự động check permission) — không gate thì lộ rating/blacklist/
    công nợ NCC/hợp đồng cho BẤT KỲ supplier nào caller truyền vào.
    """
    block_portal()
    if not frappe.db.exists("SC Supplier", supplier):
        frappe.throw(_("NCC {0} không tồn tại").format(supplier))

    sup = frappe.db.get_value("SC Supplier", supplier,
                                ["name", "supplier_name", "rating", "blacklist_flag"],
                                as_dict=True)

    cutoff = add_months(today(), -12)

    # Active framework contracts
    fc_rows = frappe.db.sql("""
        SELECT COUNT(*) AS c, COALESCE(SUM(remaining_value), 0) AS rv
        FROM `tabFramework Contract`
        WHERE supplier = %s AND docstatus = 1 AND status = 'Active'
    """, supplier, as_dict=True)
    active_contracts = int(fc_rows[0].c) if fc_rows else 0
    fc_remaining = flt(fc_rows[0].rv) if fc_rows else 0

    # POs 12 tháng
    po_rows = frappe.db.sql("""
        SELECT COUNT(*) AS c, COALESCE(SUM(grand_total), 0) AS gt
        FROM `tabSC Purchase Order`
        WHERE supplier = %s AND docstatus = 1
          AND transaction_date >= %s
    """, (supplier, cutoff), as_dict=True)
    total_pos = int(po_rows[0].c) if po_rows else 0
    total_value = flt(po_rows[0].gt) if po_rows else 0

    # On-time delivery: PR có posting_date ≤ PO.schedule_date
    on_time = frappe.db.sql("""
        SELECT
          SUM(CASE WHEN pr.posting_date <= po.schedule_date THEN 1 ELSE 0 END) AS on_time,
          COUNT(*) AS total
        FROM `tabSC Purchase Receipt` pr
        JOIN `tabSC Purchase Order` po ON po.name = pr.purchase_order
        WHERE pr.supplier = %s AND pr.docstatus = 1 AND pr.is_return = 0
          AND po.docstatus = 1
          AND pr.posting_date >= %s
    """, (supplier, cutoff), as_dict=True)
    on_time_pct = (
        round(flt(on_time[0].on_time) / flt(on_time[0].total) * 100, 2)
        if on_time and on_time[0].total else None
    )

    # QC pass rate: QI Accepted / total submitted QI cho NCC
    qc_rows = frappe.db.sql("""
        SELECT
          SUM(CASE WHEN qi.overall_status = 'Accepted' THEN 1 ELSE 0 END) AS pass_,
          COUNT(*) AS total
        FROM `tabSC Quality Inspection` qi
        JOIN `tabSC Purchase Receipt` pr ON pr.name = qi.purchase_receipt
        WHERE pr.supplier = %s AND qi.docstatus = 1
          AND qi.inspection_date >= %s
    """, (supplier, cutoff), as_dict=True)
    qc_pass_pct = (
        round(flt(qc_rows[0].pass_) / flt(qc_rows[0].total) * 100, 2)
        if qc_rows and qc_rows[0].total else None
    )

    # AP outstanding
    ap_outstanding = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0)
        FROM `tabSC Purchase Invoice`
        WHERE supplier = %s AND docstatus = 1 AND status NOT IN ('Paid', 'Cancelled')
    """, supplier)[0][0])

    # Open alerts (qua reference_name nếu là supplier hoặc qua PI)
    open_alerts = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabSC Alert` a
        WHERE a.resolved = 0 AND (
          (a.reference_doctype = 'SC Supplier' AND a.reference_name = %(s)s)
          OR (a.reference_doctype = 'SC Purchase Invoice' AND a.reference_name IN
              (SELECT name FROM `tabSC Purchase Invoice` WHERE supplier = %(s)s))
          OR (a.reference_doctype = 'Framework Contract' AND a.reference_name IN
              (SELECT name FROM `tabFramework Contract` WHERE supplier = %(s)s))
        )
    """, {"s": supplier})[0][0]

    return {
        "supplier": supplier,
        "supplier_name": sup.supplier_name,
        "rating": flt(sup.rating),
        "blacklist_flag": bool(sup.blacklist_flag),
        "active_contracts": active_contracts,
        "active_contracts_remaining_value": fc_remaining,
        "total_pos_12m": total_pos,
        "total_value_12m": total_value,
        "on_time_delivery_pct": on_time_pct,
        "qc_pass_pct": qc_pass_pct,
        "ap_outstanding": ap_outstanding,
        "open_alerts": int(open_alerts),
        "period": {"from": cutoff, "to": today()},
    }
