__SUPPLYCORE__

__Hệ Thống Quản Lý Chuỗi Cung Ứng Vật Tư Tiêu Hao Bệnh Viện__

Frappe Framework v15 \+ ERPNext v15

__WORK BREAKDOWN STRUCTURE \(WBS\)__

__Kế Hoạch Triển Khai Chi Tiết Theo Ngày__

__Phiên bản__

v1\.0 — 05/05/2026

__Phạm vi__

01/05/2026 – 31/05/2026 \(31 ngày\)

__Team__

2 người: Dev Lead \(P1\) \+ Dev/QA \(P2\)

__Nền tảng__

Frappe v15, ERPNext v15, MariaDB, Python 3\.11\+, Vue 3

__Mục tiêu__

11 Modules hoàn chỉnh, UAT sign\-off, Go\-Live 31/05/2026

# 1\. TỔNG QUAN DỰ ÁN & CẤU TRÚC WBS

SupplyCore được triển khai trong một lịch biểu cấp tốc 31 ngày \(tháng 5/2026\) với đội ngũ 2 người, bao gồm toàn bộ chu trình từ thiết kế → phát triển → kiểm thử → go\-live\. WBS này phân rã mọi deliverable đến mức task hàng ngày\.

__Phase__

__Thời gian__

__Tên giai đoạn__

__Nội dung chính__

__Deliverables__

__Trạng thái__

__P1__

01–07/05/2026 \(Tuần 1\)

__Thiết kế & Tài liệu__

BRD, URS, Use Case, As\-Is/To\-Be, System Architecture, DB Design, Tech Spec, API Docs, UI/UX Mockups, Security, Integration Design

20 tài liệu thiết kế đầy đủ

__✅ HOÀN THÀNH__

__P2__

08–14/05/2026 \(Tuần 2\)

__Dev Sprint 1 Core Modules__

Setup Frappe app, M1 Hợp đồng NCC, M2 Kế hoạch tồn kho, M3 Tiếp nhận QC, M8 Kế toán & Thanh toán

4 modules hoàn chỉnh, unit test pass

__🔄 ĐANG TIẾN HÀNH__

__P3__

15–21/05/2026 \(Tuần 3\)

__Dev Sprint 2 Operations__

M4 WMS/PDA, M5 Lô/FEFO, M6 Luân chuyển nội bộ, M7 Cấp phát BHYT, M9 Kiểm kê, M10 Truy xuất, M11 Dashboard

7 modules hoàn chỉnh, integration test pass

⏳ CHƯA BẮT ĐẦU

__P4__

22–31/05/2026 \(Tuần 4\)

__UAT, Training & Go\-Live__

Deploy staging, UAT với người dùng thực, bug fix, đào tạo, data migration, go\-live production

UAT sign\-off, Go\-Live 31/05

⏳ CHƯA BẮT ĐẦU

## 1\.1 Phân Công Nhân Sự

__Ký hiệu__

__Vai trò__

__Kỹ năng chính__

__Trách nhiệm trong dự án__

__Thời gian cam kết__

__P1__

__Dev Lead \(Backend\)__

Python, Frappe Framework, ERPNext, MariaDB, REST API

Architecture, custom Doctypes, server\-side logic, hooks, business rules, BHYT engine, integration, deployment

100% \- Full time \(08:00–22:00\)

__P2__

__Dev / QA \(Frontend\)__

Vue 3, Frappe UI, JavaScript, Test automation, UI/UX implementation

Frontend forms, custom list views, client scripts, QA testing, test cases, UAT support, training materials, user manual

100% \- Full time \(08:00–22:00\)

# 2\. PHASE 1 — THIẾT KẾ & TÀI LIỆU \(01–07/05/2026\)

Giai đoạn này đã hoàn thành\. Toàn bộ 20 tài liệu thiết kế đã được tạo và lưu trong thư mục SupplyCore\. Bảng dưới ghi lại WBS thực tế đã thực hiện để phục vụ audit trail\.

__📋 PHASE 1: THIẾT KẾ & TÀI LIỆU — TUẦN 1 \(01/05 – 07/05/2026\) — ✅ HOÀN THÀNH__

__STT__

__Ngày__

__Thứ__

__Người 1 \(Dev Lead / Backend\)__

__Người 2 \(Dev / QA / Frontend\)__

__Deliverable__

__Trạng thái__

1\.1\.1

__01/05 \(Thứ 6\)__

T6

