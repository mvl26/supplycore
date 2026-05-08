// SC Alert — UI: action button context-sensitive theo alert_type
frappe.ui.form.on("SC Alert", {
    refresh(frm) {
        if (frm.is_new()) return;

        // Hiển thị link sang document đã tạo (nếu có)
        if (frm.doc.action_taken && frm.doc.action_doctype && frm.doc.action_name) {
            frm.add_custom_button(
                __("Mở {0}", [frm.doc.action_doctype]),
                () => frappe.set_route("Form", frm.doc.action_doctype, frm.doc.action_name),
                __("Đã thực hiện"),
            );
            return;
        }

        if (frm.doc.resolved) return;

        const action_map = {
            expiring_batch: {
                label: __("Chuyển vào Kho Cách ly"),
                method: "action_quarantine_batch",
                target: __("Stock Entry"),
                indicator: "orange",
            },
            low_stock: {
                label: __("Tạo Material Request bổ sung"),
                method: "action_create_material_request",
                target: __("Material Request"),
                indicator: "blue",
            },
            overdue_payment: {
                label: __("Tạo Payment Entry"),
                method: "action_create_payment",
                target: __("Payment Entry"),
                indicator: "red",
            },
        };

        const cfg = action_map[frm.doc.alert_type];
        if (!cfg) {
            // Cho mọi alert type khác — chỉ button generic Mark Resolved
            frm.add_custom_button(__("Đánh dấu đã xử lý"), () => {
                frm.set_value("resolved", 1);
                frm.set_value("resolution_action", "Acknowledged");
                frm.save();
            });
            return;
        }

        frm.add_custom_button(cfg.label, () => {
            frappe.confirm(
                __("Tạo {0} từ alert này? Alert sẽ được đánh dấu Resolved.", [cfg.target]),
                () => {
                    frm.call(cfg.method).then(r => {
                        if (r.message) {
                            frappe.show_alert({
                                message: __("Đã tạo {0}: {1}", [cfg.target, r.message]),
                                indicator: "green",
                            }, 5);
                            // Navigate sang doc mới sau 1s
                            setTimeout(() => {
                                frappe.set_route("Form", frm.doc.action_doctype || cfg.target.replace(" ", "%20"),
                                                  r.message);
                            }, 800);
                        }
                    });
                },
            );
        }, __("Hành động")).addClass("btn-primary");

        // Phụ: dismiss
        frm.add_custom_button(__("Bỏ qua (Dismiss)"), () => {
            frm.set_value("resolved", 1);
            frm.set_value("resolution_action", "Dismissed");
            frm.save();
        }, __("Hành động"));
    },
});
