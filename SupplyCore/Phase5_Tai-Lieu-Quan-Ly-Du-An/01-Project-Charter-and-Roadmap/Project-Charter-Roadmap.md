__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung ứng Vật tư Y tế Bệnh viện

__PROJECT CHARTER & ROADMAP__

__Phiên bản__

1\.0 – Bản phát hành ban đầu

__Ngày lập__

05/2026

__Đơn vị thực hiện__

MedCons Vietnam

__Trạng thái__

Dự thảo

__Nền tảng__

Frappe Framework v15 \+ ERPNext v15 \(custom app\)

# __1\. Tổng quan Dự án__

## __1\.1 Mục tiêu__

SupplyCore là hệ thống quản lý chuỗi cung ứng vật tư tiêu hao chuyên dụng cho bệnh viện, được xây dựng trên nền tảng Frappe Framework v15 và ERPNext v15 dưới dạng custom app độc lập\. Hệ thống nhằm số hóa và tối ưu hóa toàn bộ vòng đời vật tư từ lập kế hoạch, đặt hàng, tiếp nhận, lưu kho, cấp phát đến thanh toán và báo cáo\.

## __1\.2 Phạm vi Giai đoạn 1__

Giai đoạn 1 bao gồm 11 mô\-đun chức năng chính:

- M1: Hợp đồng & Nhà cung cấp – Quản lý hợp đồng khung, thông tin NCC
- M2: Kế hoạch tồn kho & Gọi hàng – Lập kế hoạch, tạo Release Order
- M3: Tiếp nhận & Kiểm tra chất lượng – QC lô hàng nhập
- M4: WMS & PDA – Quản lý vị trí kho, hỗ trợ thiết bị PDA
- M5: Lô, Hạn dùng & FEFO – Truy xuất theo lô, quản lý FEFO
- M6: Luân chuyển nội bộ – Điều chuyển giữa các kho
- M7: Cấp phát & Ghi nhận sử dụng – Cấp phát theo khoa/bệnh nhân
- M8: Kế toán & Thanh toán – Tích hợp kế toán ERPNext
- M9: Kiểm kê & Đối soát – Kiểm kê định kỳ
- M10: Truy xuất & Điều tra – Truy vết lô hàng
- M11: Dashboard & Cảnh báo điều hành – Báo cáo, KPI

## __1\.3 Ngoài phạm vi Giai đoạn 1__

- Quản lý dược phẩm/thuốc
- Tài sản cố định \(trang thiết bị y tế\)
- Module đấu thầu tập trung
- Tích hợp cổng thanh toán điện tử
- Kết nối trực tiếp HIS/EMR/LIS \(chỉ thiết kế API sẵn sàng\)

## __1\.4 Các bên liên quan__

__Vai trò__

__Đại diện / Bộ phận__

__Trách nhiệm chính__

Project Sponsor

Ban Giám đốc Bệnh viện

Phê duyệt ngân sách, ưu tiên chiến lược

Project Manager

MedCons Vietnam

Quản lý tiến độ, rủi ro, tài nguyên

Business Analyst

Nhóm BA / MedCons

Thu thập yêu cầu, phân tích nghiệp vụ

Technical Lead

Nhóm Dev / MedCons

Thiết kế kỹ thuật, code review

Trưởng Khoa Vật tư

Bệnh viện – Phòng VTYT

Xác nhận quy trình nghiệp vụ

Kế toán trưởng

Bệnh viện – Phòng Tài chính

Xác nhận quy trình thanh toán, BHYT

IT Hospital

Bệnh viện – Phòng CNTT

Hạ tầng, bảo mật, tích hợp HIS

# __2\. Timeline & Milestones__

## __2\.1 Tổng quan Timeline__

Dự án SupplyCore giai đoạn 1 được dự kiến hoàn thành trong 12 tháng, chia thành 4 giai đoạn thực hiện chính\.

__Giai đoạn__

__Tên giai đoạn__

__Thời gian__

__Thời lượng__

__Trạng thái__

1

Phân tích & Thiết kế

T1 – T3/2026

3 tháng

Đang thực hiện

2

Phát triển Core Modules

T4 – T7/2026

4 tháng

Chưa bắt đầu

3

Testing & UAT

T8 – T9/2026

2 tháng

Chưa bắt đầu

4

Go\-Live & Hypercare

T10 – T12/2026

3 tháng

Chưa bắt đầu

## __2\.2 Milestones chính__

__MS\#__

__Milestone__

__Ngày dự kiến__

__Deliverable__

__Người phê duyệt__

M1

Hoàn thành tài liệu BRD & URS

31/01/2026

BRD, URS đã ký

Project Sponsor

M2

Hoàn thành thiết kế hệ thống

31/03/2026

System Design Package

Technical Lead

M3

Cài đặt môi trường Dev & Staging

15/04/2026

Env Setup Report

IT Hospital

M4

Hoàn thành Module M1–M3 \(Core\)

31/05/2026

Sprint report \+ Demo

PM \+ BA

M5

Hoàn thành Module M4–M7

31/07/2026

Sprint report \+ Demo

PM \+ BA

M6

Hoàn thành UAT lần 1

31/08/2026

UAT Sign\-off Sheet

Khoa VTYT

M7

Hoàn thành UAT lần 2 & Performance Test

30/09/2026

Test Report

Project Sponsor

M8

Go\-Live chính thức

01/10/2026

Go\-Live Checklist

Ban Giám đốc

M9

Kết thúc Hypercare – Bàn giao vận hành

31/12/2026

Handover Report

Project Sponsor