Khởi động dự án: setup workspace, cấu trúc thư mục, tạo BRD v1\.0 \(Executive Summary, Stakeholders, Scope, Business Requirements M1\-M3\)

Tạo URS v1\.0: phân tích user stories cho 11 modules, acceptance criteria, priority matrix

*BRD v1\.0, URS v1\.0*

✅

1\.1\.2

__02/05 \(Thứ 7\)__

T7

Tạo Use Case Diagram v1\.0: 11 actor roles, 45\+ use cases, relationship diagram\. Use Case v2\.0: mô tả chi tiết từng use case

Tạo As\-Is Process Flow: vẽ quy trình hiện tại 6 workflow \(đặt hàng, nhập kho, cấp phát, kiểm kê, thanh toán, recall\)

*Use Case v1\+v2, As\-Is Flow*

✅

1\.1\.3

__03/05 \(CN\)__

CN

Tạo To\-Be Process Flow: thiết kế 6 quy trình mới với SupplyCore, so sánh As\-Is vs To\-Be, KPI cải thiện

Tạo System Architecture Diagram: kiến trúc tổng thể Frappe/ERPNext, layer diagram, deployment view

*To\-Be Flow, System Arch*

✅

1\.1\.4

__04/05 \(CN\)__

CN

Tạo Database Design: schema 35\+ tables, ER diagram, data dictionary cho toàn bộ custom Doctypes

Tạo Technical Specification: Doctype list đầy đủ, Python class design, hooks architecture, permissions matrix

*DB Design, Tech Spec*

✅

1\.1\.5

__05/05 \(Thứ 3\)__

T3

Tạo API Documentation: 45\+ endpoints REST, request/response format, authentication, rate limiting, error codes

Tạo UI/UX Mockups v1\.0: wireframes tất cả screens chính, navigation flow, mobile responsive layouts

*API Docs, UI/UX Mockups*

✅

1\.1\.6

__06/05 \(Thứ 4\)__

T4

Tạo Integration Design: HIS/EMR webhook design, BHXH data format, ERP integration patterns, message queue

Tạo Security & Compliance: RBAC matrix, 2FA spec, audit log design, Nghị định 13/2023 compliance checklist

*Integration Design, Security*

✅

1\.1\.7

__07/05 \(Thứ 5\)__

T5

Tạo FRS, Non\-Functional Req, Tech Stack, Deployment Architecture, Testing Strategy\. Review toàn bộ Phase 1 docs

Tạo Design System, User Journey Map, Wireframes chi tiết\. Tổng hợp Glossary, Risk Register, Project Charter

*20 tài liệu Phase 1\-6 HOÀN CHỈNH*

✅

# 3\. PHASE 2 — DEV SPRINT 1: CORE MODULES \(08–14/05/2026\)

__Modules triển khai: __M1 \(Hợp đồng & NCC\) | M2 \(Kế hoạch tồn kho & Gọi hàng\) | M3 \(Tiếp nhận & QC\) | M8 \(Kế toán & Thanh toán\)  — __Nền tảng: ERPNext standard \+ Custom Frappe app__

__⚙️ PHASE 2: DEV SPRINT 1 — CORE MODULES — TUẦN 2 \(08/05 – 14/05/2026\)__

__STT__

__Ngày__

__Thứ__

__Người 1 \(Dev Lead / Backend\)__

__Người 2 \(Dev / QA / Frontend\)__

__Deliverable__

__Trạng thái__

2\.1\.1

__08/05 \(Thứ 6\)__

T6

\[SETUP\] Tạo Frappe custom app 'supplycore': bench new\-app, cấu trúc thư mục, hooks\.py skeleton, fixtures, CI/CD pipeline\. Setup ERPNext v15 với company profile bệnh viện

\[SETUP\] Setup môi trường dev P2: clone repo, cài dependencies, cấu hình VS Code extensions \(Frappe snippets, Python, Vue 3\)\. Setup test database với sample data

*Dev environment ready App scaffold CI pipeline*

🔄

2\.1\.2

__09/05 \(Thứ 7\)__

T7

\[M1\] Custom fields cho Supplier Doctype: thêm fields đặc thù y tế \(Mã NCC bệnh viện, loại NCC, giấy phép kinh doanh, chứng chỉ ISO\)\. Server script: validation NCC

\[M1\] Form view customization cho Supplier: layout 3 columns, conditional fields, child table 'Danh mục vật tư NCC'\. List view với filters chuyên biệt

*M1: Supplier form enhanced*

2\.1\.3

__10/05 \(CN\)__

