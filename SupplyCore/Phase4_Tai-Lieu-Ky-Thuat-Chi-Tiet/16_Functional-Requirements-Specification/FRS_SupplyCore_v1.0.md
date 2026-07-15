__SUPPLYCORE__

Hospital Supply Chain Management Platform

__FUNCTIONAL REQUIREMENTS SPECIFICATION__

Đặc tả Yêu cầu Chức năng Chi tiết

Phase 4 – Tài liệu số 16/20

__Phiên bản:__

1\.0

__Ngày:__

05/05/2026

__Phân loại ưu tiên:__

MUST \(bắt buộc\) | SHOULD \(nên có\) | COULD \(có thể có\)

__Tổng FRs:__

55 Functional Requirements – 11 Modules

__Phạm vi:__

SupplyCore Phase 1 – M1 đến M11 \(không bao gồm thuốc, TSCĐ\)

# __MỤC LỤC__

1\. Tổng quan & Quy ước

2\. M1 – Hợp đồng & Nhà cung cấp \(FR\-M1\-001 → 005\)

3\. M2 – Kế hoạch tồn kho & Gọi hàng \(FR\-M2\-001 → 005\)

4\. M3 – Tiếp nhận & Kiểm tra QC \(FR\-M3\-001 → 005\)

5\. M4 – WMS & PDA \(FR\-M4\-001 → 005\)

6\. M5 – Lô, Hạn dùng & FEFO \(FR\-M5\-001 → 005\)

7\. M6 – Luân chuyển nội bộ \(FR\-M6\-001 → 005\)

8\. M7 – Cấp phát & Ghi nhận sử dụng \(FR\-M7\-001 → 005\)

9\. M8 – Kế toán & Thanh toán \(FR\-M8\-001 → 005\)

10\. M9 – Kiểm kê & Đối soát \(FR\-M9\-001 → 005\)

11\. M10 – Truy xuất & Điều tra \(FR\-M10\-001 → 005\)

12\. M11 – Dashboard & Cảnh báo điều hành \(FR\-M11\-001 → 005\)

13\. Ma trận Traceability

# __1\. TỔNG QUAN & QUY ƯỚC__

## __1\.1 Cấu trúc FR ID__

__Trường__

__Format__

__Ví dụ__

__FR ID__

FR\-MX\-NNN

FR\-M1\-001 = Module 1, Requirement 001

__Priority__

MUST/SHOULD/COULD

MUST: bắt buộc Phase 1 | SHOULD: nên có | COULD: backlog

__Actor__

Role code

SC\-STOREKEEPER, SC\-WARD\-STAFF, SC\-ACCOUNTANT, SC\-MANAGER, SC\-EXECUTIVE, SC\-SYSADMIN

## __1\.2 Tổng hợp số lượng FR theo Module__

__Module__

__Tên__

__MUST__

__SHOULD__

__COULD__

__Mô tả ngắn__

__M1__

Hợp đồng & NCC

4

1

0

Framework Contract, Release Order, quản lý NCC

__M2__

Kế hoạch & Gọi hàng

3

2

0

Reorder point, auto\-suggest PO, lịch gọi hàng

__M3__

Tiếp nhận & QC

4

1

0

Purchase Receipt, QC checklist, từ chối hàng

__M4__

WMS & PDA

3

1

1

Barcode scan, sơ đồ kho, PDA offline mode

__M5__

Lô, Hạn & FEFO

4

1

0

Batch tracking, FEFO auto\-pick, cảnh báo hạn

__M6__

Luân chuyển nội bộ

3

2

0

Stock Entry transfer, phê duyệt nội bộ

__M7__

Cấp phát & Sử dụng

4

1

0

Dispensing Request, Patient Dispensing, BHYT

__M8__

Kế toán & TT

4

1

0

3\-way match, Payment Entry, công nợ NCC

__M9__

Kiểm kê & Đối soát

3

2

0

Stock Reconciliation, chênh lệch, phê duyệt

__M10__

Truy xuất & Điều tra

3

1

1

Batch trace, recall notice, audit trail

__M11__

Dashboard & Cảnh báo

3

2

0

KPI dashboard, alert engine, scheduled report

# __2\. M1 – HỢP ĐỒNG & NHÀ CUNG CẤP__

__M1 – Hợp đồng & Nhà cung cấp__

ERPNext: Supplier, Contact, ERPNext Supplier Portal

Custom Doctype: Framework Contract, FC Item, Release Order

__FR\-M1\-001__

__MUST__

__Tạo và quản lý Hợp đồng Khung \(Framework Contract\)__

Actor: SC\-MANAGER, SC\-STOREKEEPER

__Mô tả__

Hệ thống cho phép tạo Hợp đồng Khung với NCC, định nghĩa danh mục vật tư được phép mua, giá trần và hạn mức giá trị\.

__Input__

• Mã hợp đồng \(auto: SC\-FC\-YYYY\-NNNNN\)

• Nhà cung cấp \(link Supplier\)

• Ngày hiệu lực – Ngày hết hạn

• Danh sách vật tư: Item Code, đơn giá trần, đơn vị tính, hạn mức SL

• Tổng giá trị hợp đồng max

• File đính kèm PDF hợp đồng

__Output__

• Framework Contract document lưu trong hệ thống

• FC Item records với giá và hạn mức

• Trạng thái: Draft → Submitted → Active / Expired / Cancelled

__Business Rules__

• Một NCC có thể có nhiều FC nhưng chỉ 1 Active tại một thời điểm cho một nhóm vật tư

• Giá trong PO không được vượt giá trần FC; nếu vượt: warning \+ cần SC\-MANAGER override

• FC hết hạn: tự động chuyển trạng thái Expired, cảnh báo 30 ngày trước

• Không thể sửa FC đã Submitted; phải tạo Amendment

__Acceptance Criteria__

✓ Tạo FC mới thành công → ID được gán, trạng thái Draft

✓ Submit FC → trạng thái Active, vật tư trong FC khả dụng khi tạo PO

✓ Tạo PO với giá > giá trần FC → hệ thống hiện warning dialog

✓ FC hết hạn tự động 0:00 ngày hết hạn; email thông báo gửi SC\-MANAGER

__FR\-M1\-002__

__MUST__

__Tạo Release Order từ Hợp đồng Khung__

Actor: SC\-STOREKEEPER, SC\-MANAGER

__Mô tả__

Khi có nhu cầu mua hàng, hệ thống cho phép tạo Release Order \(đặt hàng cụ thể\) từ Framework Contract đang Active\.

__Input__

• Chọn Framework Contract \(FC đang Active\)

• Chọn vật tư trong FC, nhập số lượng

• Ngày giao hàng dự kiến

• Địa chỉ giao hàng \(Kho Tổng / Kho Con\)

__Output__

• Release Order document \(link to FC\)

• Tự động tạo Purchase Order trong ERPNext

• Cập nhật hạn mức đã sử dụng trong FC

__Business Rules__

• SL đặt \+ SL đã đặt trước không được vượt hạn mức SL trong FC

• Tổng giá trị Release Order tích lũy không được vượt total value FC

• Release Order approved → tự động tạo PO tương ứng

__Acceptance Criteria__

✓ Chọn FC → auto\-fill thông tin NCC, điều khoản thanh toán

✓ Nhập SL > hạn mức → validation error ngay lập tức

✓ Release Order submitted → PO tương ứng được tạo tự động

__FR\-M1\-003__

__MUST__

__Quản lý danh mục Nhà cung cấp__

Actor: SC\-MANAGER, SC\-STOREKEEPER

__Mô tả__

Quản lý thông tin NCC bao gồm đánh giá hiệu suất, điều khoản thanh toán và lịch sử giao dịch\.

__Input__

• Thông tin NCC: tên, MST, địa chỉ, người liên hệ, email, số điện thoại

• Điều khoản thanh toán: số ngày, hình thức

• Nhóm NCC: nhóm hàng chính mà NCC cung cấp

• Score card: tỷ lệ giao đúng hạn, tỷ lệ QC đạt

__Output__

• Supplier Profile đầy đủ trong ERPNext

• Score card tự động tính từ lịch sử PO/Receipt

• Danh sách NCC lọc được theo nhóm, trạng thái

__Business Rules__

• NCC phải có MST hợp lệ \(định dạng 10 hoặc 13 số\)

• Không thể xóa NCC đã có giao dịch; chỉ có thể Disable

• Score card tính tự động hàng tuần từ Purchase Receipt

__Acceptance Criteria__

✓ Tạo NCC mới với MST hợp lệ → lưu thành công

✓ Score card NCC hiển thị đúng % giao đúng hạn dựa trên lịch sử

✓ Disable NCC → không xuất hiện trong dropdown tạo PO

__FR\-M1\-004__

__MUST__

__Cảnh báo hợp đồng sắp hết hạn__

Actor: SC\-MANAGER

__Mô tả__

Hệ thống tự động phát hiện và cảnh báo khi Hợp đồng Khung sắp hết hạn hoặc sắp hết hạn mức giá trị\.

__Input__

• Scheduler job chạy mỗi ngày 8:00

• Ngưỡng cảnh báo: 30 ngày trước hết hạn \(configurable\)

• Ngưỡng cảnh báo hạn mức: < 20% còn lại

__Output__

• Alert record trong SupplyCore Alert

• Email notification gửi SC\-MANAGER

• Dashboard widget M11 hiện số FC cần gia hạn

__Business Rules__

