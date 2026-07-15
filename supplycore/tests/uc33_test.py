"""Test UC-33 — Alert Configuration.

Run individual: bench --site supplycore execute supplycore.tests.uc33_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc33_test.run
"""

import frappe
from frappe.utils import random_string


def _make_rule(**kwargs):
    rule = frappe.new_doc("SC Alert Rule")
    rule.title = kwargs.get("title", f"UC33-rule-{random_string(5)}")
    rule.alert_type = kwargs.get("alert_type", "low_stock")
    rule.severity = kwargs.get("severity", "Warning")
    rule.enabled = kwargs.get("enabled", 1)
    rule.frequency = kwargs.get("frequency", "Daily")
    rule.threshold_value = kwargs.get("threshold_value", 30)
    rule.threshold_operator = kwargs.get("threshold_operator", "<=")
    rule.threshold_unit = kwargs.get("threshold_unit", "days")
    rule.channel_email = kwargs.get("channel_email", 1)
    rule.channel_inapp = kwargs.get("channel_inapp", 1)
    rule.channel_sms = kwargs.get("channel_sms", 0)
    rule.sms_phones = kwargs.get("sms_phones", None)
    rule.recipient_roles = kwargs.get("recipient_roles", "SupplyCore Manager")
    rule.extra_emails = kwargs.get("extra_emails", None)
    if "scheduled_time" in kwargs:
        rule.scheduled_time = kwargs["scheduled_time"]
    if "day_of_week" in kwargs:
        rule.day_of_week = kwargs["day_of_week"]
    rule.flags.ignore_permissions = True
    return rule


# ---------- Tests ----------

