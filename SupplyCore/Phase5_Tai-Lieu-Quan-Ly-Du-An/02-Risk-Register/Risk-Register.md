__SUPPLYCORE – RISK REGISTER__

Sổ đăng ký & Kế hoạch xử lý Rủi ro Dự án

Phiên bản 1\.0  |  Ngày: 05/2026  |  Trạng thái: Đang cập nhật

## __Bảng chú thích Mức độ Rủi ro__

__Xác suất \(P\)__

__1 – Hiếm khi__

__2 – Có thể xảy ra__

__3 – Thỉnh thoảng__

__4 – Thường xuyên__

__5 – Gần như chắc chắn__

__Tác động \(I\)__

__Thấp \(1–4\)__

__Trung bình \(5–9\)__

__Cao \(10–16\)__

__Rất cao \(17–25\)__

Mức rủi ro = P × I  |  P: 1–5  |  I: 1–5

# __1\. Rủi ro Kỹ thuật__

__ID__

__Nhóm__

__Mô tả Rủi ro__

__P__

__I__

__Mức độ__

__Kế hoạch Xử lý \(Mitigation\)__

__Người chịu TN__

__Trạng thái__

R\-T01

Kỹ thuật

Frappe/ERPNext v15 có breaking changes làm ảnh hưởng custom app

3

4

__Cao__

Theo dõi changelog Frappe mỗi sprint; pin phiên bản cụ thể trong requirements\.txt; có môi trường test riêng để upgrade

Tech Lead

Đang theo dõi

R\-T02

Kỹ thuật

Hiệu năng hệ thống kém khi số lượng giao dịch lớn \(>1000 GDịch/ngày\)

3

5

__Cao__

Benchmark sớm từ sprint 3; tối ưu database index; caching Redis; load test trước Go\-Live

Tech Lead

Chưa bắt đầu

R\-T03

Kỹ thuật

Tích hợp PDA/barcode scanner gặp lỗi tương thích phần cứng

2

3

__Trung bình__

Xác định danh sách thiết bị được hỗ trợ từ đầu; test thực tế với hardware bệnh viện

Dev Lead M4

Chưa bắt đầu

R\-T04

Kỹ thuật

Mất dữ liệu do lỗi migration từ hệ thống cũ sang SupplyCore

2

5

__Cao__

Backup đầy đủ trước migration; dry\-run migration 3 lần; rollback plan rõ ràng

DBA/Tech Lead

Chưa bắt đầu

R\-T05

Kỹ thuật

Lỗ hổng bảo mật trong custom code Frappe

2

4

__Cao__

Code review bắt buộc; OWASP checklist; penetration test trước Go\-Live

Security Officer

Chưa bắt đầu

R\-T06

Kỹ thuật

API tích hợp HIS bị thay đổi phiên bản mà không thông báo

2

3

__Trung bình__

Ký SLA kỹ thuật với nhà cung cấp HIS; versioning API; mock server cho test

Tech Lead

Chưa bắt đầu

# __2\. Rủi ro Nghiệp vụ & Quy trình__

__ID__

__Nhóm__

__Mô tả Rủi ro__

__P__

__I__

__Mức độ__

__Kế hoạch Xử lý \(Mitigation\)__

__Người chịu TN__

__Trạng thái__

R\-B01

Nghiệp vụ

Yêu cầu thay đổi liên tục \(Scope Creep\) làm trễ timeline

4

4

__Cao__

Áp dụng Change Control Process nghiêm ngặt; baseline được ký duyệt; Change Board họp 2 tuần/lần

PM

Đang kiểm soát

R\-B02

Nghiệp vụ

Stakeholder không đồng thuận về quy trình nghiệp vụ chuẩn hóa

3

4

__Cao__

Workshop alignment với tất cả stakeholder trước khi design; RACI rõ ràng; escalation path

BA \+ PM

Đang thực hiện

R\-B03

Nghiệp vụ

Dữ liệu danh mục vật tư hiện tại không chuẩn, thiếu sót

4

3

__Cao__

Data audit sớm \(T1/2026\); data cleansing plan; chỉ định data owner phía bệnh viện

BA \+ Hospital IT

Đang thực hiện

R\-B04

Nghiệp vụ

Quy trình FEFO phức tạp hơn dự kiến do nhiều loại hạn dùng

2

3

__Trung bình__

Khảo sát kỹ quy trình FEFO hiện tại; prototype sớm; UAT riêng cho module M5

Dev Lead M5

Chưa bắt đầu

R\-B05

Nghiệp vụ

Tích hợp kế toán với ERPNext không phù hợp quy định BHYT VN

3

5

__Rất cao__

Tham vấn chuyên gia kế toán bệnh viện; review Thông tư 46; test case đặc thù BHYT