• Cảnh báo không làm gián đoạn hoạt động hiện tại của FC

• Không gửi cảnh báo lặp lại trong cùng 1 ngày cho cùng 1 FC

• Cảnh báo hết hạn mức gửi khi < 20% và khi < 10%

__Acceptance Criteria__

✓ FC còn 28 ngày hết hạn → cảnh báo hiện trong Dashboard M11

✓ Email gửi SC\-MANAGER trong vòng 5 phút sau khi scheduler chạy

✓ Hạn mức FC < 20% → badge vàng; < 10% → badge đỏ

__FR\-M1\-005__

__SHOULD__

__Xem lịch sử giao dịch theo NCC__

Actor: SC\-ACCOUNTANT, SC\-MANAGER

__Mô tả__

Xem toàn bộ lịch sử đặt hàng, nhận hàng và thanh toán cho từng NCC trong khoảng thời gian chọn\.

__Input__

• Chọn NCC

• Khoảng thời gian \(từ ngày – đến ngày\)

• Loại giao dịch: PO / Receipt / Invoice / Payment

__Output__

• Bảng tổng hợp theo tháng: SL đặt, SL nhận, tổng tiền, đã thanh toán

• Biểu đồ cột chi phí theo tháng

• Export Excel/PDF

__Business Rules__

• Dữ liệu lấy real\-time từ ERPNext standard reports

• Chỉ hiện giao dịch đã Submitted \(không hiện Draft\)

__Acceptance Criteria__

✓ Chọn NCC \+ khoảng thời gian → báo cáo hiển thị trong < 3 giây

✓ Export Excel thành công với đầy đủ cột dữ liệu

# __3\. M2 – KẾ HOẠCH TỒN KHO & GỌI HÀNG__

__M2 – Kế hoạch tồn kho & Gọi hàng__

ERPNext: Item, Reorder Point \(ERPNext standard\), Purchase Order

Custom Doctype: SupplyCore Settings \(reorder config\)

__FR\-M2\-001__

__MUST__

__Cấu hình ngưỡng tồn kho tối thiểu và tái đặt hàng__

Actor: SC\-MANAGER, SC\-STOREKEEPER

__Mô tả__

Cho phép cấu hình ngưỡng tồn kho tối thiểu \(min\_qty\), điểm tái đặt hàng \(reorder\_point\) và số lượng đặt hàng kinh tế \(EOQ\) cho từng vật tư / kho\.

__Input__

• Item Code

• Warehouse

• Min Qty \(ngưỡng tối thiểu an toàn\)

• Reorder Point \(điểm kích hoạt đặt hàng\)

• Reorder Qty \(SL đặt khi kích hoạt\)

• Lead Time \(ngày dự kiến nhận hàng từ NCC\)

__Output__

• Item Reorder record trong ERPNext

• Lưu trong SupplyCore Settings per\-item per\-warehouse

__Business Rules__

• Reorder Point phải >= Min Qty

• EOQ phải > 0

• Lead Time phải > 0 ngày

• Cùng 1 vật tư\-kho chỉ có 1 cấu hình active

__Acceptance Criteria__

✓ Lưu cấu hình cho vật tư VT\-001 tại Kho Tổng → thành công

✓ Reorder Point < Min Qty → validation error khi save

__FR\-M2\-002__

__MUST__

__Tự động gợi ý tạo PO khi tồn kho đạt Reorder Point__

Actor: SC\-STOREKEEPER, SC\-MANAGER

__Mô tả__

Scheduler hàng ngày kiểm tra tồn kho thực tế, nếu tồn kho <= Reorder Point thì tự động tạo Draft PO và thông báo cho người dùng\.

__Input__

• Actual Stock từ ERPNext Stock Ledger Entry

• Reorder configuration đã cấu hình

• Preferred Supplier từ Item Supplier table

__Output__

• Draft Purchase Order với vật tư, SL=Reorder Qty, NCC từ Item Supplier

• Alert thông báo cho SC\-STOREKEEPER

• Log entry ghi lại trigger

__Business Rules__

• Chỉ tạo Draft PO khi chưa có Draft PO pending cho cùng vật tư\-kho

• Không tạo PO nếu NCC không có FC Active \(chỉ cảnh báo\)

• Scheduler chạy hàng ngày lúc 7:00 sáng

• PO tạo tự động phải được SC\-STOREKEEPER review và Submit

__Acceptance Criteria__

✓ Tồn kho Gang tay <= 50 \(reorder point\) → Draft PO tự tạo trước 7:30

✓ Draft PO có đúng vật tư, SL, NCC từ config

✓ Đã có Draft PO pending → không tạo thêm, chỉ cảnh báo

__FR\-M2\-003__

__MUST__

__Xem kế hoạch tồn kho tổng hợp__

Actor: SC\-MANAGER, SC\-STOREKEEPER

__Mô tả__

Dashboard kế hoạch tồn kho hiển thị tình trạng tất cả vật tư: tồn thực tế, tồn min, reorder point, PO đang mở, dự báo thiếu\.

__Input__

• Danh sách Item \+ Warehouse

• Filter: kho, nhóm vật tư, trạng thái \(OK / Cảnh báo / Thiếu\)

__Output__

• Bảng tổng hợp: vật tư, kho, tồn thực, min, reorder, PO pending, dự báo

• Color coding: Xanh \(OK\), Vàng \(sắp tới reorder point\), Đỏ \(dưới min\)

__Business Rules__

• Dự báo thiếu = Tồn thực – \(Tiêu thụ trung bình 30 ngày × Lead Time\)

__Acceptance Criteria__

✓ Tải trang kế hoạch tồn kho → dữ liệu hiển thị đầy đủ < 5 giây

✓ Vật tư tồn < min\_qty → row màu đỏ rõ ràng

__FR\-M2\-004__

__SHOULD__

__Tạo kế hoạch mua hàng định kỳ \(Purchase Plan\)__

Actor: SC\-MANAGER

__Mô tả__

Cho phép tạo kế hoạch mua hàng theo chu kỳ tháng/quý dựa trên tiêu thụ lịch sử và nhu cầu dự kiến\.

__Input__

• Khoảng thời gian kế hoạch \(tháng/quý\)

• Tiêu thụ lịch sử N tháng

• Nhu cầu bổ sung \(nếu có sự kiện đặc biệt\)

__Output__

• Purchase Plan document với danh sách vật tư và SL dự kiến

• Tổng giá trị ước tính theo giá FC

• So sánh với ngân sách năm

__Business Rules__

• Kế hoạch dựa trên Moving Average 3 tháng gần nhất

• Kế hoạch phải được SC\-MANAGER approve trước khi trigger PO

__Acceptance Criteria__

✓ Tạo kế hoạch Q3/2026 → hiện danh sách vật tư với SL đề xuất

✓ Total value kế hoạch hiển thị đúng = Σ\(SL × giá FC\)

__FR\-M2\-005__

__SHOULD__

__Cảnh báo tồn kho bất thường \(đột biến tiêu thụ\)__

Actor: SC\-MANAGER

__Mô tả__

Phát hiện khi tiêu thụ vật tư trong tuần vượt quá 150% mức trung bình 4 tuần, cảnh báo để điều chỉnh kế hoạch kịp thời\.

__Input__

• Stock Ledger Entry trong 7 ngày gần nhất

• Moving Average consumption 4 tuần trước

__Output__

• Alert record mức độ MEDIUM

• Email SC\-MANAGER và SC\-STOREKEEPER liên quan

__Business Rules__

• Ngưỡng bất thường: tiêu thụ tuần > 150% MA4W \(configurable\)

• Không alert nếu vật tư đang trong đợt dùng theo kế hoạch đặc biệt

__Acceptance Criteria__

✓ Tiêu thụ tuần tăng 200% → alert hiện trong Alert Center trong 1 giờ

# __4\. M3 – TIẾP NHẬN & KIỂM TRA CHẤT LƯỢNG__

__M3 – Tiếp nhận & Kiểm tra QC__

ERPNext: Purchase Receipt \(ERPNext\), Quality Inspection

Custom Doctype: Custom fields: lot\_number, expiry\_date, qc\_result trên Purchase Receipt Item

__FR\-M3\-001__

__MUST__

__Tạo Purchase Receipt với kiểm tra QC cơ bản__

Actor: SC\-STOREKEEPER

__Mô tả__

Khi nhận hàng từ NCC, tạo Purchase Receipt với thông tin đầy đủ về lô, hạn dùng, số lượng thực nhận và kết quả QC sơ bộ\.

__Input__

• Purchase Order \(link\)

• Vật tư, số lượng thực nhận

• Số lô \(Batch Number\)

• Hạn dùng \(Expiry Date\)

• Quy cách thực tế \(actual\_package\)

• Kết quả QC: ĐẠT / KHÔNG ĐẠT / CHỜ KIỂM

• Ghi chú QC

• Ảnh chụp \(optional\)

__Output__

• Purchase Receipt document \(Submitted\)

• Batch record tự động tạo với lot number \+ expiry

• Stock Ledger Entry cập nhật tồn kho

• QC result lưu trên Receipt Item

__Business Rules__

• Số lô bắt buộc cho TẤT CẢ vật tư \(không có ngoại lệ\)

• Hạn dùng bắt buộc; phải > ngày hôm nay \+ 30 ngày \(configurable\)

• SL thực nhận không được vượt SL trong PO \+ 5% tolerance

