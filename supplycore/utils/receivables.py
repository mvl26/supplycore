"""Công nợ phải thu khách hàng — HÀM CHUẨN DUY NHẤT (single source of truth).

GĐ MVL — đóng finding audit D: trước đây Rule (sc_sales_order._check_credit_limit)
và Portal (portal._customer_outstanding) tự resolve TK Phải thu riêng lẻ → Rule
FAIL-OPEN khi field trống còn Portal có fallback, hai nơi ra số khác nhau. Từ nay
MỌI nơi cần "dư nợ hiện tại" / "hạn mức" / "số tối thiểu phải trả" của khách (rule
chặn đơn, portal hiển thị, report, print) PHẢI gọi các hàm ở đây.

Nguồn chân lý: số dư TK Phải thu (131) theo party = customer trên SC GL Entry
(GL-based, Nợ − Có). KHÔNG dùng SUM(SI.outstanding_amount) cho quyết định tín
dụng — hai con số này phải khớp về sổ sách; nếu lệch là bug bút toán chứ không
phải chỗ để chọn nguồn. (Báo cáo tuổi nợ `ar_aging_by_customer` vẫn dùng dữ liệu
per-invoice vì cần chia bucket theo ngày từng hoá đơn — đó là chi tiết hoá đơn,
không phải nguồn số dư.)
"""

import frappe
from frappe import _
from frappe.utils import flt


def get_receivable_account() -> str:
    """TK Phải thu KH: ưu tiên Settings.default_receivable_account, fallback TK 131.

    Throw nếu KHÔNG resolve được — cố tình KHÔNG fail-open (trả 0) như code cũ, vì
    trả 0 nghĩa là bỏ qua toàn bộ dư nợ → đơn lọt qua rule tín dụng một cách âm thầm.
    Patch v0_11 backfill default_receivable_account nên đường này thực tế luôn resolve.
    """
    acct = frappe.db.get_single_value("SupplyCore Settings", "default_receivable_account") \
        or frappe.db.get_value("SC GL Account", {"account_code": "131"}, "name")
    if not acct:
        frappe.throw(_(
            "Chưa cấu hình TK Phải thu khách hàng (SupplyCore Settings → 'TK Phải thu KH "
            "mặc định', hoặc TK GL mã 131). Không thể tính công nợ — liên hệ kế toán."
        ), title="CONFIG-AR-ACCOUNT")
    return acct


def get_customer_outstanding(customer: str) -> float:
    """Dư nợ phải thu hiện tại của khách = số dư Nợ TK 131 theo party (Nợ − Có).

    Nguồn CHUẨN DUY NHẤT cho rule + portal + report + print.
    """
    if not customer:
        return 0.0
    from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry
    return flt(SCGLEntry.get_balance(get_receivable_account(), customer))


def _setting_raw(field: str):
    """Đọc THÔ giá trị field của SupplyCore Settings từ tabSingles.

    Dùng thay `get_single_value` cho các cờ Check MỚI THÊM: `get_single_value`
    coerce field Check chưa có bản ghi trong tabSingles về 0 (không phân biệt
    "chưa cấu hình" với "tắt có chủ đích") → không áp được default an toàn. Query
    thô trả None khi CHƯA có bản ghi để hàm gọi tự quyết default.
    """
    row = frappe.db.sql(
        "SELECT value FROM `tabSingles` WHERE doctype='SupplyCore Settings' AND field=%s",
        (field,))
    return row[0][0] if row else None


def is_credit_check_enabled() -> bool:
    """Cờ bật/tắt rule chặn nợ toàn cục (Settings.credit_check_enabled).

    Mặc định BẬT khi field chưa cấu hình (bản ghi Settings cũ / chưa backfill) —
    an toàn theo hướng chặt: thà chặn nhầm còn hơn bỏ lọt nợ.
    """
    v = _setting_raw("credit_check_enabled")
    return True if v is None else bool(int(v or 0))


def is_stock_block_enabled() -> bool:
    """Cờ chặn gọi hàng khi tồn không đủ (Settings.block_order_on_insufficient_stock).

    Mặc định BẬT khi chưa cấu hình — khớp default '1' của field trong doctype.
    """
    v = _setting_raw("block_order_on_insufficient_stock")
    return True if v is None else bool(int(v or 0))


def get_customer_credit_limit(customer: str) -> float:
    """Hạn mức công nợ HIỆU LỰC của khách (Q3 — global default + override per-KH):

    ưu tiên `SC Customer.credit_limit` nếu > 0; ngược lại lấy ngưỡng mặc định toàn
    cục `SupplyCore Settings.default_credit_limit`. Trả 0 = "không đặt ngưỡng" →
    rule không chặn (tương thích ngược: khách cũ credit_limit=0 vẫn không bị chặn
    TRỪ KHI admin cấu hình default_credit_limit > 0 — đóng đúng lỗ hổng KH tự đăng
    ký lách rule mà không phá luồng đang chạy).
    """
    if customer:
        cust_limit = flt(frappe.db.get_value("SC Customer", customer, "credit_limit"))
        if cust_limit > 0:
            return cust_limit
    return flt(frappe.db.get_single_value("SupplyCore Settings", "default_credit_limit"))


def get_min_payment(customer: str, additional_amount: float = 0.0) -> float:
    """Số tiền tối thiểu khách phải trả để (dư nợ + đơn mới) về đúng hạn mức.

    = max(0, outstanding + additional_amount − effective_limit). Trả 0 nếu không
    có ngưỡng hoặc chưa vượt (không cần trả trước).
    """
    limit = get_customer_credit_limit(customer)
    if limit <= 0:
        return 0.0
    over = get_customer_outstanding(customer) + flt(additional_amount) - limit
    return flt(over) if over > 0 else 0.0
