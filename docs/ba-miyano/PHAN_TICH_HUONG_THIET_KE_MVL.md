# Phân tích BA SupplyCore MVL v2 → Hướng thiết kế

> Nguồn: bộ BA `SupplyCoreMVL 02072026 v2` (17 tài liệu, 02/07/2026, chủ đầu tư Miyano Việt Nam).
> Đối chiếu với codebase `supplycore` hiện tại (branch `vienyhctbca`), ngày phân tích 03/07/2026.

---

## Tiến độ thực hiện (07/07/2026 — nhánh `feat/mvl-distributor`)

**GĐ1–GĐ4 đã hoàn tất trên nhánh `feat/mvl-distributor`.** Quyết định kiến trúc #1
(mục 2) đã thực thi: MVL **thay thế in-place** bản bệnh viện, không còn
deployment_profile/fork.

- **GĐ1 — Gỡ bệnh viện + M7 Bán hàng + M12 Portal (nền tảng):** gỡ M7
  Dispensing/BHYT/Patient/HIS map; thêm M7 Sales (SC Customer, SC Sales
  Framework Contract, SC Sales Order, SC Delivery Note, SC Acceptance Record,
  SC Sales Invoice, SC Sales Receipt) + BRU-AR-001 (credit_limit) + O2C đầy đủ
  (đặt hàng → duyệt → giao → nghiệm thu → hoá đơn → thu tiền, hạch toán AR/GL);
  thêm khung M12 Customer Portal (provisioning + cô lập dữ liệu RSK-01).
- **GĐ2 — Sales suites + regression nền:** bộ test GĐ2 đầy đủ cho 7 doctype
  M7 Sales + API bán hàng + kịch bản O2C end-to-end.
- **GĐ3 — Portal khách hàng + cô lập RSK-01:** `api/portal.py` (7 API tự lọc
  theo khách hàng đăng nhập: `portal_me/contracts/catalog/order_place/
  order_track/order_history/document_download`), permission_query_conditions +
  has_permission trên 5 doctype bán + 4 child doctype, chặn residual REST
  `/api/resource|/api/v1/resource|/api/v2/document` cho child doctype bán hàng.
- **GĐ4 — Rebrand Miyano + UI Portal + Sales SPA + hardening cuối:**
  - Task 1: rebrand toàn bộ nhận diện/seed sang Công ty Miyano Việt Nam (MVL),
    kho/phòng phân phối thay khoa/phòng bệnh viện.
  - Task 2: đóng residual hardening `/api/resource` child cho portal.
  - Task 3: trang Portal khách `www/portal` (catalog, đặt hàng, theo dõi đơn
    với tracker 4 cột mốc, tải chứng từ) — mobile-first, tách khỏi SPA nội bộ.
  - Task 4: M7 Sales vào SPA nội bộ (DocView generic) + dashboard công nợ phải
    thu (`ar_aging_by_customer`, cảnh báo vượt credit_limit).
  - Task 5 (hoàn tất thành phẩm): security sweep toàn bộ `@frappe.whitelist()`
    API nội bộ (`api/*.py`, `m*/api/*.py`) — vá lỗ hổng phát hiện
    (`ap_aging_report` không role-gate, hàng chục hàm KPI/tồn kho/FEFO/audit/
    truy xuất/WMS thiếu permission check hoàn toàn) bằng `block_portal()`
    (block-list role Portal) hoặc allow-list vai trò tài chính; test portal-
    reachability (`portal_internal_api_denied_test`); regression toàn bộ
    (GĐ2+GĐ3/4+smoke+UC-26) xanh; grep thuật ngữ bệnh viện → 0; docs cập nhật.

Sản phẩm MVL (procure → nhận hàng/QC → nhập kho → bán → giao hàng → xuất hoá
đơn → thu tiền + Portal khách) sẵn sàng bàn giao trên nhánh
`feat/mvl-distributor`.

---

## 0. TL;DR

