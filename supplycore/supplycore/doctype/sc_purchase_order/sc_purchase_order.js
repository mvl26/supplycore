// SC Purchase Order — UI: button "Tạo Purchase Receipt" sau submit (chưa nhận đủ)
frappe.ui.form.on("SC Purchase Order", {
    refresh(frm) {
        if (frm.doc.docstatus !== 1) return;
        if (frm.doc.status === "Received" || frm.doc.status === "Cancelled") return;

        frm.add_custom_button(__("Tạo Purchase Receipt"), () => {
            frappe.call({
                method: "supplycore.supplycore.doctype.sc_purchase_order.sc_purchase_order.make_pr_from_po",
                args: {po_name: frm.doc.name},
                callback: r => {
                    if (r.message) {
                        frappe.show_alert({
                            message: __("Đã tạo PR draft: {0}", [r.message]),
                            indicator: "green",
                        }, 5);
                        frappe.set_route("Form", "SC Purchase Receipt", r.message);
                    }
                },
            });
        }, __("Hành động")).addClass("btn-primary");
    },
});
