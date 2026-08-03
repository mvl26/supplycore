"""GĐ MVL — tạo Print Format TT99/2025 cho bộ chứng từ bán hàng.

Idempotent: upsert theo tên Print Format (xoá & tạo lại nội dung để cập nhật khi
sửa template). Module = "M7 Sales" (đã thêm vào fixtures Print Format ở hooks.py
→ ship sang site khác). Dùng Jinja helper sc_seller_info / sc_dong_in_words
(hooks.py::jinja).

Chứng từ: Hoá đơn (SI), Phiếu giao (DN), Biên bản nghiệm thu (Acceptance),
Hợp đồng khung (SFC), Phiếu thu (Receipt), Đơn gọi hàng (SO).

Rollback: xoá các Print Format tên "TT99 - *".
"""

import frappe

CSS = """
<style>
  .tt99 { font-family: "Times New Roman", serif; font-size: 13px; color: #000; }
  .tt99 .center { text-align: center; }
  .tt99 .right { text-align: right; }
  .tt99 .b { font-weight: bold; }
  .tt99 .muted { color: #333; }
  .tt99 .hdr { display: flex; justify-content: space-between; align-items: flex-start; }
  .tt99 h1 { font-size: 18px; margin: 12px 0 2px; text-align: center; text-transform: uppercase; }
  .tt99 .sub { text-align: center; margin-bottom: 10px; }
  .tt99 table.items { width: 100%; border-collapse: collapse; margin-top: 8px; }
  .tt99 table.items th, .tt99 table.items td { border: 1px solid #000; padding: 4px 6px; }
  .tt99 table.items th { background: #f0f0f0; text-align: center; }
  .tt99 .num { text-align: right; font-variant-numeric: tabular-nums; }
  .tt99 .kv { margin: 2px 0; }
  .tt99 .sign { display: flex; justify-content: space-around; margin-top: 26px; text-align: center; }
  .tt99 .sign .col { width: 30%; }
  .tt99 .sign .role { font-weight: bold; }
  .tt99 .sign .hint { font-style: italic; font-size: 12px; }
  .tt99 .words { font-style: italic; margin-top: 6px; }
</style>
"""

HEADER = """
{%- set S = sc_seller_info() -%}
<div class="hdr">
  <div>
    <div class="b">{{ S.name }}</div>
    <div class="muted">{{ S.address }}</div>
    <div class="muted">MST: {{ S.tax_code or "..............." }}</div>
  </div>
  <div class="right muted">
    Mẫu số: {DOCCODE}<br>
    Số: {{ doc.name }}
  </div>
</div>
<h1>{TITLE}</h1>
<div class="sub">Ngày {DATEEXPR}</div>
"""

BUYER = """
<div class="kv"><span class="b">Khách hàng:</span>
  {{ frappe.db.get_value("SC Customer", doc.customer, "customer_name") or doc.customer }}</div>
<div class="kv"><span class="b">MST:</span>
  {{ frappe.db.get_value("SC Customer", doc.customer, "tax_code") or "" }}</div>
<div class="kv"><span class="b">Địa chỉ:</span>
  {{ frappe.db.get_value("SC Customer", doc.customer, "billing_address") or "" }}</div>
"""


def _sign(*cols):
    inner = "".join(
        f'<div class="col"><div class="role">{r}</div><div class="hint">{h}</div></div>'
        for r, h in cols)
    return f'<div class="sign">{inner}</div>'


SIGN_INVOICE = _sign(
    ("Người mua hàng", "(Ký, ghi rõ họ tên)"),
    ("Người lập", "(Ký, ghi rõ họ tên)"),
    ("Thủ trưởng đơn vị", "(Ký, đóng dấu)"),
)
SIGN_DELIVERY = _sign(
    ("Người nhận hàng", "(Ký, ghi rõ họ tên)"),
    ("Thủ kho", "(Ký, ghi rõ họ tên)"),
    ("Người lập phiếu", "(Ký, ghi rõ họ tên)"),
)
SIGN_ACCEPT = _sign(
    ("Đại diện bên mua", "(Ký, ghi rõ họ tên)"),
    ("Đại diện bên bán", "(Ký, ghi rõ họ tên)"),
)
SIGN_CONTRACT = _sign(
    ("ĐẠI DIỆN BÊN MUA", "(Ký, đóng dấu)"),
    ("ĐẠI DIỆN BÊN BÁN", "(Ký, đóng dấu)"),
)
SIGN_RECEIPT = _sign(
    ("Người nộp tiền", "(Ký, ghi rõ họ tên)"),
    ("Người thu tiền", "(Ký, ghi rõ họ tên)"),
    ("Kế toán trưởng", "(Ký, ghi rõ họ tên)"),
)


