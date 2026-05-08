// SC Supplier — render Scorecard panel + button "Báo cáo đánh giá NCC"
frappe.ui.form.on("SC Supplier", {
    refresh(frm) {
        if (frm.is_new()) return;

        // Render scorecard ngay khi load form
        frm.call("get_scorecard").then(r => {
            if (!r.message) return;
            _render_scorecard(frm, r.message);
        });

        // Button: chuyển sang Supplier Performance Report (chỉ NCC này)
        frm.add_custom_button(__("Mở báo cáo Supplier Performance"), () => {
            frappe.set_route("query-report", "Supplier Performance",
                              {supplier: frm.doc.name});
        }, __("Báo cáo"));

        // Button: Refresh scorecard (sau khi user thay đổi gì đó)
        frm.add_custom_button(__("Làm mới Scorecard"), () => {
            frm.call("get_scorecard").then(r => {
                if (r.message) _render_scorecard(frm, r.message);
            });
        }, __("Báo cáo"));
    },
});

function _render_scorecard(frm, sc) {
    const fmt_curr = v => v == null ? "—" : format_currency(v, "VND");
    const fmt_pct = v => v == null ? "<span class='text-muted'>chưa đủ data</span>"
                                   : `<b class="${v >= 95 ? 'text-success' : v >= 80 ? 'text-warning' : 'text-danger'}">${v}%</b>`;
    const fmt_rating = v => v ? `★ ${v.toFixed(2)}/5` : "—";

    const html = `
    <div class="supplier-scorecard" style="padding:8px 0;">
      <h5 style="margin-top:0;">📊 Scorecard NCC <small class="text-muted">(12 tháng gần nhất)</small></h5>
      <div class="row">
        <div class="col-md-3">
          <div class="text-muted">Rating</div>
          <h4 style="margin:0;">${fmt_rating(sc.rating)}</h4>
        </div>
        <div class="col-md-3">
          <div class="text-muted">Hợp đồng Active</div>
          <h4 style="margin:0;">${sc.active_contracts}</h4>
          <small class="text-muted">${fmt_curr(sc.active_contracts_remaining_value)} còn lại</small>
        </div>
        <div class="col-md-3">
          <div class="text-muted">PO 12 tháng</div>
          <h4 style="margin:0;">${sc.total_pos_12m}</h4>
          <small class="text-muted">${fmt_curr(sc.total_value_12m)}</small>
        </div>
        <div class="col-md-3">
          <div class="text-muted">Công nợ NCC</div>
          <h4 style="margin:0;${sc.ap_outstanding > 0 ? 'color:#c00;' : ''}">${fmt_curr(sc.ap_outstanding)}</h4>
          ${sc.open_alerts > 0 ? `<small style="color:#c00;">⚠ ${sc.open_alerts} alert open</small>` : ""}
        </div>
      </div>
      <hr style="margin:12px 0;"/>
      <div class="row">
        <div class="col-md-6">
          <div class="text-muted">Tỷ lệ giao hàng đúng hạn</div>
          <h3 style="margin:0;">${fmt_pct(sc.on_time_delivery_pct)}</h3>
          <small class="text-muted">PR.posting_date ≤ PO.schedule_date</small>
        </div>
        <div class="col-md-6">
          <div class="text-muted">Tỷ lệ hàng đạt QC</div>
          <h3 style="margin:0;">${fmt_pct(sc.qc_pass_pct)}</h3>
          <small class="text-muted">QI Accepted / total QI</small>
        </div>
      </div>
      ${sc.blacklist_flag ? '<div class="alert alert-danger" style="margin-top:12px;">⛔ NCC trong BLACKLIST — không được tạo PO mới</div>' : ""}
    </div>
    `;

    // Render vào dashboard area của form (Frappe v15)
    if (!frm.dashboard) return;
    const $wrap = frm.dashboard.add_section(html, __("Đánh giá NCC"));
}