- **BA v2 KHÔNG phải bản nâng cấp app hiện tại.** Nó là **biến thể MVL cho doanh nghiệp phân phối**, dẫn xuất từ "bản bệnh viện" — mà **bản bệnh viện chính là codebase `supplycore` đang chạy**.
- Khác biệt cốt lõi chỉ nằm ở **2 phân hệ**: bỏ **M7 Cấp phát + BHYT + Bệnh nhân**, thay bằng **M7 Bán hàng** và thêm mới **M12 Portal khách hàng**. ~80% còn lại (M1–M6, M8–M11) dùng chung.
- **Quyết định phải chốt trước mọi thứ khác: chiến lược cùng tồn tại** giữa bản bệnh viện (đang chạy) và bản MVL. Đề xuất: **shared-core + biến thể theo cấu hình**, KHÔNG sửa tại chỗ (in-place) làm hỏng bản bệnh viện.
- BA có nhiều dấu hiệu **sinh tự động** (US điền placeholder `m1/m2`, prototype lặp 5 template). **Tin danh mục cấu trúc** (DocType/module/role/workflow/screen + delta), **giảm trọng số phần narrative**. Khi mâu thuẫn, **code sống là chuẩn**, không phải BA.

---

## 1. Hai sản phẩm, một dòng máu

| | Bản bệnh viện (codebase hiện tại) | Bản MVL (BA v2) |
|---|---|---|
| Chủ thể | Bệnh viện dùng nội bộ | Công ty phân phối (bán ra ngoài) |
| Đầu ra M7 | **Cấp phát** cho khoa/bệnh nhân + **BHYT** | **Bán hàng** + Bàn giao + Nghiệm thu |
| Khách hàng | Bệnh nhân (SC Patient) | Doanh nghiệp (SC Customer) + **Portal** |
| Tích hợp | HIS/EMR, Cổng BHYT | **Bỏ hết** HIS/BHYT; thêm Portal + máy in nhãn |
| Kế toán | Phải trả (mua) | Phải trả **+ phải thu** (bán, công nợ khách) |
| Số phân hệ | 11 (M1–M11) | **12** (thêm M12 Portal) |

Delta Bộ Số Chuẩn (BV → MVL): UC 37→**43**, FR 42→**52**, DocType 38→**40**, Workflow 12→**14**, Role 13→**10**, Màn hình 37→**43**.

---

## 2. ★ Quyết định kiến trúc #1 — Chiến lược cùng tồn tại → ĐÃ CHỐT: THAY THẾ IN-PLACE

**Quyết định (03/07/2026): MVL thay thế hoàn toàn bản bệnh viện.** Miyano không còn dùng bản BV → **biến đổi codebase `supplycore` tại chỗ**, KHÔNG cần cơ chế `deployment_profile`/fork.

Hệ quả:
- **Gỡ hẳn** M7 Dispensing + BHYT + Patient + HIS map khỏi code (không chỉ ẩn) — xem mục 3b.
- **Thêm thẳng** M7 Sales + M12 Portal vào app hiện tại — xem mục 3a.
- **Không** phát sinh cờ profile, không nhánh điều kiện Hospital/Distributor → code gọn hơn, không nợ kỹ thuật biến thể.
- ⚠️ Vẫn nên làm trên **nhánh Git riêng** và **backup DB** trước khi gỡ (dữ liệu bệnh nhân/cấp phát/BHYT sẽ mất khi drop DocType). Xác nhận không cần migrate dữ liệu BV sang MVL.
- Đổi `app_description` từ *"Hospital medical supply chain"* → mô tả phân phối; rà `README.md`, `FLOW.md` cho khớp mô hình bán hàng.

---

## 3. Gap DocType (đối chiếu 40 BA ↔ 60 hiện có)

### 3a. THÊM MỚI cho MVL (chưa có trong code) — chiều bán
- `SC Customer` (+ ràng buộc 1-1 với User Portal, BRU-CUS-001/002)
- `SC Sales Framework Contract` (+ child SFC Item) — HĐ khung bán, giá cố định
- `SC Sales Order` (+ SO Item) — đơn khách, ràng giá & hạn mức HĐ khung
- `SC Delivery Note` (+ DN Item) — phiếu bàn giao
- `SC Acceptance Record` — biên bản nghiệm thu (điều kiện xuất hóa đơn, BRU-DEL-001)
- `SC Sales Invoice` (+ SI Item) — hóa đơn bán
- `SC Sales Receipt` — thu tiền khách (công nợ phải thu)