def _wrap(body):
    return f'<div class="tt99">{CSS}{body}</div>'


def _header(title, doccode, dateexpr):
    return (HEADER.replace("{TITLE}", title)
            .replace("{DOCCODE}", doccode)
            .replace("{DATEEXPR}", dateexpr))


# --- Item tables (Jinja) ---
ITEMS_INVOICE = """
<table class="items">
  <thead><tr><th>STT</th><th>Tên hàng hoá, dịch vụ</th><th>ĐVT</th><th>SL</th>
    <th>Đơn giá</th><th>Thành tiền</th></tr></thead>
  <tbody>
  {%- for it in doc.items %}
    <tr><td class="center">{{ loop.index }}</td>
      <td>{{ frappe.db.get_value("SC Item", it.item, "item_name") or it.item }}</td>
      <td class="center">{{ it.get("uom") or "" }}</td>
      <td class="num">{{ "{:,.0f}".format(it.qty or 0).replace(",", ".") }}</td>
      <td class="num">{{ "{:,.0f}".format(it.get("unit_price") or 0).replace(",", ".") }}</td>
      <td class="num">{{ "{:,.0f}".format(it.get("amount") or 0).replace(",", ".") }}</td></tr>
  {%- endfor %}
  </tbody>
</table>
<div class="right" style="margin-top:6px">
  <div><span class="b">Cộng tiền hàng:</span> {{ "{:,.0f}".format(doc.get("total_amount") or 0).replace(",", ".") }} đ</div>
  {%- if doc.get("tax_amount") %}<div><span class="b">Thuế GTGT:</span> {{ "{:,.0f}".format(doc.get("tax_amount")).replace(",", ".") }} đ</div>{%- endif %}
  <div class="b">Tổng cộng thanh toán: {{ "{:,.0f}".format(doc.get("grand_total") or doc.get("total_amount") or 0).replace(",", ".") }} đ</div>
</div>
<div class="words">Số tiền bằng chữ: {{ sc_dong_in_words(doc.get("grand_total") or doc.get("total_amount") or 0) }}</div>
"""

ITEMS_DELIVERY = """
<table class="items">
  <thead><tr><th>STT</th><th>Tên vật tư</th><th>ĐVT</th><th>Số lô NCC</th><th>SL giao</th></tr></thead>
  <tbody>
  {%- for it in doc.items %}
    {%- set _sbn = frappe.db.get_value("SC Batch", it.get("batch"), "supplier_batch_no") if it.get("batch") else "" %}
    <tr><td class="center">{{ loop.index }}</td>
      <td>{{ frappe.db.get_value("SC Item", it.item, "item_name") or it.item }}</td>
      <td class="center">{{ it.get("uom") or "" }}</td>
      <td class="center">{{ _sbn or "" }}</td>
      <td class="num">{{ "{:,.0f}".format(it.qty or 0).replace(",", ".") }}</td></tr>
  {%- endfor %}
  </tbody>
</table>
"""

ITEMS_CONTRACT = """
<div class="kv"><span class="b">Hiệu lực:</span> {{ doc.valid_from }} — {{ doc.valid_to }}</div>
<table class="items">
  <thead><tr><th>STT</th><th>Tên vật tư</th><th>ĐVT</th><th>Định mức SL</th>
    <th>Đơn giá</th><th>Thành tiền</th></tr></thead>
  <tbody>
  {%- for it in doc.items %}
    <tr><td class="center">{{ loop.index }}</td>
      <td>{{ frappe.db.get_value("SC Item", it.item, "item_name") or it.item }}</td>
      <td class="center">{{ it.get("uom") or "" }}</td>
      <td class="num">{{ "{:,.0f}".format(it.get("contract_qty") or 0).replace(",", ".") }}</td>
      <td class="num">{{ "{:,.0f}".format(it.get("unit_price") or 0).replace(",", ".") }}</td>
      <td class="num">{{ "{:,.0f}".format((it.get("contract_qty") or 0) * (it.get("unit_price") or 0)).replace(",", ".") }}</td></tr>
  {%- endfor %}
  </tbody>
</table>
<div class="right b" style="margin-top:6px">Tổng giá trị hợp đồng: {{ "{:,.0f}".format(doc.total_value or 0).replace(",", ".") }} đ</div>
<div class="words">Bằng chữ: {{ sc_dong_in_words(doc.total_value or 0) }}</div>
"""

