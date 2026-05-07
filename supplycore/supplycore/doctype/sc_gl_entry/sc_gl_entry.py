"""SC GL Entry — immutable bút toán kế toán."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SCGLEntry(Document):

    def on_change(self):
        if not self.flags.allow_gl_edit and not self.is_new():
            frappe.throw(_("SC GL Entry là immutable"))

    @staticmethod
    def post(account, debit=0, credit=0, *,
             voucher_type, voucher_no, posting_date,
             party_type=None, party=None, against_account=None,
             voucher_detail_no=None, remarks=None):
        """Helper: insert GL Entry. Một row chỉ có 1 trong 2 (debit hoặc credit)."""
        if flt(debit) and flt(credit):
            frappe.throw(_("Một GL Entry chỉ được debit HOẶC credit, không cả hai"))
        if not flt(debit) and not flt(credit):
            return None  # skip zero entries
        gl = frappe.new_doc("SC GL Entry")
        gl.posting_date = posting_date
        gl.account = account
        gl.debit = flt(debit)
        gl.credit = flt(credit)
        gl.voucher_type = voucher_type
        gl.voucher_no = voucher_no
        gl.voucher_detail_no = voucher_detail_no
        gl.party_type = party_type
        gl.party = party
        gl.against_account = against_account
        gl.remarks = remarks
        gl.flags.allow_gl_edit = True
        gl.insert(ignore_permissions=True)
        return gl.name

    @staticmethod
    def post_journal(entries: list, voucher_type: str, voucher_no: str, posting_date,
                     remarks: str = None):
        """Post nhiều entries cùng lúc; verify tổng nợ = tổng có (kế toán cân bằng)."""
        total_debit = sum(flt(e.get("debit", 0)) for e in entries)
        total_credit = sum(flt(e.get("credit", 0)) for e in entries)
        if abs(total_debit - total_credit) > 0.01:
            frappe.throw(_("GL Journal không cân: Nợ {0} ≠ Có {1}")
                         .format(total_debit, total_credit))
        # Build against_account string (đối ứng)
        debits = [e["account"] for e in entries if flt(e.get("debit"))]
        credits = [e["account"] for e in entries if flt(e.get("credit"))]
        for e in entries:
            against = ", ".join(credits if flt(e.get("debit")) else debits)
            SCGLEntry.post(
                account=e["account"],
                debit=flt(e.get("debit", 0)),
                credit=flt(e.get("credit", 0)),
                voucher_type=voucher_type, voucher_no=voucher_no,
                posting_date=posting_date,
                party_type=e.get("party_type"), party=e.get("party"),
                against_account=against,
                voucher_detail_no=e.get("voucher_detail_no"),
                remarks=e.get("remarks") or remarks,
            )

    @staticmethod
    def cancel_voucher(voucher_type: str, voucher_no: str):
        """Đảo ngược: insert GL đối ứng + đánh dấu original is_cancelled."""
        rows = frappe.get_all("SC GL Entry",
            filters={"voucher_type": voucher_type, "voucher_no": voucher_no, "is_cancelled": 0},
            fields=["name", "account", "debit", "credit", "posting_date",
                    "party_type", "party", "against_account", "voucher_detail_no"])
        for r in rows:
            SCGLEntry.post(
                account=r.account,
                debit=flt(r.credit),  # đảo Nợ ↔ Có
                credit=flt(r.debit),
                voucher_type=voucher_type, voucher_no=voucher_no,
                posting_date=r.posting_date,
                party_type=r.party_type, party=r.party,
                against_account=r.against_account,
                voucher_detail_no=(r.voucher_detail_no or "") + "-CANCEL",
                remarks=f"Cancel of GL {r.name}",
            )
            frappe.db.set_value("SC GL Entry", r.name, "is_cancelled", 1)

    @staticmethod
    def get_balance(account: str, party: str = None) -> float:
        """Số dư hiện tại của account (Nợ - Có); với account loại Liability/Income đảo dấu."""
        sql = """
            SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0)
            FROM `tabSC GL Entry`
            WHERE account = %s AND is_cancelled = 0
        """
        params = [account]
        if party:
            sql += " AND party = %s"
            params.append(party)
        return flt(frappe.db.sql(sql, tuple(params))[0][0])