CN

\[M1\] Tạo custom Doctype 'Framework Contract' \(Hợp đồng Khung\): fields đầy đủ, child table Items, workflow 3\-state \(Draft→Approved→Closed\)\. Auto\-alert 30/15/7 ngày trước hết hạn

\[M1\] Frontend: Framework Contract form UI, contract timeline view, pricing table\. Notification template cho alert hợp đồng hết hạn

*M1: Framework Contract Doctype \+ Workflow COMPLETE*

2\.1\.4

__11/05 \(Thứ 2\)__

T2

\[M2\] Config Reorder Point per Item per Warehouse: custom fields Min/Max/ROP\. Scheduled job: daily check tồn kho vs ROP, auto\-create Purchase Request\. Release Order Doctype từ Framework Contract

\[M2\] Frontend: Reorder config dashboard, tồn kho alert panel, Release Order form với auto\-populate từ contract\. Purchase Request list với priority flags

*M2: Reorder automation Release Order Purchase Request*

2\.1\.5

__12/05 \(Thứ 3\)__

T3

\[M3\] Extend Purchase Receipt với QC checklist: mandatory fields \(số lô, hạn dùng, số lượng thực tế, quy cách\)\. Partial receipt logic: auto backorder cho số lượng thiếu\. Reject workflow \+ NCC notification

\[M3\] QC Inspection form: scan barcode → tự điền item info, QC result \(Pass/Fail/Conditional\), photo upload cho defective items\. Rejection notice template

*M3: QC module Partial receipt Reject workflow*

2\.1\.6

__13/05 \(Thứ 4\)__

T4

\[M8\] 3\-way matching engine: so sánh PO\-Receipt\-Invoice \(qty, price, total\)\. GL Entry hooks: tự động hạch toán nhập kho, xuất kho, trả hàng theo chuẩn kế toán VN\. Credit limit check

\[M8\] Payment UI: invoice reconciliation dashboard, 3\-way match status indicator, payment approval workflow\. Aged payables report\. Công nợ NCC overview

*M8: 3\-way matching GL auto\-entries Payment workflow*

2\.1\.7

__14/05 \(Thứ 5\)__

T5

Integration M1→M2→M3→M8: test full flow từ Framework Contract → Release Order → Purchase Receipt \(với QC\) → Invoice → Payment\. Fix integration bugs\. Code review P2's work

Unit test toàn bộ M1\-M8: viết pytest cho server\-side logic, Frappe test runner\. QA test cases cho 4 modules, regression checklist\. Bug report \+ priority

*Sprint 1 DONE 4 modules pass tests Test report*

# 4\. PHASE 3 — DEV SPRINT 2: OPERATIONS & ANALYTICS \(15–21/05/2026\)

__Modules triển khai: __M4 \(WMS/PDA\) | M5 \(Lô/FEFO\) | M6 \(Luân chuyển\) | M7 \(Cấp phát BHYT\) | M9 \(Kiểm kê\) | M10 \(Truy xuất\) | M11 \(Dashboard\) — __⚠️ Sprint quan trọng nhất: BHYT engine \+ FEFO algorithm__

__🏗️ PHASE 3: DEV SPRINT 2 — OPERATIONS & ANALYTICS — TUẦN 3 \(15/05 – 21/05/2026\)__

__STT__

__Ngày__

__Thứ__

__Người 1 \(Dev Lead / Backend\)__

__Người 2 \(Dev / QA / Frontend\)__

__Deliverable__

__Trạng thái__

3\.1\.1

__15/05 \(Thứ 6\)__

T6

\[M4\] Warehouse hierarchy 3 tầng: Kho tổng → Kho con → Kho khoa phòng\. Bin/Rack location Doctype\. Barcode generation cho item \+ bin\. PDA interface REST API endpoints

\[M4\] Barcode scanner integration \(JS\): scan\-to\-receive, scan\-to\-issue flows\. Mobile\-optimized PDA web interface\. Bin location UI map\. QR code print template

*M4: WMS 3\-tier Barcode/PDA Bin locations*

3\.1\.2

__16/05 \(Thứ 7\)__

T7

\[M5\] Batch/Lot tracking: extend ERPNext Batch Doctype thêm fields y tế \(số lô NCC, ngày sản xuất, hạn dùng, nhiệt độ bảo quản\)\. FEFO algorithm: tự động sắp xếp lô theo expiry date khi xuất kho\. Lock expired batches

