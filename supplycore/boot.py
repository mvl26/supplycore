import frappe


def boot_session(bootinfo):
    """Inject SupplyCore config xuống client-side để FEFO picker, alert đọc trực tiếp."""
    if frappe.session.user == "Guest":
        return
    try:
        settings = frappe.get_single("SupplyCore Settings")
        bootinfo.supplycore = {
            "default_company":            settings.get("default_company"),
            "fefo_min_shelf_life_days":   settings.get("fefo_min_shelf_life_days") or 90,
            "expiry_alert_days":          settings.get("expiry_alert_days") or 180,
            "enforce_fefo":               settings.get("enforce_fefo") or 0,
        }
    except Exception:
        # Settings chưa migrate — bỏ qua
        pass