### 3b. BỎ / TẮT cho MVL (có trong code, không có trong BA MVL)
- `SC Patient`, `SC Dispensing Request`, `SC Patient Dispensing` (+ child) — cả module M7 Dispensing
- `SC BHYT Code Config`
- `SC HIS Warehouse Map` (M6 — map kho HIS)
- Field `his_code` trên SC Item (giữ nullable, không hiển thị ở profile Distributor)

### 3c. GIỮ NGUYÊN (lõi dùng chung — ~80%)
M1 Contract, M2 Planning, M3 Receiving+QC, M4 WMS/PDA/Barcode, M5 FEFO, M6 Transfer (bỏ HIS map), M8 Accounting (mở rộng sang phải thu), M9 Stocktake, M10 Traceability, M11 Dashboard, cùng SC Stock Ledger Entry / SC GL Entry / SC Batch / SC Supplier / SC Item.

> ⚠️ Codebase có **11 folder legacy rỗng** (không JSON) và một số DocType đã bị thay bằng biến thể `SC *`. Khi làm cần dọn để tránh nhầm.

---

## 4. Điểm mâu thuẫn BA ↔ code (phải reconcile, đừng bê nguyên BA)

1. **"Mở rộng ERPNext v15"** (Architecture doc) — **SAI**. Code là *"Frappe-only, no ERPNext dependency"* từ v0.2 (`required_apps = ["frappe/frappe"]`). → Giữ thuần Frappe.
2. **"Chưa dùng Frappe Workflow engine"** bị mapper gọi là "gap lớn nhất" — thực ra **không phải mandate của BA**. Code đã hiện thực state machine bằng `status` + `approval_stage` (Select) + controller (SC PO đã đúng các state trong WSS). Áp dụng Workflow engine là **lựa chọn**, không bắt buộc. Đề xuất: giữ pattern hiện tại trừ khi cần audit/UI workflow chuẩn của Frappe.
3. **QC Checklist Template** — BA vẫn spec, nhưng commit gần đây (`faca8b0`) đã bỏ và hiện sẵn 5 tiêu chí QC mẫu. → Code đi trước BA; theo code.
4. **Vai trò 13→10**: BA gộp/bỏ role cấp phát (Pharmacy Officer, BHYT Officer, Ward Staff/Department Requester). Ở profile Distributor thêm **`SC Customer Portal`**.
5. **BA sinh tự động**: US điền placeholder `m1/m2`; prototype 43 màn chỉ tô lại **5 archetype** (List/Form/Master/Dashboard/PDA), nội dung nghiệp vụ thật chỉ ở UC-01, UC-02, UC-17 (PDA), UC-42/43 (Portal). → Thiết kế UI thật phải tự làm, không dựa prototype.

---

## 5. Hai khối việc net-new (rủi ro & giá trị cao nhất)

### M7 — Bán hàng & Bàn giao (chuỗi Order-to-Cash)
Luồng: Portal đặt → Thương mại duyệt (kiểm hạn mức tín dụng + tồn) → Kho xuất **ép FEFO** → bàn giao → **nghiệm thu bắt buộc (biên bản)** → Kế toán xuất hóa đơn + ghi sổ phải thu → thu tiền → đóng đơn.
Ràng buộc lõi: giá **cố định theo HĐ khung, không sửa tại đơn** (BRU-SFC-002); SL ≤ hạn mức HĐ khung (BRU-SO-001); chỉ xuất hóa đơn sau nghiệm thu (BRU-DEL-001); cảnh báo công nợ vượt hạn mức tín dụng (BRU-AR-001).
Workflow mới: WF-09 (SO), WF-10 (Delivery Note), WF-11 (Sales Invoice).