• QC = KHÔNG ĐẠT → hàng nhập kho đặc biệt 'Kho Cách ly', KHÔNG nhập vào kho thường

• Không thể submit Receipt nếu thiếu Batch / Expiry / QC result

__Acceptance Criteria__

✓ Receipt với đầy đủ lot, expiry, QC → Submit thành công

✓ Hạn dùng < hôm nay \+ 30 ngày → validation error block submit

✓ QC KHÔNG ĐẠT → tự động chuyển hàng vào Kho Cách ly

✓ SL nhận > SL PO \+ 5% → block submit với thông báo rõ ràng

__FR\-M3\-002__

__MUST__

__Scan barcode để auto\-fill thông tin lô và hạn dùng__

Actor: SC\-STOREKEEPER

__Mô tả__

Hỗ trợ scan barcode GS1\-128 trên thùng hàng để tự động điền số lô, hạn dùng, mã vật tư vào Receipt\.

__Input__

• Barcode scan từ PDA hoặc barcode reader USB

• GS1\-128 data: GTIN, Lot Number, Expiry Date

• Hoặc nhập thủ công nếu barcode không đọc được

__Output__

• Auto\-fill: Item Code, Batch Number, Expiry Date trong Receipt row

• Hiển thị confirmation để user xác nhận trước khi áp dụng

__Business Rules__

• Nếu GTIN không map được sang Item Code → hiện lookup dialog để user chọn thủ công

• Nếu scan 1 item nhiều lần → cộng dồn SL

• Hạn dùng định dạng GS1: YYMMDD → convert sang DD/MM/YYYY

__Acceptance Criteria__

✓ Scan barcode hợp lệ → auto\-fill đúng lot, expiry trong < 1 giây

✓ Barcode không nhận dạng được → hiện manual input dialog

✓ Scan 2 lần cùng barcode → SL tăng lên 2

__FR\-M3\-003__

__MUST__

__Quy trình xử lý hàng không đạt QC__

Actor: SC\-STOREKEEPER, SC\-MANAGER

__Mô tả__

Khi QC KHÔNG ĐẠT, hệ thống tạo quy trình xử lý: nhập kho cách ly, thông báo NCC, trả hàng hoặc chấp nhận chiết khấu\.

__Input__

• Purchase Receipt với QC = KHÔNG ĐẠT

• Lý do không đạt \(chọn từ danh sách \+ ghi chú\)

• Quyết định xử lý: Trả hàng / Chấp nhận chiết khấu / Hủy

__Output__

• Stock Entry: nhập vào Kho Cách ly \(không vào kho thường\)

• Rejection Note gửi NCC

• Nếu trả hàng: tạo Purchase Return; Nếu chiết khấu: điều chỉnh Purchase Invoice

__Business Rules__

• Hàng QC KHÔNG ĐẠT KHÔNG ĐƯỢC phép nhập vào kho thường

• Quyết định xử lý phải được SC\-MANAGER approve

• Lý do từ chối phải chọn từ danh mục chuẩn \(configurable\)

__Acceptance Criteria__

✓ QC KHÔNG ĐẠT → hàng chỉ trong Kho Cách ly, không vào kho thường

✓ Rejection Note tạo thành công, có thể print

✓ SC\-MANAGER approve trả hàng → Purchase Return tạo tự động

__FR\-M3\-004__

__MUST__

__Dashboard tiếp nhận hàng hóa theo ngày__

Actor: SC\-STOREKEEPER, SC\-MANAGER

__Mô tả__

Dashboard hiển thị danh sách PO dự kiến giao hàng hôm nay và trong tuần, trạng thái nhận hàng từng PO\.

__Input__

• Danh sách PO với expected delivery date

• Filter: hôm nay / tuần này / quá hạn

__Output__

• PO list với: NCC, vật tư chính, SL, expected date, trạng thái

• Trạng thái: Chưa nhận / Nhận một phần / Đã nhận / Quá hạn

• Tổng số PO theo trạng thái \(KPI row\)

__Business Rules__

• PO quá hạn giao > 3 ngày → highlight đỏ \+ cảnh báo SC\-MANAGER

• Dữ liệu refresh mỗi 5 phút

__Acceptance Criteria__

✓ Dashboard tải đầy đủ PO hôm nay < 3 giây

✓ PO quá hạn hiển thị màu đỏ với số ngày trễ

__FR\-M3\-005__

__SHOULD__

__Tổng hợp báo cáo QC theo NCC và vật tư__

Actor: SC\-MANAGER

__Mô tả__

Báo cáo định kỳ về tỷ lệ đạt/không đạt QC theo NCC, loại vật tư, thời gian để đánh giá hiệu suất NCC\.

__Input__

• Khoảng thời gian

• Nhóm theo: NCC / Loại vật tư / Kho

__Output__

• Bảng: NCC → tổng Receipt → % đạt QC → xu hướng 3 tháng

• Highlight NCC có % đạt QC < 95% \(ngưỡng configurable\)

• Export Excel/PDF

__Business Rules__

• Chỉ tính Receipt đã Submitted

• % = \(Số receipt đạt\) / \(Tổng receipt\) × 100

__Acceptance Criteria__

✓ Báo cáo QC tháng 4 cho tất cả NCC → load < 5 giây

✓ NCC < 95% đạt → hiển thị màu đỏ trong bảng

# __5\. M4 – WMS & PDA__

__M4 – WMS & PDA__

ERPNext: Warehouse \(ERPNext\), Stock Entry, Serial No

Custom Doctype: Custom fields: bin\_location trên Warehouse Bin; WMS Scan Log

__FR\-M4\-001__

__MUST__

__Quản lý vị trí kho \(Bin Location\)__

Actor: SC\-STOREKEEPER

__Mô tả__

Quản lý kho theo cấu trúc 3 tầng: Kho → Khu → Kệ \(Bin\)\. Mỗi vật tư\-lô có vị trí cụ thể\.

__Input__

• Warehouse: Kho Tổng, Kho Con, Kho Khoa Phòng

• Zone: Khu A, B, C

• Bin: Kệ A1, A2, \.\.\.

• Item \+ Batch \+ Bin mapping

__Output__

• Bin Location record: kho \+ zone \+ bin \+ item \+ batch \+ SL

• Sơ đồ kho hiển thị dạng visual grid

• Tìm kiếm vị trí theo Item/Batch

__Business Rules__

• 1 Bin có thể chứa nhiều Item/Batch

• 1 Batch của 1 Item chỉ ở 1 Bin \(trừ khi split\)

• Bin capacity không vượt max\_capacity \(configurable\)

__Acceptance Criteria__

✓ Gán vật tư vào Bin A1 → lưu thành công

✓ Tìm 'Gang tay LOT\-G\-2026' → hiện đúng vị trí kệ

✓ Bin > capacity → cảnh báo khi gán thêm

__FR\-M4\-002__

__MUST__

__Scan barcode PDA để di chuyển hàng \(putaway/pick\)__

Actor: SC\-STOREKEEPER

__Mô tả__

Dùng PDA scanner để thực hiện putaway \(gán vị trí khi nhập kho\) và pick \(lấy hàng khi cấp phát/chuyển kho\)\.

__Input__

• Scan barcode lô/vật tư

• Chọn action: Putaway / Pick

• Nhập/confirm vị trí Bin

• Nhập số lượng thực tế

__Output__

• WMS Scan Log record

• Cập nhật Bin Location

• Stock Entry draft \(nếu pick\)

__Business Rules__

• Putaway: gợi ý Bin còn trống/phù hợp dựa trên loại vật tư

• Pick: FEFO tự động gợi ý lấy lô hạn gần nhất

• Scan ngoài phạm vi warehouse → báo lỗi

• Tất cả scan action được log với timestamp \+ user

__Acceptance Criteria__

✓ Scan barcode LOT\-G\-2026 → hiện vật tư, lô, vị trí đúng

✓ Putaway → gợi ý Bin dựa trên FEFO trong < 1 giây

✓ Pick → Stock Entry draft tạo tự động

__FR\-M4\-003__

__MUST__

__PDA Offline Mode – đồng bộ sau khi có mạng__

Actor: SC\-STOREKEEPER

__Mô tả__

PDA hoạt động offline \(không có WiFi trong kho\), lưu scan data vào IndexedDB cục bộ, đồng bộ khi có mạng\.

__Input__

• Scan actions offline: putaway, count, pick

• Local IndexedDB storage

• WiFi reconnect trigger sync

__Output__

• Sync queue upload lên SupplyCore API

• Conflict detection và resolution

• Sync report: số bản ghi thành công / thất bại

__Business Rules__

• Offline mode tối đa 8 giờ \(1 ca làm việc\)

• Conflict: server\-wins cho trường hợp inventory count

• User được thông báo khi có conflict cần giải quyết thủ công

• Sync phải hoàn thành trong < 30 giây cho tối đa 200 bản ghi

__Acceptance Criteria__

✓ Scan 50 items offline → upload thành công khi có WiFi

✓ Conflict item hiển thị rõ để user quyết định

✓ Sync 200 records hoàn tất trong < 30 giây

__FR\-M4\-004__

__SHOULD__

__Báo cáo tồn kho thực tế theo vị trí__

Actor: SC\-STOREKEEPER, SC\-MANAGER

__Mô tả__

Báo cáo tồn kho chi tiết theo kho / zone / bin, hiển thị từng lô vật tư với số lượng, hạn dùng và ngày nhập\.

__Input__

