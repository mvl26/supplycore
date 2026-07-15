# Design — Slice 3: Recall Email Notify + Mark Contacted UI

**Date:** 2026-05-08
**Status:** Draft (chờ user review)
**Owner:** SupplyCore team
**Slice:** 3 (sau slice 1 procurement chain, slice 2 alert→action)

## Mục tiêu

Khi một lô vật tư y tế bị recall (`SC Recall Notice` submit), hệ thống phải:

1. **3a — Auto-email Khoa & Pharmacy team** danh sách bệnh nhân đã được cấp lô đó, để họ contact follow-up (đổi thuốc, theo dõi tác dụng phụ).
2. **3b — UI để pharmacist/SK đánh dấu BN đã liên hệ** trên Recall form, theo dõi tiến độ outreach.

Áp dụng cho recall severity Class I (Critical) hoặc Class II (High) — Class III (Low) là routine, defer email.

## Bối cảnh

- M10 đã có `populate_affected_items()` quét SLE + PD Item → tạo `SC Recall Affected Item` rows phân loại theo `location_type` (Warehouse/Department/Patient).
- API `get_batch_trace` đã return danh sách `patient_dispensings`.
- Vấn đề: data có nhưng **chưa actionable** — user không biết phải làm gì với danh sách BN, không có notification, không track outreach progress.

## Approach (đã chọn)

**Approach 1: Auto-email on submit, manual resend.**

- `Recall.on_submit` (sau khi block batch + populate affected items) → tự gọi `notify_caregivers()` nếu severity Class I/II.
- Field `email_sent_at` đảm bảo idempotent.
- Button "Gửi lại email" cho phép user trigger lại nếu cần (vd: thay đổi danh sách Khoa, email service down lúc submit).
- Button "Đánh dấu đã liên hệ" cho bulk update status các affected items.

Lý do chọn: Class I+II time-sensitive (BN có thể đang dùng thuốc nguy hiểm) — không nên phụ thuộc user nhớ click button. Manual resend xử lý edge case.

## Data model changes

### 1. `SC Recall Notice` (m10_traceability)

Thêm 2 field vào section "Trạng thái":

| Field | Type | Properties |
|---|---|---|
| `email_sent_at` | Datetime | read_only=1, label="Thời điểm gửi email" |
| `email_recipients` | Small Text | read_only=1, label="Recipients đã gửi" |

### 2. `SC Recall Affected Item` (m10_traceability)

Chỉ chỉnh metadata (không thêm field):

- `voucher_no` → `in_list_view: 1`
- `voucher_date` → `in_list_view: 1`
- `qty_dispensed` → `in_list_view: 1`
- `status` đã có `in_list_view: 1`

Không cần migration phức tạp — `bench migrate` sau JSON edit là đủ.

## Email logic

### Trigger + populate ordering

`Recall.on_submit` hiện chỉ làm: set `batch.blocked=1`, `status="Issued"`. User phải click button "Populate Affected Items" **trước khi submit** để có data. Spec này:

1. Gọi `self.populate_affected_items()` ở đầu `on_submit` nếu `affected_items` rỗng — auto-populate trước khi notify, đảm bảo email luôn có context (kể cả khi user submit thẳng không populate).
2. Sau đó: `batch.blocked=1`, `status="Issued"`, `notify_caregivers()`.

```python
# m10_traceability/doctype/sc_recall_notice/sc_recall_notice.py
def on_submit(self):
    if not self.affected_items:
        self.populate_affected_items()  # auto-populate trước notify
    # ... existing: batch.blocked=1, status="Issued"
    self.notify_caregivers()  # NEW

@frappe.whitelist()
def notify_caregivers(self, force: int = 0):
    # Gating
    if self.severity not in ("Class I (Critical)", "Class II (High)"):
        return {"skipped": True, "reason": "Severity Class III — không gửi email"}
    if self.email_sent_at and not int(force or 0):
        return {"skipped": True, "reason": "Đã gửi", "sent_at": self.email_sent_at}

    recipients = self._collect_recipients()
    if not recipients:
        return {"skipped": True, "reason": "Không có recipient"}

    subject = f"[RECALL {self.severity}] {item_name} batch {self.batch_no}"
    body = self._build_email_body()
    try:
        frappe.sendmail(recipients=list(recipients), subject=subject,
                         message=body, delayed=False)
        self.db_set({
            "email_sent_at": now(),
            "email_recipients": ", ".join(sorted(recipients)),
        })
        return {"sent": True, "recipients_count": len(recipients)}
    except Exception as e:
        frappe.log_error(message=str(e)[:1000], title="M10 notify_caregivers")
        return {"sent": False, "error": str(e)[:200]}
```

### Recipients (3 nguồn, dedup)