### M12 — Portal khách hàng (rủi ro bảo mật CAO NHẤT — RSK-01)
- 7 endpoint cô lập (`portal.login/contracts/catalog/order.place/order.track/order.history/document.download`).
- **Cô lập dữ liệu tuyệt đối**: role `SC Customer Portal` chỉ thấy bản ghi của chính khách (permission query gắn `portal_user ↔ SC Customer`); mọi route/API nội bộ (NCC, kho, giá mua) → **403** (BRU-SEC-001).
- Theo dõi đơn **4 cột mốc**: Đã đặt → Đã bàn giao/nghiệm thu → Đã cấp hóa đơn → Đã thu tiền.
- Kiểm thử cô lập là **UAT bắt buộc** (TC-40..43); tuân thủ NĐ 13/2023/NĐ-CP.
- Hạ tầng: `www/portal` (Frappe website + guest→customer session). App hiện đã có SPA Vue + PWA — cần quyết định Portal dùng chung SPA (route + guard) hay tách trang web riêng.

---

## 6. Lộ trình đề xuất (in-place, đã bỏ khâu profile)

0. **GĐ0 — Chuẩn bị an toàn**: nhánh Git riêng + backup DB. Xác nhận không migrate dữ liệu bệnh nhân/cấp phát sang MVL.
1. **GĐ1 — Gỡ nghiệp vụ bệnh viện**: drop M7 Dispensing (SC Dispensing Request, SC Patient Dispensing + child), SC Patient, SC BHYT Code Config, SC HIS Warehouse Map; dọn 11 folder legacy rỗng; gỡ role cấp phát/BHYT; cập nhật hooks/scheduler/permission bỏ tham chiếu Patient Dispensing.
2. **GĐ2 — Nền M7 Sales (nội bộ)**: SC Customer, Sales Framework Contract, Sales Order, Delivery Note, Acceptance Record, Sales Invoice, Sales Receipt + ghi SC GL Entry phải thu. Tận dụng lại pattern PO/PR/PI/approval_stage đã có.
3. **GĐ3 — M12 Portal + cô lập dữ liệu**: permission query, role SC Customer Portal, 7 API, theo dõi 4 cột mốc. Viết test cô lập TRƯỚC (TDD — rủi ro cao nhất RSK-01).
4. **GĐ4 — Hoàn thiện**: dashboard/cảnh báo cho công nợ phải thu, cập nhật app_description/README/FLOW, UAT (86 test case, đặc biệt TC-40..43 cô lập Portal).

---

## 7. Rủi ro cần theo dõi
- **RSK-01 rò rỉ dữ liệu chéo Portal (Cao)** → permission query + test cô lập bắt buộc, không bao giờ tin client filter.
- **RSK-04 xuất nhầm lô hết hạn (Cao)** → ép FEFO + chặn lô hết hạn (đã có nền M5 trong code).
- Bảo trì đôi nếu chọn Fork (Phương án A).
- BA lệch code ở nhiều điểm nhỏ (mục 4) → luôn verify BA với code sống.

---

## 8. Điểm mạnh sẵn có để tận dụng
- Codebase đã materialize **60 DocType**, prefix `SC ` nhất quán, controller tách theo module → nền vững cho shared-core.
- Đã có **SC Stock Ledger / SC GL Entry** (sổ kho + sổ cái tự quản) — đúng kiến trúc BA yêu cầu.
- Đã có FEFO, batch, bin, putaway, barcode, PDA, scheduler cảnh báo — M4/M5 gần như tái dùng nguyên.
- Đã có 2 cấp duyệt (`approval_stage`) và framework contract remaining_value — tái dùng cho chiều bán.

---

## 9. Câu hỏi cần chốt với chủ đầu tư / PO
1. ~~Cùng tồn tại~~ → **ĐÃ CHỐT: thay thế in-place** (mục 2).
2. **Không migrate dữ liệu** bệnh nhân/cấp phát/BHYT sang MVL — xác nhận drop được an toàn?
3. Portal: dùng lại **SPA Vue hiện tại** (thêm route + guard) hay dựng **trang web Frappe riêng** `www/portal`?
4. Có áp dụng **Frappe Workflow engine** thật (WSS 14 workflow) hay giữ Select + controller như hiện tại?
5. Máy in nhãn Zebra (ZPL/TCP 9100) — có sẵn phần cứng để tích hợp/kiểm thử không?
