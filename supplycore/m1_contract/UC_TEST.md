# UC Test — M1 — Hợp đồng & Nhà cung cấp

**Source:** Phase 1 / 03_Use-Case-Diagram-and-Descriptions / UseCase_SupplyCore_v2.0.md
**Cập nhật:** 2026-05-08
**Mục đích:** Test scenario từng UC tương ứng với module này — End-user (BS, dược sĩ, SK, kế toán) hoặc QA tester thực hiện thủ công, hệ thống xác nhận đúng.

> Tham khảo: [`docs/UC_COVERAGE.md`](../../docs/UC_COVERAGE.md) cho overview 37 UCs. [`docs/UAT_PROCEDURE.md`](../../docs/UAT_PROCEDURE.md) cho luồng E2E xuyên suốt.

## UC-01 — Tìm kiếm & Đánh giá NCC

**Actor:** Storekeeper / Accountant
**Status:** ✅ OK (enhanced 2026-05-08 — scorecard + script report)
**Pre-condition:** SC Supplier có data + đã seed master.

### Test scenario

1. Mở `/app/sc-supplier` (List view).
2. Lọc theo: `supplier_name` (search bar) / `tax_id` / `supplier_type` / `province` / `default_item_group`.
3. Verify list hiển thị: supplier_code, supplier_name, supplier_type, rating, blacklist_flag, province.
4. Click 1 NCC để mở detail form.
5. Scorecard panel render tự động: rating ★, active contracts, PO 12t, on-time%, QC pass%, AP outstanding, open alerts.
6. Connections panel show: FC, RO, PO, PR, Batch, PI, PE, Recall liên quan.
7. Click button **"Mở báo cáo Supplier Performance"** → navigate Script Report với filter pre-fill `supplier=NCC này`.
8. Trên Script Report: chọn period + click Menu → Export → Excel / PDF.

### Expected result

- Filter trả đúng kết quả theo từng tiêu chí (combine AND).
- Scorecard tính chính xác: on-time = PR.posting_date ≤ PO.schedule_date; QC pass = QI Accepted / total submit.
- Script Report có 14 cột với color-coded rating/on-time/QC.
- Export Excel/PDF tải xuống thành công.

### Checklist Pass/Fail

- [ ] Search filter tổ hợp 4 tiêu chí hoạt động
- [ ] Scorecard load < 2s
- [ ] Script Report export Excel + PDF OK
- [ ] Color coding chính xác (xanh ≥95%, cam 80-95%, đỏ <80%)

---

## UC-02 — Tạo / Cập nhật NCC

**Actor:** Accountant / Manager
**Status:** ✅ OK (enhanced 2026-05-08 — 8-step full flow + bank info + item groups multi + attachments)
**Pre-condition:** Role SupplyCore Manager hoặc Accountant. SC Item Group có sẵn.

### Test scenario (8 bước theo Phase 1)

1. **Mở form NCC**: `/app/sc-supplier/new` (tạo mới) hoặc click 1 NCC từ list để cập nhật.
2. **Required fields:** supplier_name + **tax_id** + **address** + **mobile_no** + **email_id** (`reqd=1`).
3. **Thanh toán:**
   - `payment_terms`: Select `Net 30 / Net 60 / Net 90 / COD / 50/50 / Khác`
   - `credit_limit`: Currency VND
   - `bank_name`, `bank_account_no`, `bank_account_holder` (để trống → auto = supplier_name)
4. **Loại NCC**: Select `Nhà sản xuất / Nhà phân phối / Đại lý / Khác` (`reqd=1`).
5. **Danh mục VT cung ứng** (section collapsible):
   - `default_item_group` (filter nhanh)
   - `supplied_item_groups` (child table) — append nhiều SC Item Group + remarks
6. **Pháp lý** (section collapsible):
   - `gpkd_no` + `gpkd_attachment` (file scan GPKD)
   - `gpp_certificate_no` + `gpp_expiry`
   - `iso_certificate_no` + `iso_attachment`
7. **Save** (Ctrl+S):
   - tax_id unique check → trùng → `SC-E-DUPLICATE-TAX-ID`
   - email regex check → invalid → `SC-E-EMAIL`
   - item_groups dedup → `SC-E-DUPLICATE-ITEM-GROUP`
8. **Auto Supplier Code** format `SC-SUP-#####` (read-only).

### Expected result

- 4 required fields: thiếu → mandatory error đỏ.
- Trùng MST: reject với link tới NCC đã có MST đó.
- Email regex: `^[^\s@]+@[^\s@]+\.[^\s@]+$`.
- Bank account holder default = supplier_name nếu để trống.
- Disabled/Blacklist tick → BLOCK tạo PO (validate ở SC PO).
- Update existing: search → click → edit → save (validation lại).

### Negative tests

- Thiếu address → MandatoryError
- tax_id trùng → SC-E-DUPLICATE-TAX-ID
- Email "abc@" → SC-E-EMAIL
- Item Groups append cùng 1 group 2 lần → SC-E-DUPLICATE-ITEM-GROUP
- blacklist_flag=1 → tạo PO → throw

