"""Test UC-04 4 scenarios."""
import frappe
from frappe.utils import today, add_days, random_string


def run():
    ts = random_string(6)
    sup = frappe.db.get_value('SC Supplier', {'supplier_name':'Công ty CP Dược Hậu Giang'}, 'name')
    item = 'VTTH-MASK-3PLY'
    item_uom = frappe.db.get_value('SC Item', item, 'uom')

    def make_fc(suffix, valid_to, total=50_000_000):
        fc = frappe.new_doc('Framework Contract')
        fc.supplier = sup
        fc.contract_number = f'UC04-{suffix}-{ts}'
        fc.contract_date = add_days(today(), -60)
        fc.valid_from = add_days(today(), -30)
        fc.valid_to = valid_to
        fc.total_value = total
        fc.append('items', {'item_code': item, 'contract_qty': 1000,
                             'uom': item_uom, 'unit_price': 50000})
        fc.flags.ignore_permissions = True
        fc.insert(); fc.reload()
        fc.submit_for_review(); fc.reload()
        fc.approve_as_manager(); fc.reload()
        if fc.approval_stage == 'Executive Review':
            fc.approve_as_executive(); fc.reload()
        fc.submit(); fc.reload()
        return fc

    out = []
    out.append("=== TEST 1: Gia hạn happy path ===")
    fc = make_fc('R1', add_days(today(), 60))
    out.append(f"  FC {fc.name}: valid_to={fc.valid_to}, status={fc.status}")
    r = fc.request_renewal(new_valid_to=add_days(today(), 365),
                            reason='Tiếp tục cung ứng năm 2027')
    out.append(f"  request_renewal -> {r}")
    fc.reload()
    out.append(f"  History rows: {len(fc.renewal_history)}, status: {fc.renewal_history[0].approval_status}")
    r = fc.approve_renewal(row_idx=1, comment='OK Manager duyệt')
    out.append(f"  approve_renewal -> {r}")
    fc.reload()
    out.append(f"  After approve: valid_to={fc.valid_to}, status={fc.status}")

    out.append("")
    out.append("=== TEST 2: Reject renewal ===")
    fc2 = make_fc('R2', add_days(today(), 60))
    fc2.request_renewal(new_valid_to=add_days(today(), 200), reason='Test reject')
    fc2.reload()
    r = fc2.reject_renewal(row_idx=1, comment='NCC không đáp ứng')
    out.append(f"  reject_renewal -> {r}")
    fc2.reload()
    out.append(f"  Row status: {fc2.renewal_history[0].approval_status}")

    out.append("")
    out.append("=== TEST 3: Hết hạn quá 90 ngày -> block ===")
    fc3 = frappe.new_doc('Framework Contract')
    fc3.supplier = sup
    fc3.contract_number = f'UC04-R3-{ts}'
    fc3.contract_date = add_days(today(), -250)
    fc3.valid_from = add_days(today(), -200)
    fc3.valid_to = add_days(today(), -100)
    fc3.total_value = 50_000_000
    fc3.append('items', {'item_code': item, 'contract_qty': 1000,
                          'uom': item_uom, 'unit_price': 50000})
    fc3.flags.ignore_permissions = True
    fc3.insert(); fc3.reload()
    fc3.submit_for_review(); fc3.reload()
    fc3.approve_as_manager(); fc3.reload()
    fc3.submit(); fc3.reload()
    out.append(f"  FC {fc3.name}: valid_to={fc3.valid_to}, status={fc3.status}")
    try:
        fc3.request_renewal(new_valid_to=add_days(today(), 30),
                             reason='Test retroactive')
        out.append("  X NOT BLOCKED")
    except frappe.ValidationError as e:
        out.append(f"  OK Block: {str(e)[:100]}")

    out.append("")
    out.append("=== TEST 4: Thanh lý hợp đồng ===")
    fc4 = make_fc('R4', add_days(today(), 60))
    out.append(f"  FC {fc4.name}: status={fc4.status}")
    r = fc4.terminate_contract(reason='NCC vi phạm điều khoản giao hàng')
    out.append(f"  terminate -> {r}")
    fc4.reload()
    out.append(f"  Status={fc4.status}, date={fc4.termination_date}")
    try:
        fc4.request_renewal(new_valid_to=add_days(today(), 365), reason='Test')
        out.append("  X NOT BLOCKED")
    except frappe.ValidationError as e:
        out.append(f"  OK Block renewal sau terminated: {str(e)[:80]}")

    frappe.db.commit()
    return out
