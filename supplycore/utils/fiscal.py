"""Fiscal period lock (BRU-PAY-001) — shared enforcement helper.

BRU-PAY-001: không được GHI (submit) hoặc HỦY (cancel) bất kỳ chứng từ kế
toán nào có ngày chứng từ (invoice_date/receipt_date/payment_date/...) nằm
trong kỳ đã khóa sổ (<= SupplyCore Settings.fiscal_lock_date).

Trước fix này, check chỉ tồn tại (inline, KHÔNG dùng chung) trên SC Sales
Invoice / SC Sales Receipt submit — KHÔNG có trên SC Purchase Invoice / SC
Payment Entry submit, VÀ KHÔNG có trên BẤT KỲ đường cancel nào. Hệ quả:
  - PI/PE vẫn submit được vào kỳ đã khóa (không bị chặn).
  - `SCGLEntry.cancel_voucher()` đảo bút toán GL NGƯỢC LẠI đúng posting_date
    GỐC của chứng từ — nếu chứng từ đó có ngày nằm trong kỳ đã khóa (vd. kỳ
    bị khóa SAU KHI đã submit), hủy chứng từ sẽ ghi bút toán đảo vào LẠI kỳ
    đã khóa, phá vỡ bất biến "không ghi vào kỳ đã khóa" qua đường cancel.

Fix: 1 helper dùng chung cho cả 4 doctype (SC Sales Invoice, SC Sales
Receipt, SC Purchase Invoice, SC Payment Entry), gọi TRƯỚC submit VÀ TRƯỚC
cancel (trước khi gọi `SCGLEntry.cancel_voucher`).
"""

import frappe
from frappe import _
from frappe.utils import getdate


def check_fiscal_lock(posting_date) -> None:
    """Throw nếu `posting_date` nằm trong kỳ đã khóa sổ.

    Không throw nếu `fiscal_lock_date` chưa cấu hình (None/rỗng) hoặc
    `posting_date` rỗng (phòng thủ — các field ngày gọi hàm này đều `reqd`
    trên doctype nên trường hợp rỗng không nên xảy ra trên luồng thường)."""
    if not posting_date:
        return
    lock = frappe.db.get_single_value("SupplyCore Settings", "fiscal_lock_date")
    if lock and getdate(posting_date) <= getdate(lock):
        # Giữ cả 2 mã lỗi trong message (SC-E-FISCAL-LOCK là mã thống nhất
        # mới; BRU-PAY-001 là mã rule nghiệp vụ đã dùng từ trước trên SC
        # Sales Invoice/SC Sales Receipt) — tránh phá vỡ các assertion cũ
        # đang match theo "BRU-PAY-001" trong khi vẫn thêm mã lỗi mới thống
        # nhất cho PI/PE + mọi path cancel.
        frappe.throw(_(
            "SC-E-FISCAL-LOCK (BRU-PAY-001): Kỳ kế toán đã khóa đến {0} — "
            "không thể ghi/hủy chứng từ ngày {1}."
        ).format(lock, posting_date), title="SC-E-FISCAL-LOCK")
