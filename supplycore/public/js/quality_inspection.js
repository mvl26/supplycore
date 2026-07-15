// Quality Inspection — SupplyCore client script (M3)
frappe.ui.form.on("Quality Inspection", {
    refresh(frm) {
        _add_template_button(frm);
        _add_quick_actions(frm);
        _render_summary(frm);
    },

    sc_checklist_template(frm) {
        if (frm.doc.sc_checklist_template && frm.doc.docstatus === 0) {
            _load_template_into_readings(frm);
        }
    },
});

frappe.ui.form.on("Quality Inspection Reading", {
    status(frm, cdt, cdn) {
        // Khi user mark Pass/Fail → tự suggest QI status
        _suggest_qi_status(frm);
    },
});

function _add_template_button(frm) {
    if (frm.doc.docstatus !== 0) return;
    frm.add_custom_button(__("Nạp checklist từ template"), () => {
        if (!frm.doc.sc_checklist_template) {
            frappe.msgprint(__("Chọn template trước"));
            return;
        }
        _load_template_into_readings(frm);
    }, __("Hành động"));
}

function _load_template_into_readings(frm) {
    frappe.db.get_doc("QC Checklist Template", frm.doc.sc_checklist_template).then((tpl) => {
        const criteria = (tpl.criteria || []).slice().sort((a, b) => (a.sequence || 0) - (b.sequence || 0));
        frm.clear_table("readings");
        frm.set_value("manual_inspection", 1);  // bỏ qua auto-status logic
        criteria.forEach((c) => {
            const row = frm.add_child("readings");
            row.specification = c.criterion_name;
            row.manual_inspection = 1;
            row.numeric = 0;
            row.status = "";
        });
        frm.refresh_field("readings");
        frappe.show_alert({
            message: __("Đã nạp {0} tiêu chí", [criteria.length]),
            indicator: "green",
        });
    });
}

function _suggest_qi_status(frm) {
    const readings = frm.doc.readings || [];
    if (!readings.length) return;
    const has_rejected = readings.some((r) => r.status === "Rejected");
    const all_filled = readings.every((r) => r.status);
    if (!all_filled) return;
    const new_status = has_rejected ? "Rejected" : "Accepted";
    if (frm.doc.status !== new_status) {
        frm.set_value("status", new_status);
        frappe.show_alert({
            message: __("Auto-set Status = {0} dựa trên checklist", [new_status]),
            indicator: has_rejected ? "red" : "green",
        });
    }
}

function _render_summary(frm) {
    const readings = frm.doc.readings || [];
    if (!readings.length) return;
    const passed = readings.filter((r) => r.status === "Accepted").length;
    const failed = readings.filter((r) => r.status === "Rejected").length;
    const pending = readings.length - passed - failed;
    frm.dashboard.add_indicator(
        __("Pass: {0} / Fail: {1} / Pending: {2}", [passed, failed, pending]),
        failed > 0 ? "red" : pending > 0 ? "orange" : "green",
    );
}

function _add_quick_actions(frm) {
    if (frm.doc.docstatus !== 0) return;
    frm.add_custom_button(__("Mark all PASS"), () => {
        (frm.doc.readings || []).forEach((r) => {
            if (!r.status) r.status = "Accepted";
        });
        frm.refresh_field("readings");
        _suggest_qi_status(frm);
    }, __("QC"));
}
