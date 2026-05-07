// Framework Contract — client script (M1)
frappe.ui.form.on("Framework Contract", {
    refresh(frm) {
        _render_indicators(frm);
        _add_action_buttons(frm);
    },

    supplier(frm) {
        if (frm.doc.supplier) {
            frm.set_value("supplier_name", null);
        }
    },

    valid_from(frm) { _check_dates(frm); },
    valid_to(frm)   { _check_dates(frm); },
});

function _render_indicators(frm) {
    if (frm.doc.docstatus !== 1) return;

    const total = frm.doc.total_value || 0;
    const used = frm.doc.used_value || 0;
    const committed = frm.doc.committed_value || 0;
    const remaining = frm.doc.remaining_value || 0;
    const pct_remaining = total ? (remaining / total) * 100 : 0;
    const color = pct_remaining < 20 ? "red" : pct_remaining < 40 ? "orange" : "green";

    frm.dashboard.add_indicator(
        __("Đã sử dụng (PO): {0}", [format_currency(used, "VND")]),
        "blue",
    );
    frm.dashboard.add_indicator(
        __("Đang gọi (RO): {0}", [format_currency(committed, "VND")]),
        "yellow",
    );
    frm.dashboard.add_indicator(
        __("Còn lại: {0} ({1}%)", [format_currency(remaining, "VND"), pct_remaining.toFixed(1)]),
        color,
    );

    if (frm.doc.expiring_soon) {
        frm.dashboard.set_headline_alert(
            `<div class="indicator orange">${__("Hợp đồng sắp hết hạn — kiểm tra và gia hạn")}</div>`,
        );
    }
}

function _add_action_buttons(frm) {
    if (frm.doc.docstatus !== 1) return;

    // Tạo Release Order — hiện cho cả Active và Draft (chưa tới valid_from)
    if (["Active", "Draft"].includes(frm.doc.status)) {
        frm.add_custom_button(__("Tạo Release Order"), () => {
            frappe.new_doc("Release Order", {
                framework_contract: frm.doc.name,
            });
        }, __("Tạo"));
    }

    // Recalculate
    frm.add_custom_button(__("Tính lại giá trị"), () => {
        frm.call("recalculate_used_value").then(() => {
            frm.reload_doc();
            frappe.show_alert({ message: __("Đã tính lại"), indicator: "green" });
        });
    }, __("Hành động"));
}

function _check_dates(frm) {
    if (frm.doc.valid_from && frm.doc.valid_to) {
        if (frm.doc.valid_to <= frm.doc.valid_from) {
            frappe.msgprint({
                title: __("Lỗi ngày"),
                message: __("Ngày hết hạn phải sau ngày hiệu lực"),
                indicator: "red",
            });
            frm.set_value("valid_to", null);
        }
    }
}

frappe.ui.form.on("FC Item", {
    contract_qty(frm, cdt, cdn) { _calc_amount(frm, cdt, cdn); },
    unit_price(frm, cdt, cdn)   { _calc_amount(frm, cdt, cdn); },
});

function _calc_amount(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    row.total_amount = (row.contract_qty || 0) * (row.unit_price || 0);
    frm.refresh_field("items");
}