## __2\.3 Module Delivery Plan__

__Module__

__Tên Module__

__Sprint__

__Bắt đầu__

__Kết thúc__

M1

Hợp đồng & Nhà cung cấp

Sprint 1–2

01/04/2026

30/04/2026

M2

Kế hoạch tồn kho & Gọi hàng

Sprint 2–3

15/04/2026

15/05/2026

M3

Tiếp nhận & Kiểm tra chất lượng

Sprint 3–4

01/05/2026

31/05/2026

M4

WMS & PDA

Sprint 4–5

01/06/2026

30/06/2026

M5

Lô, Hạn dùng & FEFO

Sprint 5–6

15/06/2026

15/07/2026

M6

Luân chuyển nội bộ

Sprint 6

01/07/2026

31/07/2026

M7

Cấp phát & Ghi nhận sử dụng

Sprint 7

01/07/2026

31/07/2026

M8

Kế toán & Thanh toán

Sprint 7–8

15/07/2026

15/08/2026

M9

Kiểm kê & Đối soát

Sprint 8

01/08/2026

31/08/2026

M10

Truy xuất & Điều tra

Sprint 8–9

15/08/2026

15/09/2026

M11

Dashboard & Cảnh báo điều hành

Sprint 9

01/09/2026

30/09/2026

# __3\. Ngân sách Dự án__

## __3\.1 Ước tính Chi phí__

__Hạng mục__

__Ước tính \(VNĐ\)__

__% Ngân sách__

__Ghi chú__

Phân tích & Thiết kế hệ thống

150\.000\.000

10%

BA, Architect

Phát triển phần mềm

750\.000\.000

50%

Dev team 6 người × 8 tháng

Kiểm thử & UAT

150\.000\.000

10%

QA team \+ end\-user testing

Hạ tầng & License

120\.000\.000

8%

Server, ERPNext hosting

Đào tạo & Go\-live

90\.000\.000

6%

Training, hypercare support

Quản lý dự án

90\.000\.000

6%

PM, documentation

Dự phòng rủi ro \(10%\)

150\.000\.000

10%

Contingency fund

__TỔNG CỘNG__

__1\.500\.000\.000__

__100%__

__~1,5 tỷ VNĐ__

# __4\. Tổ chức Dự án & Phân quyền__

## __4\.1 Cơ cấu Tổ chức__

Dự án áp dụng mô hình tổ chức theo ma trận \(Matrix Organization\), trong đó Project Manager chịu trách nhiệm điều phối tổng thể, các Tech Lead đảm nhận từng nhóm module chuyên biệt\.

## __4\.2 Ma trận RACI__

__Hoạt động__

__Sponsor__

__PM__

__BA__

__Dev Lead__

__Hospital IT__

Phê duyệt Project Charter

A

R

C

I

I

Thu thập yêu cầu nghiệp vụ

I

A

R

C

C

Thiết kế kiến trúc hệ thống

I

A

C

R

C

Phát triển & Unit Test

I

A

C

R

I

Kiểm thử UAT

I

A

R

C

R

Phê duyệt Go\-Live

A

R

C

C

R

Quản lý thay đổi yêu cầu

A

R

R

C

I

Chú thích: R = Responsible \(Thực hiện\), A = Accountable \(Chịu trách nhiệm\), C = Consulted \(Tham vấn\), I = Informed \(Được thông báo\)

# __5\. Giả định & Ràng buộc__

## __5\.1 Giả định__

- Bệnh viện đã có hạ tầng mạng nội bộ ổn định \(LAN/WiFi trong khu vực kho\)
- ERPNext v15 sẽ được cài đặt trên server riêng của bệnh viện hoặc VPS
- Người dùng cuối có khả năng sử dụng máy tính/tablet ở mức cơ bản
- Dữ liệu danh mục vật tư hiện tại được cung cấp đầy đủ để migration
- Quy trình nghiệp vụ hiện tại được tài liệu hóa và xác nhận bởi stakeholder
- Nguồn lực phía bệnh viện tham gia UAT ít nhất 20% thời gian trong giai đoạn test

## __5\.2 Ràng buộc__

- Ngân sách tối đa: 1\.500\.000\.000 VNĐ
- Thời gian Go\-Live: Không muộn hơn 01/10/2026
- Nền tảng bắt buộc: Frappe/ERPNext v15 – không thay đổi tech stack
- Không tái phát triển các tính năng đã có trong ERPNext chuẩn
- Tuân thủ quy định bảo mật thông tin y tế \(Thông tư 46/2018/TT\-BYT\)

# __6\. Tiêu chí Thành công__

__\#__

__Tiêu chí__

__Cách đo lường__

1

Hệ thống hoạt động ổn định sau Go\-Live

Uptime ≥ 99,5% trong 3 tháng Hypercare

2

Tất cả 11 module Go\-Live đúng kế hoạch

100% milestone hoàn thành đúng thời hạn

3

Người dùng chấp nhận hệ thống \(UAT pass\)

UAT sign\-off ≥ 95% test cases passed

4

Hiệu năng đáp ứng SLA

Response time < 3 giây cho 95% giao dịch

5

Không vượt ngân sách

Chi phí thực tế ≤ 110% ngân sách phê duyệt

6

Truy xuất lô hàng đầy đủ

100% vật tư có thể truy xuất nguồn gốc lô/hạn

# __7\. Phê duyệt & Chữ ký__

__Project Sponsor__

__Project Manager__

__Đại diện Bệnh viện__

Ký tên: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Ngày: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Ký tên: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Ngày: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Ký tên: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Ngày: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