• Filter: kho, zone, bin, nhóm vật tư, hạn dùng

__Output__

• Bảng: Bin → Item → Batch → SL → Expiry → Ngày nhập kho

• Sort theo expiry date \(FEFO view\)

• Export Excel / in nhãn kho

__Business Rules__

• Dữ liệu real\-time từ ERPNext Stock Ledger

• Chỉ hiện tồn > 0

__Acceptance Criteria__

✓ Báo cáo Kho Tổng → hiện đủ tất cả bin và lô < 5 giây

✓ Sort theo expiry → lô gần hết hạn nhất lên đầu

__FR\-M4\-005__

__COULD__

__In nhãn barcode vị trí kho và vật tư__

Actor: SC\-STOREKEEPER

__Mô tả__

In nhãn barcode cho kệ kho và nhãn lô vật tư để dán lên sản phẩm và kệ phục vụ scan PDA\.

__Input__

• Chọn: nhãn kệ hoặc nhãn lô

• Chọn template nhãn \(kích thước, thông tin\)

• Số lượng bản in

__Output__

• PDF file nhãn barcode sẵn sàng để in

• Hỗ trợ: Code128, GS1\-128, QR Code

__Business Rules__

• Nhãn kệ: Bin ID \+ Zone \+ Warehouse

• Nhãn lô: Item Code \+ Batch \+ Expiry \+ barcode

__Acceptance Criteria__

✓ In nhãn lô LOT\-G\-2026 → PDF barcode đúng thông tin

# __6\. M5 – LÔ, HẠN DÙNG & FEFO__

__M5 – Lô, Hạn dùng & FEFO__

ERPNext: Batch \(ERPNext\), FIFO/FEFO stock settings

Custom Doctype: Custom batch fields: manufacturer, manufacturing\_date, qc\_status

__FR\-M5\-001__

__MUST__

__Tracking lô hàng xuyên suốt vòng đời__

Actor: SC\-STOREKEEPER

__Mô tả__

Mỗi lô vật tư được theo dõi đầy đủ từ khi nhập kho đến khi cấp phát hoặc hủy, bao gồm trạng thái và vị trí tại mọi thời điểm\.

__Input__

• Batch Number \(từ NCC hoặc tạo nội bộ\)

• Manufacturing Date

• Expiry Date

• Nhà sản xuất

• QC Status: PASS / FAIL / PENDING

• SL hiện tại, vị trí, trạng thái

__Output__

• Batch Ledger: lịch sử tất cả movement của lô

• Current Status: Active / Expired / Quarantine / Consumed / Recalled

__Business Rules__

• 1 Batch Number là duy nhất trong 1 Item

• Không thể modify Expiry Date sau khi đã có Stock Entry

• Batch hết hạn → tự động chuyển trạng thái Expired lúc 0:00

__Acceptance Criteria__

✓ Xem batch LOT\-G\-2026 → hiện đầy đủ lịch sử nhập/xuất/vị trí

✓ Batch qua ngày Expiry → trạng thái tự đổi Expired

✓ Không thể cấp phát batch Expired hoặc Quarantine

__FR\-M5\-002__

__MUST__

__FEFO auto\-selection khi cấp phát hoặc chuyển kho__

Actor: SC\-STOREKEEPER

__Mô tả__

Khi tạo Stock Entry \(cấp phát hoặc chuyển kho\), hệ thống tự động gợi ý lô theo nguyên tắc FEFO \(First Expiry First Out\)\.

__Input__

• Item Code

• Warehouse nguồn

• Số lượng cần lấy

__Output__

• Danh sách batch gợi ý sắp xếp theo expiry\_date ASC

• Tự động fill batch vào Stock Entry items

• Cảnh báo nếu phải dùng nhiều batch để đủ SL

__Business Rules__

• FEFO: lô hạn ngắn nhất phải được gợi ý xuất trước

• Không gợi ý batch Expired, Quarantine, Recalled

• Nếu lô gần hết hạn < 7 ngày → highlight đỏ \+ cảnh báo

• User có thể override FEFO nhưng phải có lý do \+ SC\-MANAGER approve

__Acceptance Criteria__

✓ Tạo Stock Entry 20 đôi Gang tay → batch LOT\-G\-2026 \(expiry 15/6\) gợi ý trước LOT\-G\-2026B \(expiry 30/9\)

✓ Override FEFO → dialog yêu cầu lý do

✓ Batch Expired không xuất hiện trong gợi ý

__FR\-M5\-003__

__MUST__

__Cảnh báo lô sắp hết hạn__

Actor: SC\-STOREKEEPER, SC\-MANAGER

__Mô tả__

Hệ thống tự động phát hiện lô sắp hết hạn và tạo cảnh báo theo 3 mức: 30 ngày, 7 ngày, 1 ngày\.

__Input__

• Scheduler job: chạy mỗi ngày 6:00

• Tất cả batch có status Active

• Ngưỡng cảnh báo: 30 / 7 / 1 ngày \(configurable\)

__Output__

• Alert records: EXPIRY\_30D, EXPIRY\_7D, EXPIRY\_1D

• Email SC\-STOREKEEPER \+ SC\-MANAGER theo mức độ

• Dashboard M11: widget 'Lô sắp hết hạn'

• Batch status: chuyển NEAR\_EXPIRY khi < 7 ngày

__Business Rules__

• Cảnh báo không gửi trùng trong cùng 1 ngày cho cùng 1 batch

• Batch đã Consumed hoặc Returned → không cảnh báo thêm

• Ngưỡng configurable trong SupplyCore Settings

__Acceptance Criteria__

✓ Batch hết hạn trong 29 ngày → Alert EXPIRY\_30D trong Dashboard

✓ Email gửi đúng trong vòng 15 phút sau 6:00

✓ Batch Consumed trước khi hết hạn → không cảnh báo

__FR\-M5\-004__

__MUST__

__Xem Batch Ledger – lịch sử di chuyển lô__

Actor: SC\-STOREKEEPER, SC\-MANAGER

__Mô tả__

Xem toàn bộ hành trình của 1 lô: nhập kho → chuyển kho → cấp phát → bệnh nhân / khoa nào sử dụng\.

__Input__

• Batch Number \(có thể scan barcode\)

• Filter: loại movement \(nhập / chuyển / cấp phát / trả\)

__Output__

• Timeline movement: ngày, loại, kho nguồn, kho đích, SL, người thực hiện, tài liệu tham chiếu

• Nếu đã cấp phát cho BN: hiện mã BN \(ẩn tên BN, chỉ hiện mã\)

• Export PDF / Excel

__Business Rules__

• Dữ liệu từ Stock Ledger Entry chuẩn ERPNext

• Liên kết đến document gốc \(Purchase Receipt, Stock Entry, Patient Dispensing\)

__Acceptance Criteria__

✓ Nhập LOT\-G\-2026 → hiện đủ lịch sử từ nhập đến hiện tại

✓ Mỗi movement có link đến document gốc

__FR\-M5\-005__

__SHOULD__

__Xử lý lô hàng hết hạn \(hủy / trả NCC\)__

Actor: SC\-STOREKEEPER, SC\-MANAGER

__Mô tả__

Quy trình xử lý batch đã hết hạn: tạo Stock Entry loại Write\-off hoặc Purchase Return để trả NCC\.

__Input__

• Batch list có status Expired

• Quyết định: Hủy \(Write\-off\) hoặc Trả NCC

• Lý do hủy \(chọn từ danh sách\)

• Tài liệu phê duyệt của SC\-MANAGER

__Output__

• Stock Entry: Write\-off hoặc Purchase Return

• Batch status → Destroyed / Returned

• GL Entry ghi nhận mất mát tồn kho

• Audit log đầy đủ

__Business Rules__

• Hủy batch phải có lý do và SC\-MANAGER approve

• Write\-off > ngưỡng giá trị \(configurable\) cần SC\-EXECUTIVE approve

• Không thể undo hủy batch sau khi Submit

__Acceptance Criteria__

✓ Hủy batch hết hạn → Write\-off Stock Entry tạo thành công sau khi SC\-MANAGER approve

✓ Value > 10 triệu VND → yêu cầu SC\-EXECUTIVE approve

# __7\. M6 – LUÂN CHUYỂN NỘI BỘ__

__M6 – Luân chuyển nội bộ__

ERPNext: Stock Entry \(Material Transfer\), Warehouse

Custom Doctype: —

__FR\-M6\-001__

__MUST__

__Tạo phiếu chuyển kho nội bộ__

Actor: SC\-STOREKEEPER

__Mô tả__

Tạo Stock Entry loại Material Transfer để di chuyển vật tư giữa các kho nội bộ \(Kho Tổng → Kho Con → Kho Khoa Phòng\)\.

__Input__

• Warehouse nguồn

• Warehouse đích

• Vật tư, Batch \(FEFO auto\-suggest\), số lượng

• Lý do chuyển kho

• Người phê duyệt \(nếu cần\)

__Output__

• Stock Entry Material Transfer \(Draft → Submitted\)

• Cập nhật tồn kho nguồn \(\-\) và đích \(\+\)

• Bin Location cập nhật nếu có WMS

__Business Rules__

• Không thể chuyển kho nếu tồn kho nguồn không đủ

• Chuyển kho giữa cùng warehouse → validation error

• FEFO được áp dụng khi chọn batch

• Chuyển kho > ngưỡng giá trị cần SC\-MANAGER approve

__Acceptance Criteria__

