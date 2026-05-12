// Framework Contract — client script (M1) + UC-03 approval workflow
frappe.ui.form.on("Framework Contract", {
    refresh(frm) {
        _render_indicators(frm);
        _add_approval_buttons(frm);
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

function _add_approval_buttons(frm) {
    if (frm.is_new()) return;
    if (frm.doc.docstatus === 1) return;  // đã submit, không show approval button
    if (frm.doc.docstatus === 2) return;  // cancelled

    const stage = frm.doc.approval_stage || "Draft";
    const roles = frappe.user_roles || [];
    const is_mgr = roles.includes("SupplyCore Manager") || roles.includes("System Manager");
    const is_exec = roles.includes("SupplyCore Executive") || roles.includes("System Manager");

    // Hiển thị badge stage
    frm.dashboard.set_headline_alert(_stage_badge(stage));

    // Stage Draft / Rejected → button "Gửi duyệt"
    if (["Draft", "Rejected", null, ""].includes(stage)) {
        frm.add_custom_button(__("Gửi duyệt (Manager Review)"), () => {
            frm.call("submit_for_review").then(r => {
                if (r.message) {
                    frappe.show_alert({message: __("Đã chuyển sang Manager Review"), indicator: "blue"});
                    frm.reload_doc();
                }
            });
        }, __("Phê duyệt")).addClass("btn-primary");
    }

    // Stage Manager Review → button "Manager duyệt" + "Từ chối" (chỉ Manager role)
    if (stage === "Manager Review" && is_mgr) {
        frm.add_custom_button(__("Manager duyệt"), () => {
            frappe.prompt({
                fieldname: "comment", fieldtype: "Small Text",
                label: __("Ghi chú (optional)"),
            }, values => {
                frm.call("approve_as_manager", {comment: values.comment || ""}).then(r => {
                    if (r.message) {
                        const next = r.message.stage;
                        const msg = next === "Approved"
                            ? __("FC đã Approved (< {0}đ — không cần Executive)", [r.message.threshold])
                            : __("Chuyển tiếp Executive Review (≥ {0}đ)", [r.message.threshold]);
                        frappe.show_alert({message: msg, indicator: "green"});
                        frm.reload_doc();
                    }
                });
            }, __("Manager duyệt FC"));
        }, __("Phê duyệt")).addClass("btn-primary");
        frm.add_custom_button(__("Từ chối"), () => _show_reject_dialog(frm), __("Phê duyệt"));
    }

    // Stage Executive Review → button "Lãnh đạo duyệt" + "Từ chối" (chỉ Executive role)
    if (stage === "Executive Review" && is_exec) {
        frm.add_custom_button(__("Lãnh đạo duyệt"), () => {
            frappe.prompt({
                fieldname: "comment", fieldtype: "Small Text",
                label: __("Ghi chú (optional)"),
            }, values => {
                frm.call("approve_as_executive", {comment: values.comment || ""}).then(r => {
                    if (r.message) {
                        frappe.show_alert({message: __("FC đã Approved — sẵn sàng Submit"), indicator: "green"});
                        frm.reload_doc();
                    }
                });
            }, __("Lãnh đạo duyệt FC"));
        }, __("Phê duyệt")).addClass("btn-primary");
        frm.add_custom_button(__("Từ chối"), () => _show_reject_dialog(frm), __("Phê duyệt"));
    }

    // Approved → hint user click Submit toolbar button
    if (stage === "Approved") {
        frm.dashboard.set_headline_alert(
            `<div class="indicator green">${__("Đã Approved — click Submit (toolbar) để kích hoạt HĐ")}</div>`);
    }
}

function _stage_badge(stage) {
    const colors = {
        "Draft": "gray", "Manager Review": "blue", "Executive Review": "purple",
        "Approved": "green", "Rejected": "red",
    };
    const color = colors[stage] || "gray";
    return `<div class="indicator ${color}">${__("Stage: {0}", [stage])}</div>`;
}

function _show_reject_dialog(frm) {
    frappe.prompt({
        fieldname: "reason", fieldtype: "Small Text",
        label: __("Lý do từ chối"), reqd: 1,
    }, values => {
        frm.call("reject_approval", {reason: values.reason}).then(r => {
            if (r.message) {
                frappe.show_alert({message: __("Đã reject — gửi lại Kế toán"), indicator: "orange"});
                frm.reload_doc();
            }
        });
    }, __("Từ chối FC"));
}

function _add_action_buttons(frm) {
    if (frm.doc.docstatus !== 1) return;

    // Render progress bar (% used + committed) on dashboard
    _render_progress_bar(frm);

    // Tạo Release Order — chỉ Active/Draft
    if (["Active", "Draft"].includes(frm.doc.status)) {
        frm.add_custom_button(__("Tạo Release Order"), () => {
            frappe.new_doc("Release Order", {framework_contract: frm.doc.name});
        }, __("Tạo"));
    }

    // Recalculate
    frm.add_custom_button(__("Tính lại giá trị"), () => {
        frm.call("recalculate_used_value").then(() => {
            frm.reload_doc();
            frappe.show_alert({message: __("Đã tính lại"), indicator: "green"});
        });
    }, __("Hành động"));

    // UC-04: Gia hạn (chỉ Active hoặc Expired ≤ 90 ngày)
    if (frm.doc.status !== "Terminated") {
        frm.add_custom_button(__("Gia hạn HĐ"), () => _show_renewal_dialog(frm),
            __("Hành động"));
    }

    // UC-04: Thanh lý (chỉ Active/Expired)
    const roles = frappe.user_roles || [];
    const is_mgr = roles.includes("SupplyCore Manager") || roles.includes("System Manager");
    if (frm.doc.status !== "Terminated" && is_mgr) {
        frm.add_custom_button(__("Thanh lý HĐ"), () => _show_terminate_dialog(frm),
            __("Hành động"));
    }

    // UC-04: Approve renewal Pending rows (chỉ Manager/Executive thấy)
    const pending = (frm.doc.renewal_history || []).filter(r => r.approval_status === "Pending");
    if (pending.length && is_mgr) {
        pending.forEach(row => {
            frm.add_custom_button(
                __("Duyệt gia hạn → {0}", [row.new_valid_to]),
                () => _show_approve_renewal_dialog(frm, row.idx, row.new_valid_to),
                __("Phê duyệt gia hạn"),
            );
        });
    }
}

function _render_progress_bar(frm) {
    const total = frm.doc.total_value || 0;
    if (!total) return;
    const used = frm.doc.used_value || 0;
    const committed = frm.doc.committed_value || 0;
    const used_pct = (used / total) * 100;
    const committed_pct = (committed / total) * 100;
    const total_pct = used_pct + committed_pct;
    const color = total_pct >= 80 ? "red" : total_pct >= 60 ? "orange" : "green";
    const html = `
        <div style="margin: 8px 0;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span><b>Mức giải ngân:</b> ${total_pct.toFixed(1)}% (${(100 - total_pct).toFixed(1)}% còn lại)</span>
                <span class="text-muted">${format_currency(used + committed, "VND")} / ${format_currency(total, "VND")}</span>
            </div>
            <div style="background:#f0f0f0;border-radius:4px;height:24px;overflow:hidden;display:flex;">
                <div style="width:${used_pct}%;background:#3498db;color:white;text-align:center;font-size:11px;line-height:24px;" title="PO submitted">
                    ${used_pct > 5 ? `PO ${used_pct.toFixed(1)}%` : ""}
                </div>
                <div style="width:${committed_pct}%;background:#f39c12;color:white;text-align:center;font-size:11px;line-height:24px;" title="RO Approved chưa convert">
                    ${committed_pct > 5 ? `RO ${committed_pct.toFixed(1)}%` : ""}
                </div>
            </div>
        </div>`;
    frm.dashboard.add_section(html, __("Tiến độ thực hiện hợp đồng"));
}

function _show_renewal_dialog(frm) {
    const d = new frappe.ui.Dialog({
        title: __("Gia hạn Hợp đồng khung"),
        fields: [
            {fieldname: "old_valid_to_display", fieldtype: "Date",
             label: __("Hết hạn hiện tại"), default: frm.doc.valid_to, read_only: 1},
            {fieldname: "new_valid_to", fieldtype: "Date",
             label: __("Hết hạn mới"), reqd: 1,
             description: __("Phải sau ngày hết hạn hiện tại")},
            {fieldname: "reason", fieldtype: "Small Text",
             label: __("Lý do gia hạn"), reqd: 1,
             description: __("VD: Thoả thuận tiếp tục cung ứng sang năm 2027")},
        ],
        primary_action_label: __("Gửi yêu cầu gia hạn"),
        primary_action(values) {
            frm.call("request_renewal", {
                new_valid_to: values.new_valid_to, reason: values.reason,
            }).then(r => {
                if (r.message) {
                    frappe.show_alert({
                        message: __("Đã gửi yêu cầu gia hạn — chờ Manager duyệt"),
                        indicator: "blue",
                    });
                    frm.reload_doc();
                    d.hide();
                }
            });
        },
    });
    d.show();
}

function _show_approve_renewal_dialog(frm, row_idx, new_valid_to) {
    frappe.confirm(
        __("Duyệt gia hạn → {0}? FC.valid_to sẽ cập nhật thành ngày này.", [new_valid_to]),
        () => {
            frappe.prompt({
                fieldname: "comment", fieldtype: "Small Text",
                label: __("Ghi chú phê duyệt (optional)"),
            }, values => {
                frm.call("approve_renewal", {row_idx, comment: values.comment || ""}).then(r => {
                    if (r.message) {
                        frappe.show_alert({
                            message: __("Đã duyệt — valid_to: {0}, status: {1}",
                                [r.message.new_valid_to, r.message.fc_status]),
                            indicator: "green",
                        });
                        frm.reload_doc();
                    }
                });
            }, __("Duyệt gia hạn"));
        },
    );
}

function _show_terminate_dialog(frm) {
    const d = new frappe.ui.Dialog({
        title: __("Thanh lý Hợp đồng khung"),
        fields: [
            {fieldname: "warning", fieldtype: "HTML",
             options: `<div class="alert alert-warning">
               ⚠ Hành động này không thể hoàn tác. HĐ sẽ chuyển sang trạng thái 'Terminated'
               và mọi RO draft tham chiếu sẽ bị Cancelled.</div>`},
            {fieldname: "reason", fieldtype: "Small Text",
             label: __("Lý do thanh lý"), reqd: 1,
             description: __("VD: NCC vi phạm điều khoản, kết thúc dự án, ...")},
            {fieldname: "attachment_url", fieldtype: "Attach",
             label: __("Biên bản thanh lý (PDF)"),
             description: __("Optional — upload file biên bản")},
        ],
        primary_action_label: __("Xác nhận thanh lý"),
        primary_action(values) {
            frm.call("terminate_contract", {
                reason: values.reason, attachment_url: values.attachment_url || null,
            }).then(r => {
                if (r.message) {
                    frappe.show_alert({
                        message: __("Đã thanh lý — {0}", [r.message.termination_date]),
                        indicator: "red",
                    });
                    frm.reload_doc();
                    d.hide();
                }
            });
        },
    });
    d.show();
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
