// Supplier Performance — Filters
frappe.query_reports["Supplier Performance"] = {
    "filters": [
        {
            fieldname: "supplier",
            label: __("NCC cụ thể"),
            fieldtype: "Link",
            options: "SC Supplier",
        },
        {
            fieldname: "supplier_type",
            label: __("Loại NCC"),
            fieldtype: "Select",
            options: "\nNhà sản xuất\nNhà phân phối\nĐại lý\nKhác",
        },
        {
            fieldname: "province",
            label: __("Tỉnh/Thành phố"),
            fieldtype: "Data",
        },
        {
            fieldname: "default_item_group",
            label: __("Loại vật tư cung ứng"),
            fieldtype: "Link",
            options: "SC Item Group",
        },
        {
            fieldname: "from_date",
            label: __("Từ ngày"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.now_date(), -12),
        },
        {
            fieldname: "to_date",
            label: __("Đến ngày"),
            fieldtype: "Date",
            default: frappe.datetime.now_date(),
        },
    ],
    formatter(value, row, column, data, default_formatter) {
        const v = default_formatter(value, row, column, data);
        if (column.fieldname === "rating" && data && data.rating) {
            const color = data.rating >= 4 ? "green" : data.rating >= 3 ? "orange" : "red";
            return `<span style="color:${color};font-weight:600;">★ ${data.rating.toFixed(2)}</span>`;
        }
        if (column.fieldname === "on_time_pct" && data && data.on_time_pct != null) {
            const color = data.on_time_pct >= 95 ? "green"
                         : data.on_time_pct >= 80 ? "orange" : "red";
            return `<span style="color:${color};">${data.on_time_pct.toFixed(2)}%</span>`;
        }
        if (column.fieldname === "qc_pass_pct" && data && data.qc_pass_pct != null) {
            const color = data.qc_pass_pct >= 95 ? "green"
                         : data.qc_pass_pct >= 80 ? "orange" : "red";
            return `<span style="color:${color};">${data.qc_pass_pct.toFixed(2)}%</span>`;
        }
        if (column.fieldname === "blacklist_flag" && data && data.blacklist_flag) {
            return `<span style="color:red;font-weight:600;">⛔ YES</span>`;
        }
        return v;
    },
};