✓ Chuyển 100 đôi Gang tay Kho Tổng → Kho Ngoại thành công

✓ Tồn kho nguồn cập nhật chính xác sau Submit

✓ SL chuyển > SL tồn → validation error block submit

__FR\-M6\-002__

__MUST__

__Workflow phê duyệt chuyển kho__

Actor: SC\-STOREKEEPER, SC\-MANAGER

__Mô tả__

Chuyển kho > ngưỡng giá trị hoặc chuyển từ Kho Tổng ra ngoài cần workflow phê duyệt\.

__Input__

• Stock Entry chuyển kho với tổng giá trị > ngưỡng \(configurable, default 5 triệu VND\)

__Output__

• Workflow states: Draft → Pending Approval → Approved → Submitted

• Email notification SC\-MANAGER khi có item chờ duyệt

__Business Rules__

• Ngưỡng phê duyệt configurable trong SupplyCore Settings

• Quá 48 giờ chưa duyệt → escalate email SC\-EXECUTIVE

• SC\-MANAGER chỉ duyệt được phiếu trong phạm vi warehouse mình quản lý

__Acceptance Criteria__

✓ Chuyển kho > 5 triệu → workflow Pending Approval kích hoạt

✓ SC\-MANAGER duyệt trong app → chuyển Approved tức thì

✓ Quá 48h → email SC\-EXECUTIVE tự động

__FR\-M6\-003__

__MUST__

__Báo cáo luân chuyển vật tư nội bộ__

Actor: SC\-MANAGER, SC\-ACCOUNTANT

__Mô tả__

Báo cáo tổng hợp luân chuyển vật tư nội bộ theo khoảng thời gian, kho, vật tư\.

__Input__

• Filter: khoảng thời gian, warehouse nguồn/đích, vật tư, người thực hiện

__Output__

• Bảng: ngày, vật tư, batch, SL, kho nguồn, kho đích, người thực hiện, trị giá

• Tổng giá trị luân chuyển theo kho

• Export Excel/PDF

__Business Rules__

• Dữ liệu từ Stock Entry Material Transfer đã Submitted

__Acceptance Criteria__

✓ Báo cáo tháng 4 hiện đủ tất cả chuyển kho < 5 giây

__FR\-M6\-004__

__SHOULD__

__Điều tiết vật tư giữa các kho con \(balancing\)__

Actor: SC\-MANAGER

__Mô tả__

Tính năng gợi ý điều tiết vật tư: kho nào đang thừa, kho nào đang thiếu so với ngưỡng, đề xuất lệnh chuyển\.

__Input__

• Tồn kho tất cả warehouse

• Min/Max config từng vật tư\-kho

• Lead time nội bộ

__Output__

• Danh sách gợi ý: từ kho X chuyển Y đơn vị sang kho Z

• Tổng tiết kiệm ước tính nếu thực hiện balancing

__Business Rules__

• Gợi ý dựa trên: \(tồn hiện \- max\_qty\) tại kho thừa > \(min\_qty \- tồn hiện\) tại kho thiếu

__Acceptance Criteria__

✓ Gợi ý balancing hiển thị đúng kho thừa và thiếu

✓ Tạo Stock Entry từ gợi ý → form tự điền đúng thông tin

__FR\-M6\-005__

__SHOULD__

__Yêu cầu vật tư khẩn cấp từ khoa phòng__

Actor: SC\-WARD\-STAFF, SC\-STOREKEEPER

__Mô tả__

Khoa phòng có thể tạo yêu cầu chuyển vật tư khẩn cấp trực tiếp từ tủ khoa lên Kho Con/Kho Tổng với flag URGENT\.

__Input__

• Vật tư cần, SL

• Lý do khẩn cấp

• Bác sĩ/điều dưỡng trưởng xác nhận

__Output__

• Dispensing Request với flag is\_urgent=True

• Push notification SC\-STOREKEEPER ngay lập tức

• SLA xử lý khẩn: 30 phút trong giờ hành chính

__Business Rules__

• SLA 30 phút: nếu quá → escalate SC\-MANAGER

• Flag URGENT ảnh hưởng ưu tiên trong queue của thủ kho

__Acceptance Criteria__

✓ Tạo yêu cầu URGENT → notification SC\-STOREKEEPER trong < 1 phút

✓ Quá 30 phút chưa xử lý → SC\-MANAGER nhận cảnh báo

# __8\. M7 – CẤP PHÁT & GHI NHẬN SỬ DỤNG__

__M7 – Cấp phát & Ghi nhận sử dụng__

ERPNext: Stock Entry, Stock Ledger Entry

Custom Doctype: Dispensing Request, Patient Dispensing, PD Item, BHYT Code Config

__FR\-M7\-001__

__MUST__

__Tạo Phiếu Đề nghị cấp phát vật tư \(Dispensing Request\)__

Actor: SC\-WARD\-STAFF

__Mô tả__

Điều dưỡng/nhân viên khoa tạo phiếu đề nghị cấp vật tư, gắn với bệnh nhân hoặc chỉ gắn với khoa, gửi thủ kho xử lý\.

__Input__

• Khoa/Phòng yêu cầu

• Loại đề nghị: Theo BN / Theo khoa

• Nếu theo BN: Mã BN, Tên BN \(auto\-fill từ HIS nếu có\)

• Vật tư \(search by tên hoặc mã\), SL

• Ngày cần

• Ghi chú

__Output__

• Dispensing Request document \(Draft → Submitted\)

• Notification cho SC\-STOREKEEPER

• Trạng thái tracking: Chờ xử lý / Đang chuẩn bị / Đã cấp phát

__Business Rules__

• SL đề nghị không vượt quota ngày của khoa \(nếu có thiết lập\)

• Vật tư không trong danh mục khoa → cảnh báo \(không block\)

• 1 BN 1 ngày không tạo quá 3 Dispensing Request \(soft limit\)

__Acceptance Criteria__

✓ Tạo DR thành công → notification SC\-STOREKEEPER trong < 2 phút

✓ Trạng thái DR cập nhật real\-time khi thủ kho xử lý

✓ SL > quota ngày → warning \(không block\)

__FR\-M7\-002__

__MUST__

__Tạo Phiếu Cấp phát Bệnh nhân \(Patient Dispensing\)__

Actor: SC\-STOREKEEPER

__Mô tả__

Thủ kho xử lý Dispensing Request, tạo Patient Dispensing document với thông tin chi tiết lô, BHYT, số lượng thực cấp\.

__Input__

• Dispensing Request \(link\)

• Xác nhận vật tư, batch \(FEFO\), SL thực cấp

• Mã BHYT \(auto\-suggest từ BHYT Code Config\)

• Chi phí tính toán: tổng / BHYT cover / BN thanh toán

• Chữ ký xác nhận \(nếu cần\)

__Output__

• Patient Dispensing document \(Submitted\)

• Stock Ledger Entry: xuất từ kho

• GL Entry: ghi nhận chi phí theo phân bổ BHYT

• Phiếu cấp phát in được

__Business Rules__

• Batch được chọn phải FEFO \(hạn gần nhất\)

• Mã BHYT phải tồn tại trong BHYT Code Config và trong thời hạn hiệu lực

• SL thực cấp không vượt SL đề nghị \(có thể ít hơn nếu thiếu hàng\)

• GL Entry tự tạo khi Submit: Nợ Chi phí / Có Tồn kho

__Acceptance Criteria__

✓ Cấp phát 5 đôi Gang tay → batch FEFO đúng, GL Entry tạo tự động

✓ Mã BHYT tự gợi ý theo loại BN → user chọn

✓ Cấp phát thành công → DR cập nhật trạng thái 'Đã cấp phát'

__FR\-M7\-003__

__MUST__

__Tính toán chi phí BHYT tự động__

Actor: SC\-STOREKEEPER, SC\-ACCOUNTANT

__Mô tả__

Tự động tính tỷ lệ chi phí BHYT / BN tự trả dựa trên mã BHYT, mức bảo hiểm của bệnh nhân và quy định hiện hành\.

__Input__

• Mã BHYT \(N01–N09\)

• Mức BHYT của BN: 80% / 95% / 100% \(từ thẻ BN\)

• Đơn giá vật tư

• Số lượng cấp phát

__Output__

• BHYT coverage amount

• BN self\-pay amount

• Tổng chi phí

• GL split entry

__Business Rules__

• Tất cả logic BHYT phải cấu hình được qua BHYT Code Config \(không hard\-code\)

• Quy định BHYT thay đổi → chỉ update config, không cần deploy code

• Mã BHYT hết hiệu lực → cảnh báo, không block \(vì có thể nhập thủ công\)

__Acceptance Criteria__

✓ BN BHYT 80%, đơn giá 35,000 VND × 5 đôi → BHYT trả 140,000, BN trả 35,000

✓ Thay đổi config mức BHYT → áp dụng ngay từ PD tiếp theo

__FR\-M7\-004__

__MUST__

__Báo cáo cấp phát theo khoa / BN / vật tư__

Actor: SC\-MANAGER, SC\-ACCOUNTANT

__Mô tả__

Báo cáo tổng hợp cấp phát vật tư theo khoa, bệnh nhân, vật tư, khoảng thời gian\.

__Input__

• Filter: khoảng thời gian, khoa, loại vật tư, mã BHYT

• Nhóm theo: khoa / vật tư / ngày / BN

__Output__

• Bảng: SL cấp phát, trị giá, BHYT cover, BN tự trả