\[M5\] Expiry dashboard: traffic light \(đỏ/vàng/xanh\) cho 90/60/30 ngày\. Batch detail view với movement history\. Recall workflow UI: trace batch → find all locations \+ patients

*M5: FEFO algorithm Expiry alerts Batch tracking*

3\.1\.3

__17/05 \(CN\)__

CN

\[M6\] Internal transfer workflow: Stock Entry \(Material Transfer\) giữa 3 tầng kho\. Approval workflow theo cấp kho\. Auto\-update bin quantities\. Transfer scheduling

\[M6\] Transfer request form: khoa phòng tự tạo yêu cầu chuyển kho, approval dashboard cho thủ kho\. Transfer status tracking\. Email/notification cho người phê duyệt

*M6: Internal transfer Approval workflow Complete*

3\.1\.4

__18/05 \(Thứ 2\)__

T2

\[M7\] Dispense Doctype: cấp phát cho khoa/phòng và gắn bệnh nhân\. BHYT code mapping: bảng N01\-N09 tham số hóa \(config, không hard\-code\)\. Dual UOM: đơn vị mua ↔ đơn vị BHYT conversion\. Giá trần BHYT check

\[M7\] Dispense form: patient lookup \(mã BN\), chọn vật tư → auto\-fill mã BHYT \+ UOM \+ giá trần\. Cấp phát panel cho khoa\. Approve/reject flow\. BHYT group color coding

*M7: Dispense form BHYT mapping N01\-N09 Dual UOM engine*

3\.1\.5

__19/05 \(Thứ 3\)__

T3

\[M7\] Hoàn chỉnh: BHYT rate config \(80%/95%/100%\), actual vs dispensed quantity reconcile, BHYT report aggregation by patient/ward/code\. \[M9\] Inventory count plan Doctype: cycle count vs full count

\[M9\] Count sheet generation, mobile count entry \(scan barcode → nhập SL thực tế\), variance calculation, adjustment approval\. Variance report với drill\-down by item/location

*M7 COMPLETE M9: Inventory count Variance report*

3\.1\.6

__20/05 \(Thứ 4\)__

T4

\[M10\] Traceability engine: query theo lô → tìm toàn bộ transactions \(nhập/xuất/cấp phát\)\. Recall workflow: phát lệnh recall → alert tất cả kho \+ khoa có lô đó\. Audit trail report

\[M11\] Dashboard Frappe UI: 6 KPI cards \(tồn kho, đặt hàng, hết hạn, công nợ, cấp phát, kiểm kê\)\. Alert panel \(real\-time\)\. Charts: tiêu thụ theo tháng, top items

*M10: Traceability M11: Dashboard \+ Alerts*

3\.1\.7

__21/05 \(Thứ 5\)__

T5

Full system integration test: E2E flow từ NCC contract → PO → QC nhập kho → FEFO xuất kho → cấp phát bệnh nhân BHYT → kế toán → dashboard\. Performance test sơ bộ

End\-to\-end test scenarios: 5 full workflows với real data scenarios\. Bug report tổng hợp Sprint 1\+2\. Regression test M1\-M8\. Chuẩn bị UAT test cases \(30 scenarios\)

*Sprint 2 DONE 11 modules integrated E2E test report*

# 5\. PHASE 4 — UAT, ĐÀO TẠO & GO\-LIVE \(22–31/05/2026\)

__Giai đoạn cuối: __Deploy staging → UAT với người dùng thực tế → Bug fix → Đào tạo → Data migration → Go\-Live production 31/05/2026  __⚠️ Không trễ deadline\!__

__🚀 PHASE 4: UAT, ĐÀO TẠO & GO\-LIVE — TUẦN 4 \(22/05 – 31/05/2026\)__

__STT__

__Ngày__

__Thứ__

__Người 1 \(Dev Lead / Backend\)__

__Người 2 \(Dev / QA / Frontend\)__

__Deliverable__

__Trạng thái__

4\.1\.1

__22/05 \(Thứ 6\)__

T6

Deploy lên staging server: cấu hình Nginx, SSL, production settings, backup strategy\. Smoke test toàn bộ 11 modules trên staging\. Load test sơ bộ \(50 concurrent users\)

Setup UAT environment: tạo test accounts cho 5 nhóm user \(Kho, Khoa lâm sàng, Kế toán, CNTT, BGĐ\)\. Chuẩn bị 30 UAT test scenarios với test data thực tế

*Staging LIVE UAT environment ready Test accounts created*

4\.1\.2

__23/05 \(Thứ 7\)__

