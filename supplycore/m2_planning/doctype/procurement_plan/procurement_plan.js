// Procurement Plan — client script (M2)
frappe.ui.form.on("Procurement Plan", {
    setup(frm) {
        frm.set_query("warehouse", () => ({
            filters: { is_group: 0, disabled: 0 },
        }));
    },

    refresh(frm) {
        // Indicator: tổng ước tính
        if (frm.doc.total_estimated_cost) {
            frm.dashboard.add_indicator(
                __("Tổng ước tính: {0}", [format_currency(frm.doc.total_estimated_cost, "VND")]),
                "blue",
            );
        }
        if (frm.doc.material_request) {
            frm.dashboard.add_indicator(
                __("Đã tạo MR: {0}", [frm.doc.material_request]),
                "green",
            );
        }

        // Action: Auto-load items (Draft)
        if (frm.doc.docstatus === 0 && frm.doc.warehouse) {
            frm.add_custom_button(__("Tự nạp danh mục từ lịch sử tiêu thụ"), () => {
                frappe.confirm(
                    __("Sẽ tự nạp items dựa trên TB tiêu thụ {0} tháng gần nhất + safety stock {1}%. Tiếp tục?",
                       [frm.doc.consumption_lookback_months || 3, frm.doc.safety_stock_factor || 20]),
                    () => {
                        frm.call("auto_load_items").then((r) => {
                            if (r.message) {
                                frappe.show_alert({
                                    message: __("Đã nạp {0} items, ước tính {1}",
                                        [r.message.items_loaded,
                                         format_currency(r.message.total_estimated_cost, "VND")]),
                                    indicator: "green",
                                });
                                frm.reload_doc();
                            }
                        });
                    },
                );
            }, __("Hành động"));
        }

        // Action: Tạo Material Request (Submitted, chưa generate)
        if (frm.doc.docstatus === 1 && frm.doc.status === "Approved" && !frm.doc.material_request) {
            frm.add_custom_button(__("Tạo Material Request"), () => {
                frm.call("make_material_request").then((r) => {
                    if (r.message) {
                        frappe.set_route("Form", "Material Request", r.message);
                    }
                });
            }, __("Tạo"));
        }
    },

    period_type(frm) {
        // Auto-fill from_date / to_date dựa trên period_type
        if (!frm.doc.plan_date) frm.set_value("plan_date", frappe.datetime.get_today());
        const today = frappe.datetime.get_today();
        if (frm.doc.period_type === "Monthly") {
            frm.set_value("from_date", frappe.datetime.month_start());
            frm.set_value("to_date", frappe.datetime.month_end());
        } else if (frm.doc.period_type === "Quarterly") {
            const d = new Date(today);
            const q_start_month = Math.floor(d.getMonth() / 3) * 3;
            frm.set_value("from_date", frappe.datetime.add_months(
                `${d.getFullYear()}-${String(q_start_month + 1).padStart(2, "0")}-01`, 0));
            frm.set_value("to_date", frappe.datetime.add_months(
                `${d.getFullYear()}-${String(q_start_month + 1).padStart(2, "0")}-01`, 3));
        } else if (frm.doc.period_type === "Yearly") {
            frm.set_value("from_date", frappe.datetime.year_start());
            frm.set_value("to_date", frappe.datetime.year_end());
        }
    },
});

frappe.ui.form.on("Procurement Plan Item", {
    planned_qty(frm, cdt, cdn) { _calc_amount(frm, cdt, cdn); },
    estimated_unit_cost(frm, cdt, cdn) { _calc_amount(frm, cdt, cdn); },
});

function _calc_amount(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    row.estimated_amount = (row.planned_qty || 0) * (row.estimated_unit_cost || 0);
    frm.refresh_field("items");
    let total = 0;
    (frm.doc.items || []).forEach((r) => total += (r.estimated_amount || 0));
    frm.set_value("total_estimated_cost", total);
}
