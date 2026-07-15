"""GĐ MVL — backfill cấu hình kiểm soát công nợ trên SupplyCore Settings.

Đóng finding audit D (rule chặn nợ fail-open): đảm bảo `default_receivable_account`
luôn được set để hàm chuẩn `utils.receivables.get_receivable_account` không phải
throw/không bỏ lọt dư nợ trên site đã có dữ liệu thật.

Idempotent:
- Chỉ set `default_receivable_account` khi đang trống (không đè giá trị kế toán đã chọn).
- `credit_check_enabled` / `default_credit_limit` / `block_order_on_insufficient_stock`
  đã có `default` trong doctype JSON; chỉ khởi tạo giá trị nếu đang NULL (bản ghi
  Single cũ tạo trước khi thêm field) để hành vi rõ ràng, không dựa vào ngầm định.

Rollback: các thay đổi chỉ là giá trị Settings; nếu cần hoàn tác, sửa lại trên
SupplyCore Settings hoặc set default_receivable_account về trống.
"""

import frappe


def _has_single_value(field: str) -> bool:
    """True nếu SupplyCore Settings đã có bản ghi cho field trong tabSingles.

    Dùng set_single_value (ghi thẳng tabSingles) thay vì doc.save() vì patch có
    thể chạy TRƯỚC khi doctype được sync field mới vào meta — lúc đó save() bỏ
    qua field không có trong meta, không persist. set_single_value không phụ
    thuộc meta nên an toàn với mọi thứ tự migrate.
    """
    return bool(frappe.db.sql(
        "SELECT 1 FROM `tabSingles` WHERE doctype='SupplyCore Settings' AND field=%s LIMIT 1",
        (field,)))


def execute():
    # 1) TK Phải thu KH mặc định — fallback TK 131 (đã seed trong seed_master_data).
    if not frappe.db.get_single_value("SupplyCore Settings", "default_receivable_account"):
        ar = frappe.db.get_value("SC GL Account", {"account_code": "131"}, "name") \
            or frappe.db.get_value("SC GL Account", {"account_type": "Receivable"}, "name")
        if ar:
            frappe.db.set_single_value("SupplyCore Settings", "default_receivable_account", ar)
            print(f"  ✓ default_receivable_account = {ar}")

    # 2) Cờ / ngưỡng — chỉ set khi CHƯA có bản ghi (idempotent, không đè admin đã chỉnh).
    for field, default in [
        ("credit_check_enabled", 1),
        ("default_credit_limit", 0),
        ("block_order_on_insufficient_stock", 1),
    ]:
        if not _has_single_value(field):
            frappe.db.set_single_value("SupplyCore Settings", field, default)
            print(f"  ✓ {field} = {default}")

    frappe.db.commit()
    print("  ✓ SupplyCore Settings credit-control backfilled")