• Tổng chi phí theo khoa \(cho phân bổ nội bộ\)

• Export Excel \(cho kế toán\) / PDF \(cho khoa\)

__Business Rules__

• Dữ liệu từ Patient Dispensing đã Submitted

• Mã BN trong báo cáo: ẩn tên, chỉ hiện mã \(bảo mật\)

__Acceptance Criteria__

✓ Báo cáo cấp phát tháng 4 Khoa Ngoại < 5 giây

✓ Export Excel đúng format kế toán viện phí

__FR\-M7\-005__

__SHOULD__

__Cấp phát vật tư không gắn BN \(theo khoa\)__

Actor: SC\-STOREKEEPER, SC\-WARD\-STAFF

__Mô tả__

Hỗ trợ cấp phát vật tư tiêu hao chung cho khoa \(không gắn BN cụ thể\): vật tư vệ sinh, bảo hộ lao động, văn phòng phẩm y tế\.

__Input__

• Khoa/Phòng

• Vật tư, SL

• Mục đích sử dụng chung \(chọn từ danh sách\)

__Output__

• Stock Entry Material Issue gắn Cost Center của khoa

• GL Entry: Nợ Chi phí khoa / Có Tồn kho

__Business Rules__

• Cấp phát không\-BN không được dùng mã BHYT

• SL cấp phát không\-BN theo dõi riêng với quota tháng của khoa

__Acceptance Criteria__

✓ Cấp phát vật tư vệ sinh Khoa Ngoại → Stock Entry \+ GL Entry đúng Cost Center

# __9\. M8 – KẾ TOÁN & THANH TOÁN__

__M8 – Kế toán & Thanh toán__

ERPNext: Purchase Invoice, Payment Entry, GL Entry, Journal Entry \(ERPNext standard\)

Custom Doctype: —

__FR\-M8\-001__

__MUST__

__3\-Way Match: Purchase Invoice vs PO vs Receipt__

Actor: SC\-ACCOUNTANT

__Mô tả__

Khi tạo Purchase Invoice, hệ thống tự động đối chiếu 3 chiều: Invoice với Purchase Order và Purchase Receipt, highlight chênh lệch\.

__Input__

• Purchase Invoice \(tạo thủ công hoặc từ PO\)

• Chọn PO tham chiếu và Receipt tương ứng

__Output__

• 3\-way match report: bảng so sánh từng dòng Invoice vs PO vs Receipt

• Flag chênh lệch: về SL và đơn giá

• Trạng thái: MATCH / QUANTITY\_MISMATCH / PRICE\_MISMATCH / MISSING

__Business Rules__

• Tolerance SL: ±2% \(configurable\)

• Tolerance giá: 0% \(giá phải đúng theo FC\)

• Invoice SL > Receipt SL → QUANTITY\_MISMATCH, block Submit nếu > tolerance

• Invoice giá > giá FC → PRICE\_MISMATCH, block Submit

__Acceptance Criteria__

✓ Invoice SL khớp Receipt → MATCH → cho phép Submit

✓ Invoice SL lệch 1% → warning nhưng vẫn Submit được

✓ Invoice giá > giá FC → block Submit với thông báo rõ

__FR\-M8\-002__

__MUST__

__Tạo Payment Entry và quản lý công nợ NCC__

Actor: SC\-ACCOUNTANT

__Mô tả__

Tạo thanh toán cho NCC từ Purchase Invoice đã duyệt, theo dõi công nợ và lịch sử thanh toán\.

__Input__

• Purchase Invoice \(Submitted, Outstanding > 0\)

• Số tiền thanh toán

• Ngày thanh toán

• Tài khoản thanh toán \(Bank/Cash\)

• Số tham chiếu ngân hàng

• File đính kèm chứng từ

__Output__

• Payment Entry document \(Submitted\)

• GL Entry: Nợ Phải trả NCC / Có Tiền gửi ngân hàng

• Outstanding amount cập nhật trên Invoice

• Payment history cho NCC

__Business Rules__

• Số tiền thanh toán không vượt Outstanding Amount

• Thanh toán đúng hạn theo điều khoản HĐK \(late payment alert nếu trễ\)

• Số tham chiếu ngân hàng phải duy nhất \(tránh trùng lặp\)

__Acceptance Criteria__

✓ Thanh toán 50 triệu cho NCC → GL Entry đúng, Outstanding giảm tương ứng

✓ Số tham chiếu ngân hàng trùng → validation error

✓ Thanh toán sau hạn → cảnh báo nhưng không block

__FR\-M8\-003__

__MUST__

__Báo cáo công nợ và lão hóa \(Aging Report\)__

Actor: SC\-ACCOUNTANT, SC\-MANAGER

__Mô tả__

Báo cáo công nợ NCC theo tuổi nợ: < 30 ngày, 30–60, 60–90, > 90 ngày\.

__Input__

• Ngày lập báo cáo

• Filter: NCC, nhóm NCC, khoảng thời gian

__Output__

• Aging report: NCC → tổng nợ → phân loại theo tuổi → overdue flag

• Cảnh báo NCC overdue > 60 ngày

• Export Excel/PDF

__Business Rules__

• Tính từ ngày Invoice → Payment Due Date \(theo điều khoản HĐK\)

• Overdue: ngày hôm nay > Payment Due Date

__Acceptance Criteria__

✓ Aging Report ngày hôm nay load đúng phân loại tuổi nợ < 5 giây

✓ NCC overdue > 60 ngày hiển thị màu đỏ

__FR\-M8\-004__

__MUST__

__Tổng hợp chi phí vật tư theo kỳ và khoa__

Actor: SC\-ACCOUNTANT, SC\-MANAGER

__Mô tả__

Báo cáo chi phí vật tư tổng hợp theo tháng/quý, phân loại theo khoa/phòng và loại vật tư, so sánh với ngân sách\.

__Input__

• Kỳ báo cáo: tháng / quý

• Nhóm theo: khoa / loại vật tư / mã BHYT

• So sánh với ngân sách \(nếu có\)

__Output__

• Bảng chi phí: khoa → tổng chi phí → BHYT cover → BN tự trả → bệnh viện chịu

• % sử dụng so ngân sách theo khoa

• Biểu đồ xu hướng 6 tháng

• Export PDF cho họp BGĐ

__Business Rules__

• Dữ liệu từ GL Entry liên quan vật tư

• Khoa không có ngân sách → hiện N/A cho % ngân sách

__Acceptance Criteria__

✓ Báo cáo chi phí Q2/2026 → số liệu khớp GL trong < 5 giây

✓ Export PDF đúng format trình BGĐ

__FR\-M8\-005__

__SHOULD__

__Cảnh báo Invoice đến hạn thanh toán__

Actor: SC\-ACCOUNTANT

__Mô tả__

Cảnh báo proactive khi Invoice sắp đến hạn thanh toán \(trước 7 ngày và trước 1 ngày\)\.

__Input__

• Scheduler hàng ngày 8:00

• Payment Due Date của tất cả Outstanding Invoice

__Output__

• Alert PAYMENT\_DUE\_7D và PAYMENT\_DUE\_1D

• Email SC\-ACCOUNTANT

• Dashboard widget công nợ M8

__Business Rules__

• Không cảnh báo Invoice đã thanh toán đầy đủ

• Cảnh báo chỉ trong giờ hành chính \(7:00–17:00\)

__Acceptance Criteria__

✓ Invoice đến hạn 6 ngày nữa → alert PAYMENT\_DUE\_7D trong Dashboard

✓ Email SC\-ACCOUNTANT trong vòng 15 phút sau 8:00

# __10\. M9 – KIỂM KÊ & ĐỐI SOÁT__

__M9 – Kiểm kê & Đối soát__

ERPNext: Stock Reconciliation \(ERPNext standard\)

Custom Doctype: —

__FR\-M9\-001__

__MUST__

__Tạo phiếu kiểm kê định kỳ__

Actor: SC\-STOREKEEPER

__Mô tả__

Tạo Stock Reconciliation để so sánh tồn kho hệ thống với số đếm thực tế, ghi nhận chênh lệch\.

__Input__

• Warehouse cần kiểm kê

• Ngày kiểm kê

• Phương pháp: Kiểm kê toàn bộ / Kiểm kê theo nhóm vật tư

• Số đếm thực tế từng vật tư\-batch

__Output__

• Stock Reconciliation document với từng dòng: hệ thống vs thực tế vs chênh lệch

• Tổng chênh lệch giá trị

• Trạng thái: Draft → Pending Approval → Submitted

__Business Rules__

• Không thể submit Stock Reconciliation khi có Stock Entry Draft liên quan đến kho đó

• Chênh lệch > ±2% hoặc > 1 triệu VND cần SC\-MANAGER approve

• Kiểm kê toàn bộ: KHÔNG thực hiện trong giờ cao điểm \(7:00–16:00\)

__Acceptance Criteria__

✓ Kiểm kê Kho Tổng: tạo thành công với đủ dòng vật tư

✓ Chênh lệch 5% → Pending Approval, email SC\-MANAGER

✓ Submit sau khi approve → Stock Ledger cập nhật

__FR\-M9\-002__

__MUST__

__PDA hỗ trợ đếm kiểm kê ngoại tuyến__

Actor: SC\-STOREKEEPER

__Mô tả__

Dùng PDA để scan và đếm vật tư trong quá trình kiểm kê, lưu kết quả offline và sync khi xong\.

__Input__