```python
def _collect_recipients(self) -> set:
    rec = set()
    # 1. head_user của Khoa có affected_items
    depts = frappe.db.sql_list("""
        SELECT DISTINCT department FROM `tabSC Recall Affected Item`
        WHERE parent = %s AND department IS NOT NULL AND department != ''
    """, self.name)
    for dept in depts:
        head = frappe.db.get_value("SC Department", dept, "head_user")
        if head:
            email = frappe.db.get_value("User", head, "email")
            if email:
                rec.add(email)
    # 2. role Pharmacy Officer
    rec.update(_get_users_by_role("Pharmacy Officer"))
    # 3. role SupplyCore Manager
    rec.update(_get_users_by_role("SupplyCore Manager"))
    return rec


def _get_users_by_role(role: str) -> list:
    return frappe.db.sql_list("""
        SELECT DISTINCT u.email FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role = %s AND u.enabled = 1 AND u.email != ''
    """, role) or []
```

### Email body (HTML, tiếng Việt)

```html
<h2>Thông báo thu hồi vật tư y tế</h2>
<p><b>Mức độ:</b> {{ severity }}</p>
<table>
  <tr><th>Vật tư</th><td>{{ item }} — {{ item_name }}</td></tr>
  <tr><th>Lô bị thu hồi</th><td>{{ batch_no }}</td></tr>
  <tr><th>Hạn dùng</th><td>{{ expiry_date }}</td></tr>
  <tr><th>Lý do thu hồi</th><td>{{ recall_reason }}</td></tr>
  <tr><th>Tham chiếu pháp lý</th><td>{{ regulatory_reference }}</td></tr>
</table>

<h3>Tồn kho cần xử lý ({{ n_warehouse }} dòng)</h3>
<table border="1">
  <tr><th>Kho</th><th>SL</th></tr>
  {% for r in warehouse_rows %}
  <tr><td>{{ r.warehouse }}</td><td>{{ r.qty_dispensed }}</td></tr>
  {% endfor %}
</table>

<h3>Bệnh nhân đã được cấp ({{ n_patient }} BN)</h3>
<table border="1">
  <tr><th>BN</th><th>Khoa</th><th>Ngày cấp</th><th>SL</th></tr>
  {% for r in patient_rows %}
  <tr><td>{{ r.patient }}</td><td>{{ r.department }}</td>
      <td>{{ r.voucher_date }}</td><td>{{ r.qty_dispensed }}</td></tr>
  {% endfor %}
</table>

<p><b>Hành động cần thiết:</b></p>
<ol>
  <li>Liên hệ với từng BN trong danh sách trên để follow-up</li>
  <li>Mở Recall Notice để đánh dấu đã liên hệ:
      <a href="/app/sc-recall-notice/{{ name }}">{{ name }}</a></li>
  <li>Tồn kho ở Khoa: chuyển trả về Kho Cách ly QC</li>
</ol>

<p><i>Email tự động từ SupplyCore.</i></p>
```

## UI buttons

### `sc_recall_notice.js` — 3 button khi `docstatus=1`

```javascript
frappe.ui.form.on("SC Recall Notice", {
    refresh(frm) {
        if (frm.doc.docstatus !== 1) return;

        // Button 1: Resend email (chỉ show nếu severity I/II)
        if (["Class I (Critical)", "Class II (High)"].includes(frm.doc.severity)) {
            frm.add_custom_button(__("Gửi lại email thông báo"), () => {
                frappe.confirm(__("Gửi lại email tới Khoa + Pharmacy + Manager?"), () => {
                    frm.call("notify_caregivers", {force: 1}).then(r => {
                        const m = r.message || {};
                        frappe.show_alert({
                            message: m.sent
                                ? __("Đã gửi tới {0} người", [m.recipients_count])
                                : __("Lỗi: {0}", [m.error || m.reason]),
                            indicator: m.sent ? "green" : "orange",
                        }, 5);
                        frm.reload_doc();
                    });
                });
            }, __("Email"));
        }

        // Button 2: Bulk mark contacted
        frm.add_custom_button(__("Đánh dấu đã liên hệ"), () => {
            const grid = frm.get_field("affected_items").grid;
            const selected = grid.get_selected_children();
            if (!selected.length) {
                frappe.msgprint(__("Vui lòng tick các dòng cần đánh dấu trong bảng Items"));
                return;
            }
            const stamp = `${frappe.session.user_fullname} @ ${frappe.datetime.now_datetime()}`;
            selected.forEach(row => {
                row.status = "In Progress";
                row.remarks = `${row.remarks || ""}\nLiên hệ bởi ${stamp}`.trim();
            });
            frm.refresh_field("affected_items");
            frm.dirty();
            frm.save();
        }, __("Hành động"));

        // Button 3: Open trace
        if (frm.doc.batch_no) {
            frm.add_custom_button(__("Xem trace batch"), () => {
                frappe.set_route("Form", "SC Batch", frm.doc.batch_no);
            }, __("Hành động"));
        }
    },
});
```

## Test strategy

**File mới:** `supplycore/tests/smoke_recall_notify.py`

### Setup chung

- SC Department test có `head_user` (User có email valid)
- SC Patient test
- SC Batch + SE Receipt 100 hộp → Kho Vật tư tiêu hao
- SC Patient Dispensing 5 hộp cho BN, `ward` = test dept
- SC Recall Notice draft với batch + recall_reason
- Gọi `populate_affected_items()` → assert rows có cả Warehouse + Patient location_type

