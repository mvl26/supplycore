// Stock Entry — SupplyCore client script (M4 bin + M5 FEFO)
frappe.ui.form.on("Stock Entry", {
    refresh(frm) {
        _add_fefo_buttons(frm);
    },
});

frappe.ui.form.on("Stock Entry Detail", {
    item_code(frm, cdt, cdn) { _suggest_fefo(frm, cdt, cdn); },
    qty(frm, cdt, cdn)        { _suggest_fefo(frm, cdt, cdn); },
    s_warehouse(frm, cdt, cdn){ _suggest_fefo(frm, cdt, cdn); },

    sc_fefo_override(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.sc_fefo_override && !row.sc_fefo_override_reason) {
            frappe.prompt(
                {fieldname: "reason", fieldtype: "Small Text",
                 label: __("Lý do override FEFO"), reqd: 1},
                (v) => {
                    row.sc_fefo_override_reason = v.reason;
                    frm.refresh_field("items");
                },
                __("FEFO Override")
            );
        }
    },
});

function _suggest_fefo(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row.item_code || !row.s_warehouse) return;
    if (!["Material Issue", "Material Transfer"].includes(frm.doc.stock_entry_type)) return;

    frappe.call({
        method: "supplycore.api.fefo.get_suggested_batches",
        args: {
            item_code: row.item_code,
            warehouse: row.s_warehouse,
            qty: row.qty || 0,
        },
        callback(r) {
            if (!r.message || !r.message.batches || !r.message.batches.length) return;
            const top = r.message.batches[0];

            // Auto-fill nếu user chưa chọn batch
            if (!row.batch_no) {
                row.batch_no = top.batch_no;
                frm.refresh_field("items");
            }

            // Cảnh báo expiry
            if (top.severity === "Critical") {
                frappe.show_alert({
                    message: __("⚠ Lô FEFO {0}: chỉ còn {1} ngày", [top.batch_no, top.days_to_expiry]),
                    indicator: "red",
                });
            } else if (top.severity === "Warning") {
                frappe.show_alert({
                    message: __("ℹ Lô FEFO {0}: còn {1} ngày", [top.batch_no, top.days_to_expiry]),
                    indicator: "orange",
                });
            }
        },
    });
}

function _add_fefo_buttons(frm) {
    if (frm.doc.docstatus !== 0) return;
    if (!["Material Issue", "Material Transfer"].includes(frm.doc.stock_entry_type)) return;

    frm.add_custom_button(__("Mở FEFO Picker"), () => {
        const items = frm.doc.items || [];
        if (!items.length) {
            frappe.msgprint(__("Thêm item trước"));
            return;
        }
        // Show panel with FEFO suggestions for each item
        const item_codes = items.map(i => i.item_code).filter(Boolean);
        frappe.msgprint({
            title: __("FEFO Suggestions"),
            indicator: "blue",
            message: __("Đang query FEFO cho {0} items...", [item_codes.length]),
        });
        // For each row, fetch FEFO suggestions
        items.forEach((row, idx) => {
            if (!row.item_code || !row.s_warehouse) return;
            frappe.call({
                method: "supplycore.api.fefo.get_suggested_batches",
                args: {item_code: row.item_code, warehouse: row.s_warehouse, qty: row.qty || 0},
                callback(r) {
                    if (!r.message) return;
                    const top = (r.message.batches || []).slice(0, 3);
                    const lines = top.map(b =>
                        `${b.batch_no} | hạn ${b.expiry_date || 'N/A'} | còn ${b.available_qty} | severity ${b.severity}`
                    ).join("<br>");
                    frappe.show_alert({
                        message: `Item ${row.item_code}:<br>${lines || 'Không có batch khả dụng'}`,
                        indicator: "blue",
                    });
                },
            });
        });
    }, __("M5 FEFO"));
}
