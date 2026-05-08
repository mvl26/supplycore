// SC Purchase Receipt — UI: button "Tạo Purchase Invoice" sau khi QC Accepted
frappe.ui.form.on("SC Purchase Receipt", {
    refresh(frm) {
        if (frm.doc.docstatus === 1
            && frm.doc.qc_status !== "Rejected"
            && !frm.doc.is_return) {
            frm.add_custom_button(__("Tạo Purchase Invoice"), () => {
                frappe.call({
                    method: "supplycore.m8_accounting.doctype.sc_purchase_invoice.sc_purchase_invoice.make_invoice_from_pr",
                    args: {pr_name: frm.doc.name},
                    callback: r => {
                        if (r.message) {
                            frappe.set_route("Form", "SC Purchase Invoice", r.message);
                        }
                    }
                });
            }, __("Hành động")).addClass("btn-primary");
        }
    },
});
