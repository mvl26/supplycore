"""Test UC-23 — BHYT Code Config management.

Run individual: bench --site supplycore execute supplycore.tests.uc23_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc23_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC23-{suffix}-{random_string(5)}"
    item.item_name = f"UC-23 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.is_medical_supply = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_cfg(item=None, item_group=None, **kwargs):
    cfg = frappe.new_doc("SC BHYT Code Config")
    cfg.bhyt_code = kwargs.get("bhyt_code", f"UC23-{random_string(5)}")
    cfg.bhyt_name = kwargs.get("bhyt_name", f"UC-23 BHYT {random_string(4)}")
    cfg.bhyt_group = kwargs.get("bhyt_group", "N01")
    cfg.payment_rate = kwargs.get("payment_rate", 80)
    cfg.effective_from = kwargs.get("effective_from", today())
    if kwargs.get("effective_to"):
        cfg.effective_to = kwargs["effective_to"]
    if "is_active" in kwargs:
        cfg.is_active = kwargs["is_active"]
    if item:
        cfg.item = item
    if item_group:
        cfg.item_group = item_group
    if "ceiling_price" in kwargs:
        cfg.ceiling_price = kwargs["ceiling_price"]
    cfg.flags.ignore_permissions = True
    return cfg


# ---------- Tests ----------

def test_bhyt_create_basic():
    """Tạo config với item + rate 80% → save OK."""
    item = _make_item("BASIC")
    cfg = _make_cfg(item=item.name, payment_rate=80)
    try:
        cfg.insert()
        ok = (cfg.name and cfg.payment_rate == 80)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK {cfg.name}"}
        return {"pass": False, "msg": f"X"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_bhyt_rate_over_100_blocked():
    """rate=120 → throw SC-E-BHYT-RATE."""
    item = _make_item("RATE")
    cfg = _make_cfg(item=item.name, payment_rate=120)
    try:
        cfg.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-BHYT-RATE" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_bhyt_rate_negative_blocked():
    """rate=-10 → throw."""
    item = _make_item("NEGR")
    cfg = _make_cfg(item=item.name, payment_rate=-10)
    try:
        cfg.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-BHYT-RATE" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_bhyt_requires_item_or_group():
    """Không item + không group → throw."""
    cfg = _make_cfg()  # no item, no group
    try:
        cfg.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "Item" in msg or "Group" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_bhyt_effective_to_before_from():
    """effective_to < effective_from → throw."""
    item = _make_item("DATES")
    cfg = _make_cfg(
        item=item.name,
        effective_from=today(),
        effective_to=add_days(today(), -10),
    )
    try:
        cfg.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "hiệu lực" in msg.lower():
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_bhyt_overlap_same_item_blocked():
    """2 configs cùng item + date overlap → SC-E-BHYT-OVERLAP."""
    item = _make_item("OVLP")
    cfg1 = _make_cfg(item=item.name,
                     effective_from=add_days(today(), -30),
                     effective_to=add_days(today(), 30))
    cfg1.insert()
    cfg2 = _make_cfg(item=item.name,
                     effective_from=today(),
                     effective_to=add_days(today(), 60))
    try:
        cfg2.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-BHYT-OVERLAP" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_bhyt_overlap_close_old_allows_new():
    """Close bản cũ + tạo bản mới sau → OK."""
    item = _make_item("CLOSE")
    cfg_old = _make_cfg(item=item.name,
                         effective_from=add_days(today(), -60),
                         effective_to=add_days(today(), -10))
    cfg_old.insert()
    cfg_new = _make_cfg(item=item.name,
                         effective_from=add_days(today(), -5),
                         effective_to=add_days(today(), 60))
    try:
        cfg_new.insert()
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK new config created sau old close"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_bhyt_inactive_no_overlap_check():
    """is_active=0 → không check overlap."""
    item = _make_item("INACT")
    cfg1 = _make_cfg(item=item.name,
                     effective_from=today(),
                     effective_to=add_days(today(), 60))
    cfg1.insert()
    cfg2 = _make_cfg(item=item.name,
                     effective_from=today(),
                     effective_to=add_days(today(), 60),
                     is_active=0)
    try:
        cfg2.insert()
        frappe.db.rollback()
        return {"pass": True, "msg": "OK inactive config skipped overlap check"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_list_bhyt_configs_for_item():
    """Tạo 2 configs khác kỳ → list trả 2 records."""
    from supplycore.api.bhyt import list_bhyt_configs_for_item
    item = _make_item("LIST")
    cfg1 = _make_cfg(item=item.name,
                     effective_from=add_days(today(), -120),
                     effective_to=add_days(today(), -60))
    cfg1.insert()
    cfg2 = _make_cfg(item=item.name,
                     effective_from=add_days(today(), -30))
    cfg2.insert()
    try:
        res = list_bhyt_configs_for_item(item.name)
        frappe.db.rollback()
        if res["count"] >= 2:
            return {"pass": True, "msg": f"OK count={res['count']}"}
        return {"pass": False, "msg": f"X count={res['count']}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_active_config_picks_latest():
    """2 configs khác kỳ → get_active_config trả bản hiện hành."""
    from supplycore.api.bhyt import get_active_config
    item = _make_item("LATEST")
    cfg_old = _make_cfg(item=item.name,
                         payment_rate=70,
                         effective_from=add_days(today(), -120),
                         effective_to=add_days(today(), -60))
    cfg_old.insert()
    cfg_curr = _make_cfg(item=item.name,
                          payment_rate=85,
                          effective_from=add_days(today(), -30))
    cfg_curr.insert()
    try:
        active = get_active_config(item.name, on_date=today())
        frappe.db.rollback()
        if active and active.get("payment_rate") == 85:
            return {"pass": True, "msg": f"OK active rate=85"}
        return {"pass": False, "msg": f"X active={active}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_bhyt_create_basic,
        test_bhyt_rate_over_100_blocked,
        test_bhyt_rate_negative_blocked,
        test_bhyt_requires_item_or_group,
        test_bhyt_effective_to_before_from,
        test_bhyt_overlap_same_item_blocked,
        test_bhyt_overlap_close_old_allows_new,
        test_bhyt_inactive_no_overlap_check,
        test_list_bhyt_configs_for_item,
        test_get_active_config_picks_latest,
    ]
    results = []
    for t in tests:
        try:
            r = t()
            r["test"] = t.__name__
        except Exception as e:
            r = {"test": t.__name__, "pass": False, "msg": f"EXCEPTION: {str(e)[:200]}"}
        results.append(r)
    frappe.db.rollback()
    passed = sum(1 for r in results if r.get("pass"))
    return {"passed": passed, "total": len(results), "results": results}