T7

UAT Session 1 — Nhóm Kho vật tư \(sáng\): hướng dẫn M1\-M3 trực tiếp\. Thu thập phản hồi, ghi nhận bugs\. UAT Session 2 — Nhóm Kế toán \(chiều\): M8 thanh toán, 3\-way matching

UAT facilitation \+ ghi chép: screen recording, bug screenshots, user feedback forms\. Phân loại bugs: P1 \(blocker\) / P2 \(major\) / P3 \(minor\)\. Bug tracker update

*UAT Round 1 \- Kho & Kế toán Bug list P1/P2/P3*

4\.1\.3

__24/05 \(CN\)__

CN

UAT Session 3 — Nhóm Khoa lâm sàng \(sáng\): M7 cấp phát BHYT, M6 luân chuyển\. UAT Session 4 — BGĐ \(chiều\): M11 dashboard, KPI review, báo cáo điều hành

Tổng hợp UAT Round 1: 30 scenarios tested, bug consolidation, UAT sign\-off checklist\. Chuẩn bị UAT Round 2 scenarios dựa trên feedback ngày 23

*UAT Round 1 DONE Sign\-off checklist Bug consolidated*

4\.1\.4

__25/05 \(Thứ 2\)__

T2

Bug fix sprint: xử lý toàn bộ P1 bugs \(blockers\) — mục tiêu 0 P1 bugs EOD\. Hotfix deploy lên staging sau mỗi fix\. Performance optimization: slow queries, index optimization

Bug fix: P2 bugs \(major\) — mục tiêu 80% P2 resolved\. Retest fixed bugs trên staging\. Update test cases với kết quả mới\. Chuẩn bị regression test suite

*P1 bugs: 0 remaining P2 bugs: 80% fixed Staging updated*

4\.1\.5

__26/05 \(Thứ 3\)__

T3

Fix P2 remaining \+ P3 bugs\. Security scan: check RBAC permissions, SQL injection test, authentication flows\. Performance benchmark: response times cho 5 critical workflows

Regression test đầy đủ: retest tất cả 30 UAT scenarios sau bug fixes\. Chuẩn bị UAT Round 2 với users\. Update user manual với UI thay đổi sau bug fixes

*All P1\+P2 bugs fixed Regression test PASS Security check OK*

4\.1\.6

__27/05 \(Thứ 4\)__

T4

Training Session 1 \(sáng 3h\): Phòng Vật tư & Thủ kho — M1\-M5 \(NCC, đặt hàng, nhập kho, QC, FEFO, WMS/PDA\)\. Training Session 2 \(chiều 3h\): Kế toán — M8 \(thanh toán, đối chiếu, GL\)

Tạo Training Materials: Quick Start Guide \(1 trang A4 per role\), video tutorial screenshots, FAQ document\. Setup help desk email/chat cho user support sau go\-live

*Training Day 1 DONE Quick Start Guides FAQ document*

4\.1\.7

__28/05 \(Thứ 5\)__

T5

Training Session 3 \(sáng 3h\): Khoa lâm sàng & Điều dưỡng — M6, M7 \(cấp phát BHYT, luân chuyển, cấp phát bệnh nhân\)\. Training Session 4 \(chiều 2h\): BGĐ & CNTT — M11, admin

Hoàn thiện User Manual đầy đủ \(PDF\)\. UAT Round 2 sign\-off: thu thập chữ ký xác nhận từ đại diện mỗi phòng ban\. Checklist Go\-Live readiness

*All users trained UAT sign\-off Go\-Live checklist*

4\.1\.8

__29/05 \(Thứ 6\)__

T6

Data Migration: import master data vào production — Supplier list, Item master, Warehouse structure, opening stock, Framework Contracts, BHYT code table \(N01\-N09\)

Data validation sau migration: kiểm tra 100% records đã import đúng, reconcile số lượng, test BHYT mapping với data thực tế bệnh viện

*Production data loaded Master data validated BHYT mapping tested*

4\.1\.9

__30/05 \(Thứ 7\)__

T7

Go/No\-Go Meeting \(09:00\): review Go\-Live checklist với stakeholders \(BGĐ, Kho, Kế toán, CNTT\)\. Production deploy: migrate code lên production server, final config, SSL, backup

Production smoke test: test toàn bộ 11 modules trên production với real data\. Monitoring setup: alert rules cho server health, error logs, slow queries\. Rollback plan documented

*GO/NO\-GO Decision Production deployed Monitoring active*

4\.1\.10