### Test cases

| # | Test | Assertion |
|---|---|---|
| 1 | Submit Recall Class I → notify_caregivers tự chạy | `email_sent_at` ≠ None, `email_recipients` chứa head_user.email + role Pharmacy/MGR users |
| 2 | Email Queue có entry | `frappe.db.exists("Email Queue", {recipients: like %head_email%})` đúng, subject contains batch_no |
| 3 | Idempotent: gọi `notify_caregivers()` lần 2 không force | trả `{"skipped": True, "reason": "Đã gửi"}` |
| 4 | Resend với `force=1` | gửi lại, `email_sent_at` mới hơn |
| 5 | Recall mới severity Class III submit | `email_sent_at` = None, không Email Queue entry |
| 6 | UI mark contacted (mô phỏng): set row.status='In Progress' + save | row reload có status mới + remarks chứa user |
| 7 | Recipients dedup: nếu head_user cũng có role Pharmacy → chỉ 1 email | len(recipients) đúng |

### Cleanup

- Cancel + delete test Recall, PD, SE, Batch, Patient, Department, User
- Xoá Email Queue entries match subject pattern `[RECALL %`

### Regression

- `smoke_m10`, `smoke_integration`, `smoke_alert_action` phải vẫn xanh
- UAT 44 step REST phải vẫn 100%

## Documentation updates

1. **`m10_traceability/README.md`** — thêm section "Recall → Email notify (slice 3)" với:
   - Trigger condition (severity gating)
   - Recipients logic (3 nguồn dedup)
   - Email content sample
   - Resend flow + idempotent guard

2. **`m7_dispensing/README.md`** — Integration section bổ sung outgoing event:
   "PD Item → M10 Recall Affected Item (auto-populate khi recall) + email notify Khoa khi severity Class I/II"

3. **`FLOW.md`** — section "Recall + Trace (M10)":
   - Thêm bước [4] "Recall.on_submit + email Khoa + Pharmacy + Manager nếu Class I/II"
   - Sơ đồ mermaid bổ sung arrow `RCL -.email.-> CARE[Khoa head_user + Pharmacy + Manager]`

## Files changed

| File | Action |
|---|---|
| `m10_traceability/doctype/sc_recall_notice/sc_recall_notice.json` | Add `email_sent_at`, `email_recipients` |
| `m10_traceability/doctype/sc_recall_notice/sc_recall_notice.py` | Add `notify_caregivers()`, `_collect_recipients()`, `_build_email_body()`, hook into `on_submit` |
| `m10_traceability/doctype/sc_recall_notice/sc_recall_notice.js` | Add 3 buttons (Resend, Mark contacted, Trace) |
| `m10_traceability/doctype/sc_recall_affected_item/sc_recall_affected_item.json` | Add `in_list_view` to 3 fields |
| `tests/smoke_recall_notify.py` | New — 7 test cases |
| `m10_traceability/README.md` | New section "Recall → Email notify" |
| `m7_dispensing/README.md` | Update Integration outgoing |
| `FLOW.md` | Update Recall section + mermaid |

## Out of scope (defer)

- 3c PD form post-dispense warning (banner đỏ khi mở PD đã submit) — không actionable, chỉ thông tin
- 3d Báo cáo "Patients exposed" cho audit — có thể tạo bằng Frappe Report Builder UI sau, không cần code
- Per-patient phone call tracking với contact result → nếu cần sau này, mở rộng `SC Recall Affected Item` với `phone_called`, `call_outcome`
- SMS notification (cần gateway integration)
- Auto-create SE Return cho stock ở Khoa (có thể mở rộng từ slice 2 alert action pattern)
- Multi-language email template — chỉ tiếng Việt v1

## Risks / open questions

- **R1: Email volume** — bệnh viện lớn có thể có 100+ Khoa, mỗi recall email tới ~10 người. `frappe.sendmail` queue handle được, nhưng nếu nhiều recall đồng thời cần monitor.
- **R2: head_user.email** chưa được seed bắt buộc. Nếu Khoa thiếu head_user, email skip Khoa đó (vẫn gửi role-based). Cần document trong README.
- **R3: PII trong email** — danh sách BN gửi qua SMTP cần đảm bảo TLS. Default Frappe SMTP setting nên đã enforce.

## Acceptance criteria

- [ ] `email_sent_at` set sau Class I recall submit
- [ ] Email Queue có entry với recipients chính xác (test case #2)
- [ ] Idempotent: 2nd auto-call không gửi (test case #3)
- [ ] Resend force=1 update timestamp (test case #4)
- [ ] Class III recall không gửi (test case #5)
- [ ] UI bulk mark contacted update status + remarks (test case #6)
- [ ] 11 module smoke + integration + alert_action regression vẫn xanh
- [ ] UAT 44/44 PASS
- [ ] FLOW.md + 2 README cập nhật
