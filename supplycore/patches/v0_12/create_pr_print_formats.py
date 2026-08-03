"""GĐ MVL — 2 print format cho SC Purchase Receipt (luồng nhập kho 2 bước).

- "Phiếu tiếp nhận tạm": in ngay khi tiếp nhận, ghi rõ HÀNG CHƯA NHẬP KHO — CHỜ QC.
- "Phiếu nhập kho (TT99)": in sau khi Xác nhận nhập kho, mẫu chính thức.
Idempotent (xoá & tạo lại). Dùng jinja helper sc_seller_info (hooks.py::jinja).
Rollback: xoá 2 Print Format tên "PR - *".
"""

import frappe

CSS = """<style>
 .pr { font-family:"Times New Roman",serif; font-size:13px; color:#000; }
 .pr .center{text-align:center} .pr .right{text-align:right} .pr .b{font-weight:bold}
 .pr h1{font-size:18px;text-align:center;text-transform:uppercase;margin:10px 0 2px}
 .pr .warn{border:1.5px solid #b3261e;color:#b3261e;font-weight:bold;text-align:center;padding:6px;margin:8px 0}
 .pr table{width:100%;border-collapse:collapse;margin-top:8px}
 .pr th,.pr td{border:1px solid #000;padding:4px 6px} .pr th{background:#f0f0f0;text-align:center}
 .pr .num{text-align:right} .pr .kv{margin:2px 0}
 .pr .sign{display:flex;justify-content:space-around;margin-top:26px;text-align:center}
 .pr .sign .role{font-weight:bold}.pr .sign .hint{font-style:italic;font-size:12px}
</style>"""

HEADER = """{%- set S = sc_seller_info() -%}
<div class="b">{{ S.name }}</div><div>MST: {{ S.tax_code or "..." }}</div>
<h1>{TITLE}</h1>
<div class="center">Số: {{ doc.name }} · Ngày tiếp nhận: {{ doc.posting_date }}</div>
{WARN}
<div class="kv"><span class="b">Nhà cung cấp:</span> {{ frappe.db.get_value("SC Supplier", doc.supplier, "supplier_name") or doc.supplier }}</div>
<div class="kv"><span class="b">Kho nhập:</span> {{ doc.to_warehouse }}</div>
{CONFIRM}
"""

# ITEMS: in TẤT CẢ dòng (dùng cho phiếu tiếp nhận tạm — hàng chưa QC).
ITEMS = """<table>
 <thead><tr><th>STT</th><th>Tên vật tư</th><th>ĐVT</th><th>Số lô NCC</th><th>HSD</th><th>SL</th><th>Đơn giá</th><th>Thành tiền</th></tr></thead>
 <tbody>
 {%- for it in doc.items %}
 <tr><td class="center">{{ loop.index }}</td>
  <td>{{ frappe.db.get_value("SC Item", it.item, "item_name") or it.item }}</td>
  <td class="center">{{ it.get("uom") or "" }}</td>
  {%- set _sbn = it.get("supplier_batch_no") or (frappe.db.get_value("SC Batch", it.get("batch_no"), "supplier_batch_no") if it.get("batch_no") else "") %}
  <td class="center">{{ _sbn or "" }}</td>
  <td class="center">{{ it.get("expiry_date") or "" }}</td>
  <td class="num">{{ "{:,.0f}".format(it.qty or 0).replace(",", ".") }}</td>
  <td class="num">{{ "{:,.0f}".format(it.get("rate") or 0).replace(",", ".") }}</td>
  <td class="num">{{ "{:,.0f}".format(it.get("amount") or 0).replace(",", ".") }}</td></tr>
 {%- endfor %}
 </tbody></table>
<div class="right b" style="margin-top:6px">Tổng giá trị: {{ "{:,.0f}".format(doc.total_value or 0).replace(",", ".") }} đ</div>
"""

