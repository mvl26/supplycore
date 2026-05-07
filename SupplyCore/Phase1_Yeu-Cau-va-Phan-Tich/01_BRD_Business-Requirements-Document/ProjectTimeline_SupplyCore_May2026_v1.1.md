__SUPPLYCORE__

__Hệ Thống Quản Lý Chuỗi Cung Ứng Vật Tư Tiêu Hao Bệnh Viện__

__KẾ HOẠCH TIẾN ĐỘ TRIỂN KHAI__

*Project Timeline – Tháng 5/2026*

Phiên bản: 1\.1 \(Cập nhật lịch biểu\)  |  Ngày: 05/05/2026

Nền tảng: Frappe Framework v15 \+ ERPNext v15  |  Mục tiêu: Go\-live 31/05/2026

# 1\. TÓM TẮT LỘ TRÌNH

SupplyCore được triển khai theo lịch biểu cấp tốc toàn bộ trong tháng 5/2026, chia thành 3 giai đoạn tập trung:

__Giai đoạn__

__Thời gian__

__Nội dung trọng tâm__

__Trạng thái__

__Giai đoạn 1 Thiết Kế__

Tuần 1 01/05 – 07/05/2026

Hoàn thiện toàn bộ tài liệu phân tích & thiết kế: BRD, URS, Use Case, As\-Is/To\-Be, System Architecture, Database Design, Technical Spec, API, UI/UX Mockups, Design System

__✓ HOÀN THÀNH \(05/05/2026\)__

__Giai đoạn 2 Dev – Build__

Tuần 2–3 08/05 – 21/05/2026

IT team phát triển và hoàn thiện đầy đủ 11 module: M1\-M11\. Mỗi module hoàn chỉnh theo Technical Spec đã được phê duyệt\. Unit test và integration test pass 100% trước 21/05

__⏳ ĐANG THỰC HIỆN Từ 08/05/2026__

__Giai đoạn 3 Thử Nghiệm & Tối Ưu__

Tuần 4 22/05 – 31/05/2026

Deploy staging, UAT với người dùng thực tế, ghi nhận & fix bug, performance tuning, đào tạo người dùng, migrate dữ liệu đầu kỳ, go\-live chính thức 31/05

__📋 KẾ HOẠCH Từ 22/05/2026__

# 2\. KẾ HOẠCH GANTT – THÁNG 5/2026

__Hạng mục công việc__

__Phụ trách__

__T1 01\-07/5__

__T2 08\-14/5__

__T3 15\-21/5__

__T4 22\-31/5__

__Ghi chú / Deliverable__

__▌ GIAI ĐOẠN 1 – THIẾT KẾ & TÀI LIỆU \(Tuần 1: 01–07/05\)__

BRD – Business Requirements Document

BA Team

 

✓ Hoàn thành 05/05

URS – User Requirements Specification

BA Team

 

✓ Hoàn thành 05/05

Use Case Diagram & Descriptions

BA Team

 

✓ Hoàn thành 05/05

As\-Is Process Flow

BA Team

 

✓ Hoàn thành 05/05

To\-Be Process Flow

BA Team

 

✓ Hoàn thành 05/05

System Architecture Diagram

Solution Architect

 

Tuần 1 – Phase 2 doc

Database Design \(ER Diagram, Schema\)

Solution Architect

 

Tuần 1 – Phase 2 doc

Technical Specification – 11 Modules

Solution Architect

 

Tuần 1 – Phase 2 doc

API Documentation

Solution Architect

 

Tuần 1 – Phase 2 doc

Security & Compliance Document

Solution Architect

 

Tuần 1 – Phase 2 doc

UI/UX Mockups & Wireframes

UI/UX Designer

 

Tuần 1 – Phase 3 doc

Design System Document

UI/UX Designer

 

Tuần 1 – Phase 3 doc

FRS, Non\-Func Req, Tech Stack, Deploy, Testing Strategy

BA \+ Architect

 

Tuần 1 – Phase 4 doc

__▌ GIAI ĐOẠN 2 – DEV BUILD 11 MODULES \(Tuần 2–3: 08–21/05\)__

M1 – Hợp đồng & Nhà cung cấp

Dev Team

 

 

Custom Doctype: Framework Contract, Release Order

M2 – Kế hoạch tồn kho & Gọi hàng

Dev Team

 

 

Auto reorder, EOQ, cảnh báo ROP

M3 – Tiếp nhận & Kiểm tra QC

Dev Team

 

 

QC checklist, partial receipt, barcode