### Checklist Pass/Fail

- [ ] Tạo NCC mới 8 bước đầy đủ → supplier_code auto-sinh
- [ ] payment_terms select hoạt động (6 options)
- [ ] bank_account_holder default = supplier_name
- [ ] supplied_item_groups child table append/remove được
- [ ] Upload + xem GPKD attachment
- [ ] Update existing NCC: edit + save validation lại
- [ ] Negative tax_id trùng → throw đúng
- [ ] Negative email invalid → throw đúng
- [ ] Negative item_groups trùng → throw đúng
- [ ] Blacklist → cố tạo PO → throw đúng

---

## UC-03 — Tạo & Quản lý Hợp đồng khung (FC)

**Actor:** Accountant (tạo) → Manager (duyệt) → Executive (duyệt nếu ≥ ngưỡng)
**Status:** ✅ OK (enhanced 2026-05-08 — 3-tier workflow + delivery_terms + blacklist override)
**Pre-condition:** SC Supplier active + SC Item. Settings.fc_executive_threshold (default 100tr).

### Test scenario (8 bước theo Phase 1)

1. **Mở form** `/app/framework-contract/new` → Tạo mới (role: Accountant/Manager).
2. **Chọn NCC** từ danh sách (autocomplete). System validate supplier tồn tại + active.
3. **Thông tin HĐ**: contract_number (unique), contract_date (≤ valid_from), valid_from, valid_to (> valid_from).
4. **Danh mục vật tư** (child Items): mỗi row item_code + uom + unit_price + contract_qty (max).
5. **Điều khoản**: payment_terms (Net 30/60/90/COD/...) + **delivery_terms** (mới, vd: "Giao tận kho, lead time 7 ngày").
6. **Gửi phê duyệt** — Workflow Kế toán → Quản lý → Lãnh đạo:
   - Click button **"Gửi duyệt (Manager Review)"** → `submit_for_review()` → stage=Manager Review
   - Manager (role SupplyCore Manager) click **"Manager duyệt"** → prompt comment:
     - Nếu `total_value < fc_executive_threshold` → stage=**Approved** trực tiếp
     - Nếu `total_value ≥ fc_executive_threshold` → stage=**Executive Review**
   - Executive (role SupplyCore Executive) click **"Lãnh đạo duyệt"** → stage=Approved
7. **Submit FC** (toolbar) — chỉ enable khi `approval_stage=Approved` (else throw `SC-E-FC-NOT-APPROVED`):
   - status auto chuyển Active (nếu `today ≤ valid_to`) hoặc Expired
   - Connections panel: 0 RO/PO ban đầu
8. **Cảnh báo hết hạn**: scheduler daily check + M11 Alert `contract_expiring` 30 ngày trước.

### Luồng thay thế

- **6a Reject:** Manager hoặc Executive click button **"Từ chối"** → prompt reason (reqd) → stage=Rejected + ghi `rejection_reason`. Kế toán click "Gửi duyệt" lại → reset Rejected → Manager Review (rejection_reason cleared).
- **4a Item chưa có**: Frappe Link field cho phép `+ Add new` ngay trong form FC để tạo SC Item song song.

### Xử lý ngoại lệ

- **Ngày**: valid_to ≤ valid_from → `SC-E-DATE` "Ngày hết hạn phải sau ngày hiệu lực". contract_date > valid_from → `SC-E-DATE` "Ngày ký không được sau ngày hiệu lực".
- **NCC blacklist**: nếu `supplier.blacklist_flag=1`:
  - Stage Draft: msgprint warning
  - Stage Manager/Executive Review: throw `SC-E-FC-BLACKLIST` trừ khi Lãnh đạo tick **"Executive override blacklist"** (`executive_override_blacklist=1`)
- **Submit chưa Approved**: throw `SC-E-FC-NOT-APPROVED` — phải đi qua workflow trước.

### Hậu điều kiện

- FC trạng thái Active, lưu `manager_approved_by/at`, `executive_approved_by/at` (nếu áp dụng), comments.
- Release Order có thể tham chiếu (link framework_contract).
- M11 Alert `contract_expiring` activated.

### Checklist Pass/Fail

- [ ] FC < 100tr: Manager-only approval (stage = Approved sau Manager duyệt)
- [ ] FC ≥ 100tr: Manager → Executive Review → Executive duyệt → Approved
- [ ] Submit khi chưa Approved → throw SC-E-FC-NOT-APPROVED
- [ ] Reject với reason + Re-submit → stage reset Manager Review, reason cleared
- [ ] Manager-only role: Executive button không hiển thị
- [ ] Executive-only role: Manager button không hiển thị
- [ ] NCC blacklist + chưa override → block ở Manager Review
- [ ] NCC blacklist + executive_override_blacklist=1 → cho qua
- [ ] Validate ngày ký vs hiệu lực (2 case)
- [ ] Validate supplier không tồn tại (BUG-M1-01)
- [ ] delivery_terms field hiển thị + lưu được
- [ ] manager_approved_by/at + executive_approved_by/at ghi nhận đúng user/timestamp