# ITEMS_IN: CHỈ in dòng ĐÃ nhập kho = lô KHÔNG bị QC Từ chối (Rejected). Dòng bị
# từ chối đã/đang trả NCC nên KHÔNG nằm trên phiếu nhập kho — chúng in ở phiếu trả
# NCC. Tổng giá trị tính lại theo đúng phần thực nhập.
ITEMS_IN = """{%- set ns = namespace(stt=0, total=0.0) -%}
<table>
 <thead><tr><th>STT</th><th>Tên vật tư</th><th>ĐVT</th><th>Số lô</th><th>HSD</th><th>SL</th><th>Đơn giá</th><th>Thành tiền</th></tr></thead>
 <tbody>
 {%- for it in doc.items %}
 {%- set qc = frappe.db.get_value("SC Batch", it.get("batch_no"), "qc_status") if it.get("batch_no") else None %}
 {%- if qc != "Rejected" %}
 {%- set ns.stt = ns.stt + 1 %}
 {%- set ns.total = ns.total + (it.get("amount") or 0) %}
 <tr><td class="center">{{ ns.stt }}</td>
  <td>{{ frappe.db.get_value("SC Item", it.item, "item_name") or it.item }}</td>
  <td class="center">{{ it.get("uom") or "" }}</td>
  <td class="center">{{ it.get("batch_no") or "" }}</td>
  <td class="center">{{ it.get("expiry_date") or "" }}</td>
  <td class="num">{{ "{:,.0f}".format(it.qty or 0).replace(",", ".") }}</td>
  <td class="num">{{ "{:,.0f}".format(it.get("rate") or 0).replace(",", ".") }}</td>
  <td class="num">{{ "{:,.0f}".format(it.get("amount") or 0).replace(",", ".") }}</td></tr>
 {%- endif %}
 {%- endfor %}
 {%- if ns.stt == 0 %}
 <tr><td colspan="8" class="center">(Không có vật tư đủ điều kiện nhập kho)</td></tr>
 {%- endif %}
 </tbody></table>
<div class="right b" style="margin-top:6px">Tổng giá trị nhập kho: {{ "{:,.0f}".format(ns.total).replace(",", ".") }} đ</div>
"""

SIGN = """<div class="sign">
 <div><div class="role">Người giao (NCC)</div><div class="hint">(Ký, ghi rõ họ tên)</div></div>
 <div><div class="role">Thủ kho</div><div class="hint">(Ký, ghi rõ họ tên)</div></div>
 <div><div class="role">KCS / QC</div><div class="hint">(Ký, ghi rõ họ tên)</div></div>
</div>"""

# Chữ ký cho phiếu TRẢ NCC (bên trả ↔ bên nhận NCC).
SIGN_RETURN = """<div class="sign">
 <div><div class="role">Người lập phiếu</div><div class="hint">(Ký, ghi rõ họ tên)</div></div>
 <div><div class="role">Thủ kho (giao trả)</div><div class="hint">(Ký, ghi rõ họ tên)</div></div>
 <div><div class="role">Nhà cung cấp (nhận)</div><div class="hint">(Ký, ghi rõ họ tên)</div></div>
</div>"""

FORMATS = [
    {
        "name": "PR - Phiếu tiếp nhận tạm",
        "html": '<div class="pr">' + CSS
        + HEADER.replace("{TITLE}", "PHIẾU TIẾP NHẬN TẠM")
                .replace("{WARN}", '<div class="warn">HÀNG CHƯA NHẬP KHO — ĐANG CHỜ QC / XÁC NHẬN NHẬP KHO</div>')
                .replace("{CONFIRM}", '<div class="kv"><span class="b">Trạng thái QC:</span> {{ doc.qc_status or "Chờ QC" }}</div>')
        + ITEMS + SIGN + "</div>",
    },
    {
        "name": "PR - Phiếu nhập kho (TT99)",
        "html": '<div class="pr">' + CSS
        + HEADER.replace("{TITLE}", "PHIẾU NHẬP KHO")
                .replace("{WARN}", "")
                .replace("{CONFIRM}",
                         '<div class="kv"><span class="b">Ngày nhập kho:</span> {{ doc.warehouse_in_date or doc.posting_date }}'
                         ' · <span class="b">Người xác nhận:</span> {{ doc.confirmed_by or "" }}</div>')
        + ITEMS_IN + SIGN + "</div>",
    },
    {
        "name": "PR - Phiếu trả NCC",
        "html": '<div class="pr">' + CSS
        + HEADER.replace("{TITLE}", "PHIẾU TRẢ HÀNG NHÀ CUNG CẤP")
                .replace("{WARN}", '<div class="warn">HÀNG TRẢ LẠI NHÀ CUNG CẤP — KHÔNG ĐỦ ĐIỀU KIỆN NHẬP KHO</div>')
                .replace("{CONFIRM}",
                         '<div class="kv"><span class="b">Lý do trả:</span> {{ doc.remarks or "QC không đạt" }}</div>')
        + ITEMS + SIGN_RETURN + "</div>",
    },
]


def execute():
    for f in FORMATS:
        if frappe.db.exists("Print Format", f["name"]):
            frappe.delete_doc("Print Format", f["name"], ignore_permissions=True, force=True)
        pf = frappe.new_doc("Print Format")
        pf.name = f["name"]
        pf.doc_type = "SC Purchase Receipt"
        pf.module = "Supplycore"
        pf.print_format_type = "Jinja"
        pf.standard = "No"
        pf.custom_format = 1
        pf.disabled = 0
        pf.html = f["html"]
        pf.flags.ignore_permissions = True
        pf.insert()
        print(f"  ✓ Print Format: {f['name']}")
    frappe.db.commit()