def test_alert_rule_validates_no_channel():
    """Không tick channel nào → throw SC-E-AR-NO-CHANNEL."""
    rule = _make_rule(channel_email=0, channel_inapp=0, channel_sms=0)
    try:
        rule.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X insert thành công không có channel"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "SC-E-AR-NO-CHANNEL" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_alert_rule_validates_sms_no_phones():
    """channel_sms=1 + sms_phones rỗng → throw."""
    rule = _make_rule(channel_sms=1, sms_phones="")
    try:
        rule.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X SMS bật không có phones"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "SC-E-AR-SMS-NO-PHONES" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_alert_rule_validates_no_recipient():
    """recipient_roles + extra_emails + sms_phones đều rỗng → throw."""
    rule = _make_rule(recipient_roles="", extra_emails="",
                       channel_sms=0, channel_email=1, channel_inapp=1)
    try:
        rule.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X insert no recipient"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "SC-E-AR-NO-RECIPIENT" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_test_alert_rule_inapp_creates_sc_alert():
    """channel_inapp=1 → test tạo SC Alert '[TEST]'."""
    rule = _make_rule(channel_email=0, channel_inapp=1, channel_sms=0,
                       extra_emails="dummy@example.com")
    rule.insert()
    try:
        res = rule.test_alert_rule()
        alert_name = res["results"]["inapp"]["alert"]
        alert = frappe.db.get_value("SC Alert", alert_name,
                                     ["title", "alert_rule"], as_dict=True)
        frappe.db.rollback()
        if (alert and "[TEST]" in alert["title"]
            and alert["alert_rule"] == rule.name):
            return {"pass": True, "msg": f"OK SC Alert created"}
        return {"pass": False, "msg": f"X alert={alert}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_test_alert_rule_sms_no_gateway_fails():
    """channel_sms=1, sms_gateway_endpoint rỗng → results.sms.status=Failed."""
    # Đảm bảo gateway = empty
    frappe.db.set_single_value("SupplyCore Settings", "sms_gateway_endpoint", "")
    rule = _make_rule(channel_email=0, channel_inapp=0,
                       channel_sms=1, sms_phones="0901111111")
    rule.insert()
    try:
        res = rule.test_alert_rule()
        frappe.db.rollback()
        sms_res = res["results"]["sms"]
        if (sms_res and sms_res["status"] == "Failed"
            and "gateway" in sms_res["error"].lower()):
            return {"pass": True, "msg": "OK SMS failed (no gateway)"}
        return {"pass": False, "msg": f"X sms={sms_res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_test_alert_rule_persists_last_test():
    """Sau test → last_test_at + status set trong DB."""
    rule = _make_rule(channel_email=0, channel_inapp=1, channel_sms=0,
                       extra_emails="dummy@example.com")
    rule.insert()
    try:
        rule.test_alert_rule()
        # reload to read DB values
        rule.reload()
        frappe.db.rollback()
        if rule.last_test_at and rule.last_test_status in ("Success", "Partial", "Failed"):
            return {"pass": True, "msg": f"OK status={rule.last_test_status}"}
        return {"pass": False, "msg": f"X at={rule.last_test_at} status={rule.last_test_status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_test_alert_rule_sms_only_status_failed():
    """Chỉ SMS bật và fail → overall status=Failed."""
    frappe.db.set_single_value("SupplyCore Settings", "sms_gateway_endpoint", "")
    rule = _make_rule(channel_email=0, channel_inapp=0,
                       channel_sms=1, sms_phones="0901234567")
    rule.insert()
    try:
        res = rule.test_alert_rule()
        frappe.db.rollback()
        if res["status"] == "Failed":
            return {"pass": True, "msg": "OK overall=Failed"}
        return {"pass": False, "msg": f"X status={res['status']}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_test_alert_rule_sms_partial_when_other_ok():
    """SMS fail + In-app OK → overall status=Partial."""
    frappe.db.set_single_value("SupplyCore Settings", "sms_gateway_endpoint", "")
    rule = _make_rule(channel_email=0, channel_inapp=1,
                       channel_sms=1, sms_phones="0901234567")
    rule.insert()
    try:
        res = rule.test_alert_rule()
        frappe.db.rollback()
        if res["status"] == "Partial":
            return {"pass": True, "msg": "OK Partial"}
        return {"pass": False, "msg": f"X status={res['status']}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_weekly_frequency_with_day_of_week():
    """frequency=Weekly + day_of_week=Mon → save OK."""
    rule = _make_rule(frequency="Weekly", day_of_week="Mon",
                       scheduled_time="08:00:00")
    try:
        rule.insert()
        rule.reload()
        frappe.db.rollback()
        if rule.frequency == "Weekly" and rule.day_of_week == "Mon":
            return {"pass": True, "msg": "OK Weekly+Mon"}
        return {"pass": False, "msg": f"X freq={rule.frequency} dow={rule.day_of_week}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_scheduled_time_default_8am():
    """scheduled_time mặc định 08:00:00 khi tạo mới."""
    rule = _make_rule()
    try:
        rule.insert()
        rule.reload()
        frappe.db.rollback()
        st = str(rule.scheduled_time or "")
        # Accept both "08:00:00" and "8:00:00"
        if st.startswith(("08:00", "8:00")):
            return {"pass": True, "msg": f"OK scheduled_time={st}"}
        return {"pass": False, "msg": f"X st={st}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_resolve_email_recipients_dedup():
    """role + extra_email overlap → emails dedup."""
    # Add a test user with SupplyCore Manager role
    email = f"uc33-dedup-{random_string(5)}@example.com"
    u = frappe.new_doc("User")
    u.email = email; u.first_name = "UC33"
    u.send_welcome_email = 0; u.enabled = 1
    u.append("roles", {"role": "SupplyCore Manager"})
    u.flags.ignore_permissions = True
    u.insert()
    rule = _make_rule(recipient_roles="SupplyCore Manager",
                       extra_emails=email)
    rule.insert()
    try:
        recipients = rule._resolve_email_recipients()
        frappe.db.rollback()
        # email should appear once even though in both role and extra
        count = sum(1 for r in recipients if r == email)
        if count == 1:
            return {"pass": True, "msg": "OK deduped"}
        return {"pass": False, "msg": f"X count={count} list={recipients[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dispatch_alert_notifications_no_throw():
    """dispatch không throw ngay cả khi alert minimal."""
    rule = _make_rule(channel_email=0, channel_inapp=1, channel_sms=0,
                       extra_emails="dummy@example.com")
    rule.insert()
    a = frappe.new_doc("SC Alert")
    a.alert_date = frappe.utils.now()
    a.alert_rule = rule.name
    a.alert_type = rule.alert_type
    a.severity = "Warning"
    a.title = "Dispatch test"
    a.message = "Body"
    a.flags.ignore_permissions = True
    a.insert()
    try:
        rule.dispatch_alert_notifications(a)
        frappe.db.rollback()
        return {"pass": True, "msg": "OK dispatch no throw"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_alert_rule_validates_no_channel,
        test_alert_rule_validates_sms_no_phones,
        test_alert_rule_validates_no_recipient,
        test_test_alert_rule_inapp_creates_sc_alert,
        test_test_alert_rule_sms_no_gateway_fails,
        test_test_alert_rule_persists_last_test,
        test_test_alert_rule_sms_only_status_failed,
        test_test_alert_rule_sms_partial_when_other_ok,
        test_weekly_frequency_with_day_of_week,
        test_scheduled_time_default_8am,
        test_resolve_email_recipients_dedup,
        test_dispatch_alert_notifications_no_throw,
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