M4 – WMS & PDA

Dev Team

 

 

Bin location, PDA interface, scan workflows

M5 – Lô, Hạn dùng & FEFO

Dev Team

 

 

Batch tracking, expiry alerts, FEFO auto\-select

M6 – Luân chuyển nội bộ

Dev Team

 

Inter\-warehouse transfer, 3\-tier warehouse

M7 – Cấp phát & Ghi nhận sử dụng

Dev Team

 

Patient\-linked dispensing, BHYT N01\-N09

M8 – Kế toán & Thanh toán NCC

Dev Team

 

 

3\-way matching, GL Entry auto, AP tracking

M9 – Kiểm kê & Đối soát

Dev Team

 

Stock reconciliation, PDA counting

M10 – Truy xuất & Điều tra

Dev Team

 

Batch trace, recall management

M11 – Dashboard & Cảnh báo

Dev Team

 

Executive dashboard, KPI widgets, alerts

Unit Test & Integration Test toàn hệ thống

QA Team

 

 

Test coverage ≥ 80%

__▌ GIAI ĐOẠN 3 – CHẠY THỬ & TỐI ƯU \(Tuần 4: 22–31/05\)__

Deploy môi trường staging

DevOps / IT

 

Server staging ready

UAT – Nhóm Mua hàng & Thủ kho

QA \+ Key Users

 

UAT checklist M1\-M4

UAT – Nhóm Khoa phòng & Điều dưỡng

QA \+ Key Users

 

UAT checklist M6\-M7

UAT – Kế toán & Kiểm kê

QA \+ Key Users

 

UAT checklist M8\-M9

Bug Fix – Ưu tiên P1/P2

Dev Team

 

Tất cả P1 fix trước 28/05

Performance tuning & Load test

Dev Team

 

Response ≤ 2s @ 50 users

Đào tạo người dùng \(fast\-track\)

PM \+ Trainer

 

Mỗi nhóm 2\-4 giờ

Migrate dữ liệu đầu kỳ \(tồn kho, danh mục\)

Dev \+ Data

 

Tồn kho đầu kỳ chính xác

Phê duyệt Go\-live & Go\-live chính thức

PM \+ Management

 

✓ Go\-live 31/05/2026

Thiết kế \(Hoàn thành\)

Dev Build

Chạy thử & Tối ưu

Chưa bắt đầu

# 3\. PHÂN RÃ CÔNG VIỆC TỪNG MODULE \(Tuần 2–3\)

Mỗi module được xây dựng theo nguyên tắc: tận dụng tối đa ERPNext standard, chỉ custom khi thực sự cần\. Ưu tiên các module core trước \(M1\-M3, M8\) trong tuần 2, sau đó hoàn thiện operations và analytics trong tuần 3\.

__Mã__

__Module__

__Nền tảng chính__

__Tuần Dev__

__Tính năng đặc thù cần custom__

__Custom Doctype/Script__

M1

Hợp đồng & NCC

ERPNext Supplier \+ Custom

Tuần 2

Framework Contract, Release Order, cảnh báo hết hạn HĐ

Framework Contract \(new Doctype\), Release Order \(new Doctype\)

M2

Kế hoạch tồn kho

ERPNext Reorder Level

Tuần 2

Min/Max/ROP per item per warehouse, auto PR creation, EOQ suggestion

Custom fields on Item, hooks\.py auto PR trigger

M3

Tiếp nhận & QC

ERPNext Purchase Receipt

Tuần 2

QC checklist bắt buộc, partial receipt, reject \+ biên bản

QC Inspection \(custom child table\), client script validation

M4

WMS & PDA

ERPNext \+ Custom UI

Tuần 2–3

Bin location, PDA\-optimized screen, barcode scan, 3\-tier warehouse

Bin Location Doctype, custom PDA page \(Frappe UI\), barcode hooks

M5

Lô, Hạn dùng & FEFO

ERPNext Batch \+ Custom

Tuần 2

FEFO auto\-select khi xuất kho, cảnh báo 30/60/90 ngày, block hết hạn

Override Stock Entry pick\_serial\_or\_batch\(\), scheduled alert jobs

M6

Luân chuyển nội bộ

ERPNext Stock Entry Transfer

Tuần 3

Workflow phê duyệt, yêu cầu chuyển kho từ khoa phòng

Material Transfer Request \(custom Doctype\), Workflow config

M7

Cấp phát & BHYT

Custom Doctype

Tuần 3

