// Release Order — client script (M1)
frappe.ui.form.on("Release Order", {
    setup(frm) {
        // Lọc HĐK: chỉ HĐK Active (đã submit, chưa hết hạn)
        frm.set_query("framework_contract", () => ({
            filters: {
                docstatus: 1,
                status: "Active",
            },
        }));
    },

    refresh(frm) {
        // Indicator HĐK còn lại
        if (frm.doc.framework_contract) {
            frappe.db.get_value(
                "Framework Contract",
                frm.doc.framework_contract,
                ["total_value", "used_value", "committed_value", "remaining_value", "valid_to"]
            ).then((r) => {
                if (!r.message) return;
                const m = r.message;
                const pct = m.total_value ? (m.remaining_value / m.total_value) * 100 : 0;
                const color = pct < 20 ? "red" : pct < 40 ? "orange" : "green";
                frm.dashboard.add_indicator(
                    __("HĐK còn lại: {0} ({1}%)", [
                        format_currency(m.remaining_value, "VND"),
                        pct.toFixed(1),
                    ]),
                    color,
                );
                if (m.committed_value) {
                    frm.dashboard.add_indicator(
                        __("HĐK đang gọi (RO): {0}", [format_currency(m.committed_value, "VND")]),
                        "yellow",
                    );
                }
            });
        }

        // Button: Tạo Purchase Order
        if (frm.doc.docstatus === 1 && frm.doc.status === "Approved" && !frm.doc.purchase_order) {
            frm.add_custom_button(__("Tạo Purchase Order"), () => {
                frm.call("make_purchase_order").then((r) => {
                    if (r.message) {
                        frappe.set_route("Form", "Purchase Order", r.message);
                    }
                });
            }, __("Tạo"));
        }

        // Button: Bulk-fill remaining qty từ HĐK (cho draft)
        if (frm.doc.docstatus === 0 && frm.doc.framework_contract) {
            frm.add_custom_button(__("Lấy SL còn lại từ HĐK"), () => {
                _fill_items_from_fc(frm, /* useRemaining */ true);
            }, __("Hành động"));
        }

        if (frm.doc.purchase_order) {
            frm.dashboard.add_indicator(
                __("Đã tạo PO: {0}", [frm.doc.purchase_order]),
                "blue",
            );
        }
    },

    framework_contract(frm) {
        // Auto-fetch items từ HĐK khi user chọn FC
        if (!frm.doc.framework_contract) return;
        if (frm.doc.docstatus !== 0) return;  // chỉ auto-fill ở Draft

        // Nếu đã có items: confirm trước khi overwrite
        const has_items = (frm.doc.items || []).some((r) => r.item_code);
        if (has_items) {
            frappe.confirm(
                __("Đã có vật tư trong bảng. Lấy lại từ HĐK sẽ ghi đè. Tiếp tục?"),
                () => _fill_items_from_fc(frm, /* useRemaining */ false),
            );
        } else {
            _fill_items_from_fc(frm, /* useRemaining */ false);
        }
    },
});

function _fill_items_from_fc(frm, useRemaining) {
    if (!frm.doc.framework_contract) return;
    frappe.call({
        method: "frappe.client.get",
        args: { doctype: "Framework Contract", name: frm.doc.framework_contract },
        callback(r) {
            if (!r.message) return;
            const fc = r.message;
            frm.clear_table("items");
            (fc.items || []).forEach((fci) => {
                if ((fci.remaining_qty || 0) <= 0) return;  // bỏ qua item đã hết qty
                const row = frm.add_child("items");
                row.fc_item        = fci.name;
                row.item_code      = fci.item_code;
                row.item_name      = fci.item_name;
                row.uom            = fci.uom;
                row.unit_price     = fci.unit_price;
                row.available_qty  = fci.remaining_qty;
                row.qty            = useRemaining ? fci.remaining_qty : 0;
                row.amount         = (row.qty || 0) * (row.unit_price || 0);
            });
            frm.refresh_field("items");
            _recompute_total(frm);
            frappe.show_alert({
                message: __("Đã nạp {0} vật tư từ HĐK", [(fc.items || []).length]),
                indicator: "green",
            });
        },
    });
}

frappe.ui.form.on("RO Item", {
    item_code(frm, cdt, cdn) { _fetch_fc_price(frm, cdt, cdn); },
    qty(frm, cdt, cdn)        { _calc_amount(frm, cdt, cdn); },
});

function _fetch_fc_price(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!frm.doc.framework_contract || !row.item_code) return;
    frappe.call({
        method: "frappe.client.get",
        args: { doctype: "Framework Contract", name: frm.doc.framework_contract },
        callback(r) {
            const fc = r.message;
            const fci = (fc.items || []).find((x) => x.item_code === row.item_code);
            if (!fci) {
                frappe.msgprint({
                    title: __("Vật tư không thuộc HĐK"),
                    message: __("Vật tư {0} không có trong hợp đồng khung này", [row.item_code]),
                    indicator: "red",
                });
                row.item_code = null;
                frm.refresh_field("items");
                return;
            }
            row.fc_item       = fci.name;
            row.uom           = fci.uom;
            row.unit_price    = fci.unit_price;
            row.available_qty = fci.remaining_qty;
            _calc_amount(frm, cdt, cdn);
        },
    });
}

function _calc_amount(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    row.amount = (row.qty || 0) * (row.unit_price || 0);
    frm.refresh_field("items");
    _recompute_total(frm);
}

function _recompute_total(frm) {
    let total = 0;
    (frm.doc.items || []).forEach((r) => total += (r.amount || 0));
    frm.set_value("total_amount", total);
}
