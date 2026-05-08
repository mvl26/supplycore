// SC Material Request — UI: button "Tạo PO từ HĐK" sau submit
frappe.ui.form.on("SC Material Request", {
    refresh(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.status !== "Cancelled") {
            // Preview action — non-destructive
            frm.add_custom_button(__("Xem gợi ý PO từ HĐK"), () => {
                frm.call("get_po_suggestion").then(r => {
                    if (!r.message) return;
                    const m = r.message;
                    let html = `<h4>Có ${m.groups.length} nhóm theo (NCC × HĐK)</h4>`;
                    if (m.groups.length) {
                        html += `<table class="table table-bordered"><thead>
                            <tr><th>NCC</th><th>HĐK</th><th>Items</th><th>Tổng tiền</th></tr></thead><tbody>`;
                        m.groups.forEach(g => {
                            html += `<tr><td>${g.supplier}</td><td>${g.framework_contract}</td>
                                     <td>${g.items.length}</td>
                                     <td>${format_currency(g.subtotal)}</td></tr>`;
                        });
                        html += `</tbody></table>`;
                    }
                    if (m.unmatched_items && m.unmatched_items.length) {
                        html += `<h5 class="text-warning">Items không match HĐK</h5><ul>`;
                        m.unmatched_items.forEach(u => {
                            html += `<li>${u.item} (${u.qty} ${u.uom || ''}) — ${u.reason}</li>`;
                        });
                        html += `</ul>`;
                    }
                    frappe.msgprint({title: __("Gợi ý PO"), message: html, wide: true});
                });
            }, __("Hành động"));

            // Destructive action — confirm
            frm.add_custom_button(__("Tạo Purchase Order"), () => {
                frappe.confirm(
                    __("Tạo draft Purchase Order từ MR này (theo HĐK Active)?"),
                    () => {
                        frm.call("create_purchase_orders").then(r => {
                            const m = r.message || {};
                            if (m.created_pos && m.created_pos.length) {
                                frappe.show_alert({
                                    message: __("Đã tạo {0} PO: {1}",
                                        [m.created_pos.length, m.created_pos.join(", ")]),
                                    indicator: "green",
                                }, 7);
                                frm.reload_doc();
                            } else {
                                frappe.msgprint(__("Không có item nào match HĐK Active."));
                            }
                        });
                    }
                );
            }, __("Hành động")).addClass("btn-primary");
        }
    },
});