BODY_ACCEPT = """
<div class="kv"><span class="b">Phiếu giao hàng số:</span> {{ doc.delivery_note }}</div>
<div class="kv"><span class="b">Ngày nghiệm thu:</span> {{ doc.acceptance_date }}</div>
<div class="kv"><span class="b">Người nhận (phía khách):</span> {{ doc.accepted_by or "" }}</div>
<p style="margin-top:10px">Hai bên đã tiến hành nghiệm thu, xác nhận hàng hoá giao theo Phiếu giao hàng
nêu trên đủ số lượng, đúng chủng loại và đạt yêu cầu chất lượng.</p>
{%- if doc.note %}<div class="kv"><span class="b">Ghi chú:</span> {{ doc.note }}</div>{%- endif %}
"""

BODY_RECEIPT = """
<div class="kv"><span class="b">Người nộp tiền:</span>
  {{ frappe.db.get_value("SC Customer", doc.customer, "customer_name") or doc.customer }}</div>
<div class="kv"><span class="b">Về khoản:</span> Thanh toán hoá đơn {{ doc.sales_invoice or "" }}</div>
<div class="kv"><span class="b">Hình thức:</span> {{ doc.mode or "" }}</div>
<div class="kv b" style="margin-top:8px">Số tiền: {{ "{:,.0f}".format(doc.amount or 0).replace(",", ".") }} đ</div>
<div class="words">Bằng chữ: {{ sc_dong_in_words(doc.amount or 0) }}</div>
"""


def _fmt(doc_type, name, title, doccode, dateexpr, buyer, body, sign):
    html = _wrap(_header(title, doccode, dateexpr) + buyer + body + sign)
    return {"doc_type": doc_type, "name": name, "html": html}


FORMATS = [
    _fmt("SC Sales Invoice", "TT99 - Hoá đơn bán hàng", "HOÁ ĐƠN BÁN HÀNG",
         "01-SI", "{{ doc.invoice_date }}", BUYER, ITEMS_INVOICE, SIGN_INVOICE),
    _fmt("SC Delivery Note", "TT99 - Phiếu giao hàng", "PHIẾU GIAO HÀNG",
         "02-DN", "{{ doc.delivery_date }}", BUYER, ITEMS_DELIVERY, SIGN_DELIVERY),
    _fmt("SC Acceptance Record", "TT99 - Biên bản nghiệm thu", "BIÊN BẢN NGHIỆM THU",
         "03-NT", "{{ doc.acceptance_date }}",
         '<div class="kv"><span class="b">Khách hàng:</span> {{ frappe.db.get_value("SC Customer", doc.customer, "customer_name") or doc.customer }}</div>',
         BODY_ACCEPT, SIGN_ACCEPT),
    _fmt("SC Sales Framework Contract", "TT99 - Hợp đồng khung bán hàng", "HỢP ĐỒNG KHUNG BÁN HÀNG",
         "04-HDK", "{{ doc.valid_from }}", BUYER, ITEMS_CONTRACT, SIGN_CONTRACT),
    _fmt("SC Sales Receipt", "TT99 - Phiếu thu", "PHIẾU THU",
         "05-PT", "{{ doc.receipt_date or doc.creation }}",
         "", BODY_RECEIPT, SIGN_RECEIPT),
    _fmt("SC Sales Order", "TT99 - Đơn gọi hàng", "ĐƠN GỌI HÀNG (THEO HỢP ĐỒNG KHUNG)",
         "06-DGH", "{{ doc.order_date }}", BUYER, ITEMS_INVOICE, SIGN_CONTRACT),
]


def execute():
    for f in FORMATS:
        if frappe.db.exists("Print Format", f["name"]):
            frappe.delete_doc("Print Format", f["name"], ignore_permissions=True, force=True)
        pf = frappe.new_doc("Print Format")
        pf.name = f["name"]
        pf.doc_type = f["doc_type"]
        pf.module = "M7 Sales"
        pf.print_format_type = "Jinja"
        pf.standard = "No"
        pf.custom_format = 1
        pf.disabled = 0
        pf.html = f["html"]
        pf.flags.ignore_permissions = True
        pf.insert()
        # Đặt TT99 làm print format MẶC ĐỊNH của doctype — để frappe.get_print
        # (portal_document_download gọi không chỉ định format) dùng TT99 thay vì
        # Standard. Property Setter survive migrate; get_print đọc lại sau clear-cache.
        frappe.make_property_setter({
            "doctype": f["doc_type"],
            "doctype_or_field": "DocType",
            "property": "default_print_format",
            "value": f["name"],
            "property_type": "Data",
        }, is_system_generated=True)
        print(f"  ✓ Print Format: {f['name']} (default)")
    frappe.clear_cache()
    frappe.db.commit()