__31/05 \(CN\)__

CN

🚀 GO\-LIVE\! Monitoring hours 1\-4: theo dõi server metrics \(CPU, RAM, DB\), error logs\. Giờ 5\-8: user support trực tiếp tại bệnh viện\. Xử lý incidents P1 nếu phát sinh

Go\-Live support: hỗ trợ users tại các bộ phận trong 8 tiếng đầu\. Ghi nhận incident log\. Backup snapshot sau 8 tiếng go\-live thành công\. Lessons learned draft

*🎉 SYSTEM LIVE\! Incident log Backup snapshot Project DONE*

🚀

# 6\. RỦI RO THEO GIAI ĐOẠN & KẾ HOẠCH DỰ PHÒNG

__Phase__

__Ngày__

__Rủi ro__

__Tác động__

__Mức độ__

__Xác suất__

__Kế hoạch xử lý__

__P2__

08\-14/05

Frappe v15 có breaking changes chưa documented

Dev mất 1\-2 ngày debug, delay Sprint 1

🔴 Cao

40%

Đọc CHANGELOG kỹ trước, test trên branch riêng\. Buffer 4h/ngày cho debugging

__P2__

11\-12/05

BHYT logic phức tạp hơn dự kiến \(M7 early design\)

Delay M7 sang Sprint 2 không hoàn chỉnh

🔴 Cao

50%

Bắt đầu research BHYT rules từ ngày 10, có mockup sẵn cho M7

__P3__

15\-18/05

PDA/barcode hardware không tương thích \(M4\)

M4 WMS bị limited functionality

🟡 Trung bình

30%

Test với browser camera trước, native PDA là enhancement sau go\-live

__P3__

18\-19/05

Quy định BHYT N01\-N09 không đủ dữ liệu từ bệnh viện

M7 không map được đúng mã BHYT thực tế

🔴 Cao

45%

Thu thập bảng mã BHYT từ phòng kế hoạch bệnh viện trước ngày 15/05

__P4__

22\-24/05

UAT users không có thời gian tham gia đầy đủ

UAT không đủ scenario, bugs bị bỏ sót

🟡 Trung bình

40%

Book lịch UAT trước 7 ngày, chuẩn bị test script cho self\-testing

__P4__

25\-26/05

Bug P1 phát sinh nhiều sau UAT

Không đủ thời gian fix trước go\-live

🔴 Cao

35%

Cấp tốc mode: P1 fix < 4h mỗi bug, P2 defer sang post\-launch patch

__P4__

29/05

Data migration lỗi \(duplicate, encoding\)

Production data sai, delay go\-live

🟡 Trung bình

30%

Dry\-run migration 28/05 trên staging, script validation tự động

__P4__

31/05

Server performance kém khi nhiều users

Slow response, user frustration ngày đầu

🟡 Trung bình

25%

Pre\-warm cache, set max concurrent users = 50 tuần đầu, scale sau

# 7\. GO\-LIVE READINESS CHECKLIST

__\#__

__Hạng mục kiểm tra__

__Người kiểm tra__

__Deadline__

__Done?__

1

11 modules pass unit test

P1\+P2

28/05

☐

2

UAT sign\-off từ tất cả phòng ban

PM

28/05

☐

3

0 P1 \(critical\) bugs còn mở

P1\+P2

29/05

☐

4

Production server đủ cấu hình \(RAM/CPU/SSD\)

P1

28/05

☐

5

SSL certificate valid, domain configured

P1

29/05

☐

6

Backup tự động chạy & test restore

P1

29/05

☐

7

Master data đã migrate & validated

P1\+P2

29/05

☐

8

BHYT code table N01\-N09 đầy đủ

P1

28/05

☐

9

Toàn bộ users đã tạo tài khoản & phân quyền

P2

29/05

☐

10

Training hoàn thành cho tất cả nhóm user

P2

28/05

☐

11

Quick Start Guide đã phân phát

P2

29/05

☐

12

Monitoring alerts đã cấu hình

P1

30/05

☐

13

Rollback plan documented & tested

P1

30/05

☐

14

Support hotline/email đã thông báo cho users

P2

30/05

☐

15

Go/No\-Go approval từ BGĐ và PM

PM

30/05

☐

## 7\.1 Phê Duyệt Tài Liệu WBS

__Vai trò__

__Họ tên__

__Chữ ký__

__Ngày__

Project Manager / Dev Lead

Dev / QA

Trưởng phòng Vật tư

Trưởng phòng CNTT