• Tải danh sách vật tư\-batch từ Stock Reconciliation draft

• Scan barcode hoặc nhập thủ công số đếm thực tế

• Lưu local, sync khi kết nối

__Output__

• Kết quả đếm upload vào Stock Reconciliation draft

• Báo cáo tiến độ: đã đếm X/Y dòng

__Business Rules__

• Đồng bộ 2 người đếm cùng 1 kho: lưu count\_1 và count\_2, tính trung bình

__Acceptance Criteria__

✓ PDA đếm 200 items offline → sync thành công vào Stock Reconciliation

✓ 2 người đếm khác nhau → hệ thống ghi 2 kết quả và hiện chênh lệch

__FR\-M9\-003__

__MUST__

__Báo cáo đối soát tồn kho và phân tích chênh lệch__

Actor: SC\-MANAGER, SC\-ACCOUNTANT

__Mô tả__

Báo cáo tổng hợp kết quả kiểm kê: chênh lệch theo vật tư, nguyên nhân, giá trị và xu hướng qua các kỳ\.

__Input__

• Kỳ kiểm kê \(tháng/quý\)

• Kho, nhóm vật tư

__Output__

• Bảng chênh lệch: vật tư → SL hệ thống vs thực tế → chênh lệch SL và giá trị

• Phân loại nguyên nhân \(chọn từ danh sách\)

• So sánh accuracy qua 6 kỳ gần nhất

• Export PDF cho kiểm toán

__Business Rules__

• Inventory Accuracy = \(1 \- Tổng|chênh lệch|/Tổng tồn hệ thống\) × 100%

• Target: Inventory Accuracy ≥ 98%

__Acceptance Criteria__

✓ Báo cáo kiểm kê Q1/2026 load < 5 giây

✓ Inventory Accuracy tính đúng từ số liệu chênh lệch

__FR\-M9\-004__

__SHOULD__

__Quy trình phê duyệt điều chỉnh tồn kho__

Actor: SC\-MANAGER, SC\-STOREKEEPER

__Mô tả__

Chênh lệch kiểm kê cần được phân tích nguyên nhân và phê duyệt trước khi điều chỉnh vào hệ thống\.

__Input__

• Stock Reconciliation với chênh lệch

• Phân tích nguyên nhân từng dòng chênh lệch

• SC\-MANAGER xác nhận điều chỉnh

__Output__

• Reconciliation Approval workflow

• Điều chỉnh tồn kho chỉ khi đã approve

• GL Entry ghi nhận chênh lệch giá trị

__Business Rules__

• Nguyên nhân từ danh sách chuẩn: Hư hỏng / Mất / Nhầm lẫn nhập liệu / Hết hạn / Khác

• Điều chỉnh giá trị > 5 triệu cần SC\-EXECUTIVE approve

__Acceptance Criteria__

✓ SC\-MANAGER approve → Stock Ledger cập nhật, GL tự tạo

✓ Điều chỉnh > 5 triệu → escalate SC\-EXECUTIVE

__FR\-M9\-005__

__SHOULD__

__Kiểm kê đột xuất theo nhóm vật tư hoặc lô__

Actor: SC\-MANAGER

__Mô tả__

Tạo kiểm kê đột xuất cho một nhóm vật tư cụ thể \(không kiểm kê toàn kho\) khi có nghi ngờ hoặc sự cố\.

__Input__

• Nhóm vật tư hoặc danh sách lô cụ thể

• Lý do kiểm kê đột xuất

• Người thực hiện và giám sát

__Output__

• Spot\-check Stock Reconciliation với phạm vi giới hạn

• Kết quả so sánh nhanh

• Audit log ghi rõ lý do

__Business Rules__

• Kiểm kê đột xuất không ảnh hưởng đến kiểm kê định kỳ sắp tới

• Kết quả cập nhật Stock Ledger ngay sau approve

__Acceptance Criteria__

✓ Tạo kiểm kê đột xuất Gang tay sau khi phát hiện nghi ngờ → xử lý trong < 2 giờ

# __11\. M10 – TRUY XUẤT & ĐIỀU TRA__

__M10 – Truy xuất & Điều tra__

ERPNext: Stock Ledger Entry \(audit trail built\-in\)

Custom Doctype: Recall Notice

__FR\-M10\-001__

__MUST__

__Truy xuất nguồn gốc lô hàng toàn trình__

Actor: SC\-MANAGER, SC\-STOREKEEPER

__Mô tả__

Từ mã lô, tìm toàn bộ vòng đời: NCC → PO → Receipt → kho → cấp phát → bệnh nhân \(nếu có\)\.

__Input__

• Batch Number \(nhập thủ công hoặc scan\)

__Output__

• Supply chain trace timeline: NCC → PO → Receipt → Bin Location → Stock Entries → Dispensing

• Mã BN đã nhận \(ẩn tên\)

• Tổng SL nhập / xuất / tồn hiện tại

• Export PDF Trace Report

__Business Rules__

• Trace phải hoàn thành trong < 5 giây cho bất kỳ batch nào

• Dữ liệu lịch sử không bao giờ bị xóa \(soft delete only\)

• Accessible bởi SC\-MANAGER, SC\-STOREKEEPER, SC\-SYSADMIN

__Acceptance Criteria__

✓ Nhập LOT\-G\-2026 → hiện đầy đủ timeline 100% chính xác trong < 5 giây

✓ Export PDF với đầy đủ thông tin trace

__FR\-M10\-002__

__MUST__

__Phát hành Recall Notice cho lô hàng cần thu hồi__

Actor: SC\-MANAGER

__Mô tả__

Khi có thông báo thu hồi từ nhà sản xuất hoặc Bộ Y tế, tạo Recall Notice cho tất cả lô liên quan và xử lý tồn kho\.

__Input__

• Recall source: Bộ Y tế / NSX / Nội bộ

• Batch list hoặc tiêu chí \(NSX \+ Item \+ date range\)

• Mức độ recall: Class I \(nguy hiểm\) / II / III

• Hành động: Dừng cấp phát / Thu hồi từ khoa / Trả NCC / Hủy

__Output__

• Recall Notice document

• Tất cả batch liên quan → trạng thái Recalled

• Block toàn bộ transaction mới với batch bị recall

• Thông báo tất cả khoa có batch đó

• Report: batch nào đã dùng cho BN nào

__Business Rules__

• Class I Recall: Block NGAY LẬP TỨC, không cần approve thêm

• Class II/III: SC\-MANAGER approve, block trong vòng 1 giờ

• Recall không thể undo \(chỉ Close với lý do\)

• Thông báo khoa có batch recall trong < 5 phút

__Acceptance Criteria__

✓ Tạo Class I Recall → tất cả batch bị block ngay lập tức

✓ Email/notification gửi tất cả khoa liên quan < 5 phút

✓ Báo cáo BN đã nhận batch bị recall export thành công

__FR\-M10\-003__

__MUST__

__Audit Trail cho mọi thay đổi dữ liệu__

Actor: SC\-SYSADMIN, SC\-MANAGER

__Mô tả__

Ghi lại toàn bộ thay đổi trên các Doctype nhạy cảm: ai thay đổi gì, lúc nào, giá trị trước/sau\.

__Input__

• Frappe built\-in document versioning

• Custom audit cho: Patient Dispensing, BHYT Code Config, Framework Contract, Stock Entry manual

__Output__

• Audit log table: user, doctype, docname, field, old\_value, new\_value, timestamp

• Export audit log cho kỳ kiểm toán

• Không thể xóa audit log \(immutable\)

__Business Rules__

• Audit log immutable: không SC nào có quyền xóa

• Retention: 7 năm \(theo quy định bệnh viện\)

• Performance: audit log write không ảnh hưởng transaction chính > 100ms

__Acceptance Criteria__

✓ Sửa đơn giá FC → audit log ghi đúng giá trước/sau, user, thời gian

✓ Export audit log 1 tháng < 10 giây

__FR\-M10\-004__

__SHOULD__

__Báo cáo hoạt động người dùng__

Actor: SC\-SYSADMIN

__Mô tả__

Báo cáo hoạt động đăng nhập và thao tác của từng người dùng: login history, document actions theo thời gian\.

__Input__

• Khoảng thời gian

• Filter: user, role, action type

__Output__

• Login history: user, IP, thời gian, thành công/thất bại

• Document action log: create/edit/submit/cancel

• Bất thường: nhiều login fail, login ngoài giờ

__Business Rules__

• Access log chỉ SC\-SYSADMIN xem được

• Dữ liệu không thể sửa

__Acceptance Criteria__

✓ Báo cáo login 7 ngày gần nhất load < 5 giây

✓ Phát hiện 5\+ login fail → flag trong report

__FR\-M10\-005__

__COULD__

__Điều tra sự cố \(Incident Investigation\)__

Actor: SC\-MANAGER, SC\-SYSADMIN

__Mô tả__

Công cụ điều tra sự cố liên quan vật tư: tìm kiếm cross\-reference giữa batch, BN, thời gian, khoa để xác định phạm vi ảnh hưởng\.

__Input__

• Tiêu chí điều tra: batch / thời gian / vật tư / khoa / BN \(mã\)

• Xuất phát điểm: Batch ID hoặc Patient ID

__Output__

• Danh sách tất cả transactions liên quan

• Bản đồ ảnh hưởng: batch nào, khoa nào, BN nào

• Risk assessment: số BN có thể ảnh hưởng

__Business Rules__