---

## UC-04 — Theo dõi & Gia hạn / Thanh lý HĐ

**Actor:** Accountant / Manager (Executive nếu FC ≥ ngưỡng)
**Status:** ✅ OK (enhanced 2026-05-08 — renewal workflow + terminate + 90d block)
**Pre-condition:** FC đã submit (Active hoặc Expired ≤ 90 ngày).

### Test scenario (8 bước theo Phase 1)

1. **Dashboard FC**: `/app/framework-contract` (filter status, expiring_soon).
2. **Mở chi tiết FC**: hiển thị 3 indicator + **progress bar 2-color**:
   - Blue = % `used_value` (PO submitted)
   - Orange = % `committed_value` (RO Approved chưa convert)
   - Total filling: green <60% / orange 60-80% / red ≥80%
3. **Connections panel**: Release Order + SC PO + PR + PI tham chiếu FC.
4. **Cảnh báo hết hạn**: nếu `expiring_soon=1` (≤30 ngày) → headline alert orange. M11 Alert `contract_expiring` daily quét.
5. **Gia hạn**:
   - Click button **"Gia hạn HĐ"** → dialog: ngày hết hạn mới (reqd) + lý do (reqd)
   - `request_renewal()` validate: new_valid_to > current valid_to + chưa quá 90 ngày
   - Append entry status=Pending vào `renewal_history` child table
6. **Phê duyệt gia hạn** (Manager hoặc Executive nếu ≥ threshold):
   - Trên FC form, button **"Duyệt gia hạn → {date}"** xuất hiện
   - Confirm + prompt comment → `approve_renewal()` set `valid_to = new_valid_to` + status auto Active
   - Hoặc button **"Reject"** → entry status=Rejected
7. **Sau duyệt**: FC.valid_to cập nhật, `expiring_soon` reset, `renewal_history` lưu lịch sử (request_date, old/new valid_to, by/at, status, reason).
8. **Cảnh báo daily**: scheduler `check_contract_expiry` email 30/15/7 ngày + tạo M11 Alert (slice 2: button "Gia hạn" có thể trigger từ alert).

### Luồng thay thế

- **5a Thanh lý**:
  - Click button **"Thanh lý HĐ"** (role Manager) → dialog warning + reason (reqd) + attachment (optional biên bản PDF)
  - `terminate_contract()` set status=Terminated + termination_date + termination_reason + termination_minutes
  - Block tất cả Release Order draft tham chiếu (đã có ở on_cancel — set RO.status=Cancelled)
- **4a Vượt hạn mức**: PO/RO submit > FC.remaining_value → throw `SC-E002 FC_EXCEEDED` (đã có ở SC PO controller)

### Hậu điều kiện

- Trạng thái FC cập nhật chính xác.
- `renewal_history` ghi đầy đủ lịch sử (request_date + old/new valid_to + reason + approver).
- `track_changes` Frappe builtin lưu version history toàn bộ field changes.
- M11 Alert `contract_expiring` reset sau gia hạn nếu valid_to mới ≥ 30 ngày.

### Xử lý ngoại lệ

- **Hết hạn > 90 ngày**: throw `SC-E-FC-EXPIRED-90D` "HĐ đã hết hạn quá X ngày — không thể gia hạn retroactively. Vui lòng tạo FC mới."
- **Gia hạn FC đã Terminated**: throw `SC-E-FC-TERMINATED` "HĐ đã thanh lý — không thể gia hạn"
- **new_valid_to ≤ valid_to**: throw `SC-E-FC-RENEWAL` "Ngày hết hạn mới phải SAU ngày hết hạn hiện tại"
- **Reject role**: chỉ Manager/Executive được reject

### Checklist Pass/Fail

- [ ] Progress bar render đúng tỷ lệ used + committed
- [ ] Dashboard indicators (3 màu) chính xác
- [ ] Gia hạn happy path: request → Manager duyệt → valid_to update
- [ ] Reject renewal: row status=Rejected, valid_to KHÔNG đổi
- [ ] Quá 90 ngày: throw SC-E-FC-EXPIRED-90D
- [ ] new_valid_to ≤ current: throw SC-E-FC-RENEWAL
- [ ] Thanh lý: status=Terminated, termination_date set, RO draft → Cancelled
- [ ] Sau Terminated: gia hạn → block
- [ ] Daily scheduler email 30/15/7 ngày
- [ ] M11 Alert contract_expiring auto-tạo
- [ ] renewal_history table render đầy đủ lịch sử
- [ ] track_changes có audit log toàn bộ field

---


## Tổng kết module m1_contract

**Total UCs:** 4

**Sign-off:**
- [ ] UC-01 Tìm kiếm & Đánh giá NCC — Tester: __________ Date: __________
- [ ] UC-02 Tạo / Cập nhật NCC — Tester: __________ Date: __________
- [ ] UC-03 Tạo & Quản lý Hợp đồng khung (FC) — Tester: __________ Date: __________
- [ ] UC-04 Theo dõi & Gia hạn HĐ — Tester: __________ Date: __________