Phiếu cấp phát bệnh nhân, gán mã BHYT N01\-N09, tính phần BH/tự trả

Patient Dispensing \(new Doctype\), BHYT Config \(parametric\), Stock Entry hook

M8

Kế toán & Thanh toán

ERPNext Purchase Invoice \+ GL

Tuần 2

3\-way matching tự động, cảnh báo AP overdue, GL Entry auto

3\-way match script, AP aging dashboard widget

M9

Kiểm kê & Đối soát

ERPNext Stock Reconciliation

Tuần 3

Kế hoạch kiểm kê, PDA counting interface, so sánh tự động

Stock Count Plan \(custom Doctype\), PDA counting page

M10

Truy xuất & Điều tra

Custom Report \+ Doctype

Tuần 3

Batch trace full history, recall management, lock batch

Recall Alert \(custom Doctype\), batch traceability report

M11

Dashboard & Cảnh báo

Frappe Dashboard \+ Custom Widgets

Tuần 3

Executive KPI cards, RAG status, cảnh báo email tự động

Custom Dashboard Page \(Vue 3\), Alert Config \(parametric\), scheduled jobs

# 4\. KẾ HOẠCH TUẦN 4 – CHẠY THỬ & TỐI ƯU

## 4\.1 Lịch UAT Chi Tiết \(22–31/05/2026\)

__Ngày__

__Nhóm tham gia__

__Module kiểm thử__

__Nội dung kiểm thử__

__Tiêu chí pass__

22\-23/05

NV Mua hàng, Quản lý VT

M1, M2, M3

Tạo NCC, HĐ khung, Release Order, tiếp nhận hàng, QC, nhập kho

100% use case P1 pass, không có lỗi block

23\-24/05

Thủ kho

M4, M5

Scan barcode, PDA workflows, FEFO khi xuất kho, cảnh báo hạn dùng

FEFO 100% đúng, scan < 2 giây

25\-26/05

Điều dưỡng trưởng khoa

M6, M7

Yêu cầu chuyển kho, cấp phát bệnh nhân, gán mã BHYT, tính chi phí

Mã BHYT tự động đúng 100% test cases

26\-27/05

Kế toán

M8

3\-way matching, hạch toán GL tự động, thanh toán NCC, báo cáo công nợ

GL Entry đúng 100%, 3\-way match < 1 phút

27\-28/05

Thủ kho, Quản lý

M9, M10

Kiểm kê bằng PDA, xử lý chênh lệch, test recall theo số lô

Recall trace < 5 phút, kiểm kê đúng

28\-29/05

Ban Giám đốc, Quản lý

M11

Dashboard KPI, cảnh báo tự động, báo cáo điều hành, phê duyệt mobile

Dashboard load < 3 giây

29\-30/05

Dev \+ QA

Toàn hệ thống

Fix tất cả bug P1, P2 được ghi nhận\. Performance test 50 concurrent users

Không còn P1 bug\. Response ≤ 2s

30\-31/05

PM \+ IT \+ Lãnh đạo

Toàn hệ thống

Migrate dữ liệu đầu kỳ, đào tạo lần cuối, phê duyệt Go\-live, chuyển sang Production

__✓ GO\-LIVE 31/05/2026__

## 4\.2 Tiêu Chí Go\-live \(Definition of Done\)

__STT__

__Tiêu chí__

__Chỉ số đo lường__

__Kết quả__

1

Tất cả 11 module hoạt động đúng chức năng

100% use case P1 pass trong UAT

□ Pass

2

Hiệu năng đạt yêu cầu

Response ≤ 2s với 50 concurrent users

□ Pass

3

Không có bug P1 còn mở

0 critical/blocker bugs

□ Pass

4

Dữ liệu đầu kỳ đã migrate đúng

Kiểm kê đầu kỳ khớp 100% với sổ sách hiện tại

□ Pass

5

Người dùng đã được đào tạo

≥ 1 người/nhóm hoàn thành đào tạo và ký xác nhận

□ Pass

6

Backup & Recovery đã kiểm tra

Restore thành công từ backup trong < 30 phút

□ Pass

7

Lãnh đạo ký phê duyệt Go\-live

Chữ ký xác nhận từ Giám đốc bệnh viện

□ Ký

─────────────────────────────────────────────────────────────────────────────

Mục tiêu go\-live: 31/05/2026\. Mọi thay đổi lịch biểu phải được Giám đốc dự án phê duyệt bằng văn bản\. Sau go\-live, hỗ trợ vận hành 24/7 trong 2 tuần đầu tiên\.