• Tìm kiếm phải trả về kết quả trong < 10 giây dù data > 1 triệu records

• Kết quả export PDF ngay lập tức

__Acceptance Criteria__

✓ Điều tra batch LOT\-G\-2026 → report đầy đủ phạm vi ảnh hưởng < 10 giây

# __12\. M11 – DASHBOARD & CẢNH BÁO ĐIỀU HÀNH__

__M11 – Dashboard & Cảnh báo điều hành__

ERPNext: ERPNext Dashboard, Report Builder \(standard\)

Custom Doctype: SupplyCore Alert, SupplyCore Settings \(alert config\)

__FR\-M11\-001__

__MUST__

__Dashboard KPI điều hành thời gian thực__

Actor: SC\-EXECUTIVE, SC\-MANAGER

__Mô tả__

Dashboard tổng hợp KPI chiến lược: tồn kho, chi phí, cấp phát, QC, cảnh báo – cập nhật real\-time\.

__Input__

• Role của user \(Executive/Manager\): hiện widget khác nhau

__Output__

• KPI Widgets: Tổng tồn kho \(value\), Số cảnh báo tồn kho thấp, Lô sắp hết hạn, Chi phí tháng vs ngân sách, Tỷ lệ QC đạt, PO chờ duyệt

• Biểu đồ xu hướng 6 tháng \(chi phí, tồn kho\)

• Refresh tự động mỗi 5 phút hoặc manual

__Business Rules__

• Dashboard khác nhau theo role: SC\-EXECUTIVE thấy KPI cấp cao; SC\-MANAGER thấy KPI vận hành

• Dữ liệu KPI tính từ database trực tiếp, không cache quá 5 phút

• KPI threshold configurable trong SupplyCore Settings

__Acceptance Criteria__

✓ Dashboard tải đầy đủ trong < 5 giây

✓ KPI refresh tự động mỗi 5 phút mà không cần reload trang

✓ SC\-EXECUTIVE và SC\-MANAGER thấy widget khác nhau

__FR\-M11\-002__

__MUST__

__Alert Engine – Phân loại và quản lý cảnh báo__

Actor: SC\-STOREKEEPER, SC\-MANAGER, SC\-EXECUTIVE

__Mô tả__

Hệ thống tạo, phân loại và quản lý tất cả cảnh báo hoạt động: tồn kho thấp, hạn hết, PO quá hạn, chênh lệch kiểm kê\.

__Input__

• Alert records từ tất cả modules

• Alert categories: STOCK\_LOW, EXPIRY, PO\_OVERDUE, QC\_FAIL, PAYMENT\_DUE, RECALL, DISCREPANCY

__Output__

• Alert Center: danh sách cảnh báo với level \(CRITICAL/HIGH/MEDIUM/LOW\)

• Filter theo loại, level, trạng thái

• Mark as Read / Acknowledge / Resolve với note

• Counter badge trên menu theo role

__Business Rules__

• CRITICAL alert: gửi email ngay, hiện popup khi user đăng nhập

• HIGH: gửi email, hiện trong Alert Center

• MEDIUM: chỉ Alert Center

• LOW: chỉ Alert Center

• Cùng loại alert cho cùng đối tượng: tối đa 1 lần/24h

__Acceptance Criteria__

✓ Alert Center hiện đầy đủ cảnh báo phân loại đúng level

✓ CRITICAL alert → email trong < 5 phút

✓ Acknowledge alert → không gửi email lại trong 24h

__FR\-M11\-003__

__MUST__

__Scheduled Reports – Báo cáo định kỳ tự động__

Actor: SC\-MANAGER, SC\-EXECUTIVE, SC\-ACCOUNTANT

__Mô tả__

Hệ thống tự động tạo và gửi báo cáo định kỳ theo lịch đã cấu hình\.

__Input__

• Cấu hình trong SupplyCore Settings: report type, recipients, schedule, format

__Output__

• PDF/Excel file gửi qua email đúng lịch

• Log ghi nhận đã gửi / lỗi

• Lịch mặc định: Tuần \(thứ 2 8h\), Tháng \(ngày 1\), Quý \(ngày đầu tháng đầu quý\)

__Business Rules__

• Report fail: retry 3 lần, sau đó alert SC\-SYSADMIN

• Report gửi không quá 60 phút sau giờ đã lên lịch

• Format PDF: dùng dpi 150 minimum cho bảng số liệu

__Acceptance Criteria__

✓ Báo cáo tuần gửi thứ 2 8:00 → email đến đúng 3 địa chỉ cấu hình

✓ Report fail → retry thành công lần 2

✓ Log ghi nhận thời gian gửi và status

__FR\-M11\-004__

__SHOULD__

__Cấu hình ngưỡng cảnh báo \(Alert Configuration\)__

Actor: SC\-SYSADMIN, SC\-MANAGER

__Mô tả__

Cho phép cấu hình linh hoạt ngưỡng tất cả cảnh báo qua SupplyCore Settings mà không cần deploy code\.

__Input__

• SupplyCore Settings doctype

• Ngưỡng: expiry\_warning\_days, low\_stock\_threshold\_pct, qc\_pass\_rate\_min, payment\_overdue\_days, reconciliation\_tolerance\_pct

__Output__

• Settings lưu vào database

• Apply ngay lập tức cho các lần scheduler chạy tiếp theo

• Audit log ghi lại thay đổi config

__Business Rules__

• Config thay đổi không yêu cầu restart service

• Chỉ SC\-SYSADMIN được sửa Settings

• Giá trị hợp lệ: expiry\_days 1–365, threshold\_pct 1–100

__Acceptance Criteria__

✓ Sửa expiry\_warning\_days từ 30 sang 14 → áp dụng ngay scheduler lần sau

✓ Config không hợp lệ → validation error, không lưu

__FR\-M11\-005__

__SHOULD__

__Drill\-down từ KPI Dashboard đến chi tiết__

Actor: SC\-MANAGER, SC\-EXECUTIVE

__Mô tả__

Từ KPI widget, click để drill\-down xem danh sách chi tiết các records tạo nên KPI đó\.

__Input__

• Click trên KPI widget

__Output__

• Popup hoặc trang danh sách với filter tự động áp dụng theo KPI

• Có thể export từ drill\-down view

__Business Rules__

• Drill\-down phải tải < 3 giây

• Filter áp dụng tự động: không cần user chọn lại

__Acceptance Criteria__

✓ Click KPI 'Cảnh báo tồn thấp: 8 mặt hàng' → danh sách 8 mặt hàng hiện ngay

✓ Export từ drill\-down → đúng dữ liệu đang xem

# __13\. MA TRẬN TRACEABILITY__

Ma trận liên kết FR với Use Case và Module tương ứng\.

__FR ID__

__Priority__

__Use Case__

__Module__

__Tên yêu cầu ngắn__

__FR\-M1\-001__

__MUST__

UC\-01

M1

Tạo & quản lý Hợp đồng Khung

__FR\-M1\-002__

__MUST__

UC\-02

M1

Tạo Release Order từ FC

__FR\-M2\-001__

__MUST__

UC\-05

M2

Cấu hình ngưỡng tồn kho

__FR\-M2\-002__

__MUST__

UC\-06

M2

Auto\-suggest PO khi đạt Reorder Point

__FR\-M3\-001__

__MUST__

UC\-09

M3

Tạo Purchase Receipt \+ QC cơ bản

__FR\-M3\-002__

__MUST__

UC\-09

M3

Scan barcode auto\-fill Receipt

__FR\-M4\-001__

__MUST__

UC\-12

M4

Quản lý Bin Location

__FR\-M4\-002__

__MUST__

UC\-13

M4

PDA scan putaway/pick

__FR\-M4\-003__

__MUST__

UC\-13

M4

PDA Offline Mode \+ sync

__FR\-M5\-001__

__MUST__

UC\-15

M5

Batch tracking toàn vòng đời

__FR\-M5\-002__

__MUST__

UC\-16

M5

FEFO auto\-selection

__FR\-M5\-003__

__MUST__

UC\-17

M5

Cảnh báo lô sắp hết hạn

__FR\-M6\-001__

__MUST__

UC\-19

M6

Phiếu chuyển kho nội bộ

__FR\-M7\-001__

__MUST__

UC\-22

M7

Dispensing Request từ khoa

__FR\-M7\-002__

__MUST__

UC\-23

M7

Patient Dispensing \+ BHYT

__FR\-M7\-003__

__MUST__

UC\-24

M7

Tính chi phí BHYT tự động

__FR\-M8\-001__

__MUST__

UC\-26

M8

3\-Way Match Invoice

__FR\-M8\-002__

__MUST__

UC\-27

M8

Payment Entry \+ công nợ NCC

__FR\-M9\-001__

__MUST__

UC\-30

M9

Kiểm kê định kỳ

__FR\-M10\-001__

__MUST__

UC\-33

M10

Truy xuất nguồn gốc lô

__FR\-M10\-002__

__MUST__

UC\-34

M10

Recall Notice

__FR\-M10\-003__

__MUST__

UC\-35

M10

Audit Trail

__FR\-M11\-001__

__MUST__

UC\-36

M11

Dashboard KPI real\-time

__FR\-M11\-002__

__MUST__

UC\-37

M11

Alert Engine

__FRS SupplyCore v1\.0 – 55 Functional Requirements__

MUST: 38 | SHOULD: 15 | COULD: 2 | Phase 4 – Document 16/20

