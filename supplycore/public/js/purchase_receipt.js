// Purchase Receipt — SupplyCore client script (M3)
frappe.ui.form.on("Purchase Receipt", {
    refresh(frm) {
        _render_qc_indicator(frm);
        _add_qc_buttons(frm);
    },
});

function _render_qc_indicator(frm) {
    if (frm.doc.docstatus !== 1) return;
    if (!frm.doc.sc_qc_status) return;

    const colorMap = {
        "Pending":      "orange",
        "Pass":         "green",
        "Partial Pass": "yellow",
        "Fail":         "red",
    };
    const color = colorMap[frm.doc.sc_qc_status] || "blue";
    frm.dashboard.add_indicator(__("QC: {0}", [frm.doc.sc_qc_status]), color);
}

function _add_qc_buttons(frm) {
    if (frm.doc.docstatus !== 1 || frm.doc.is_return) return;

    // Button: Mở danh sách QI của PR này
    frm.add_custom_button(__("Xem Quality Inspections"), () => {
        frappe.set_route("List", "Quality Inspection", {
            reference_type: "Purchase Receipt",
            reference_name: frm.doc.name,
        });
    }, __("QC"));

    // Button: Tạo phiếu trả NCC nếu QC Fail
    if (frm.doc.sc_qc_status === "Fail" || frm.doc.sc_qc_status === "Partial Pass") {
        frm.add_custom_button(__("Tạo phiếu trả NCC"), () => {
            frappe.model.open_mapped_doc({
                method: "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_return",
                frm: frm,
            });
        }, __("QC"));
    }
}