BA \+ Kế toán

Ưu tiên cao

R\-B06

Nghiệp vụ

Nhân viên kho từ chối chuyển đổi hệ thống mới \(Change Resistance\)

3

3

__Trung bình__

Change management plan; đào tạo sớm; super\-user program; lãnh đạo bệnh viện cam kết

PM \+ HR BV

Đang lên kế hoạch

# __3\. Rủi ro Nguồn lực & Tổ chức__

__ID__

__Nhóm__

__Mô tả Rủi ro__

__P__

__I__

__Mức độ__

__Kế hoạch Xử lý \(Mitigation\)__

__Người chịu TN__

__Trạng thái__

R\-O01

Tổ chức

Dev team thiếu kinh nghiệm Frappe Framework

3

4

__Cao__

Đào tạo Frappe nội bộ 2 tuần trước sprint 1; mentor từ Frappe community; pair programming

Tech Lead

Đang thực hiện

R\-O02

Tổ chức

Key developer nghỉ việc giữa chừng

2

5

__Cao__

Knowledge sharing bắt buộc; tài liệu kỹ thuật đầy đủ; cross\-training; điều khoản hợp đồng

PM

Đang kiểm soát

R\-O03

Tổ chức

Stakeholder phía bệnh viện không có thời gian tham gia UAT

3

4

__Cao__

Cam kết resource UAT ngay từ Project Charter; kế hoạch UAT chia nhỏ; user proxy

PM \+ Hospital

Chưa giải quyết

R\-O04

Tổ chức

Ngân sách dự án bị cắt giảm giữa chừng

2

5

__Cao__

Phân chia deliverable theo ưu tiên \(MoSCoW\); milestone payment; contingency 10%

PM \+ Sponsor

Đang kiểm soát

R\-O05

Tổ chức

Thay đổi nhân sự lãnh đạo bệnh viện ảnh hưởng cam kết dự án

1

5

__Trung bình__

Tài liệu hóa đầy đủ các cam kết; escalation to Board; Project Charter ký bởi nhiều cấp

PM

Theo dõi

# __4\. Rủi ro Hạ tầng & Bảo mật__

__ID__

__Nhóm__

__Mô tả Rủi ro__

__P__

__I__

__Mức độ__

__Kế hoạch Xử lý \(Mitigation\)__

__Người chịu TN__

__Trạng thái__

R\-I01

Hạ tầng

Server bệnh viện không đáp ứng yêu cầu kỹ thuật tối thiểu

3

4

__Cao__

Infrastructure audit T1/2026; spec requirements document ký duyệt; phương án cloud backup

Hospital IT

Đang kiểm tra

R\-I02

Hạ tầng

Mất điện/mạng ảnh hưởng hoạt động kho trong giờ cao điểm

2

4

__Cao__

UPS cho server; offline mode PDA; backup connectivity \(4G failover\)

Hospital IT

Chưa bắt đầu

R\-I03

Bảo mật

Rò rỉ dữ liệu bệnh nhân/tài chính do cấu hình sai

2

5

__Cao__

Security checklist deployment; role\-based access control; audit log; penetration test

Security Officer

Chưa bắt đầu

R\-I04

Bảo mật

Tấn công ransomware vào hệ thống bệnh viện

1

5

__Trung bình__

Backup daily offsite; network segmentation; antivirus; incident response plan

Hospital IT

Theo dõi

R\-I05

Hạ tầng

Không gian lưu trữ không đủ cho dữ liệu attachments và logs

3

2

__Trung bình__

Storage estimation sớm; auto\-archiving policy; monitoring disk usage

Hospital IT \+ Dev

Chưa bắt đầu

# __5\. Tóm tắt Dashboard Rủi ro__

__RẤT CAO__

1 rủi ro

R\-B05

__CAO__

9 rủi ro

R\-T01,T02,T04,T05,R\-B01,B02,B03,R\-O01,O2,O3,O4,R\-I01,I02,I03

__TRUNG BÌNH__

7 rủi ro

R\-T03,T06,R\-B04,B06,R\-O05,R\-I04,I05

__THẤP__

0 rủi ro

__TỔNG CỘNG__

17 rủi ro

## __Tần suất Review & Cập nhật__

- Sprint Review \(2 tuần/lần\): PM cập nhật trạng thái tất cả rủi ro đang mở
- Monthly Risk Report: Gửi Sponsor báo cáo rủi ro hàng tháng
- Rủi ro mới: Bất kỳ thành viên nào có thể đề xuất rủi ro mới qua Risk Log Template
- Escalation: Rủi ro mức Rất cao → PM phải báo cáo Sponsor trong vòng 24 giờ

