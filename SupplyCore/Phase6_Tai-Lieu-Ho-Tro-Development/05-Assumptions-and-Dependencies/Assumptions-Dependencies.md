__SUPPLYCORE – ASSUMPTIONS & DEPENDENCIES DOCUMENT__

Tài liệu Giả định & Phụ thuộc Dự án  |  Phiên bản 1\.0  |  05/2026

Trạng thái: Đang xem xét  |  Cần xác nhận từ: Hospital IT, Kế toán, Khoa VTYT

Tài liệu này liệt kê toàn bộ giả định \(assumptions\) được đưa ra trong quá trình thiết kế SupplyCore và các phụ thuộc \(dependencies\) kỹ thuật & nghiệp vụ mà dự án phải đảm bảo\. Mỗi giả định sai lệch hoặc phụ thuộc không được đáp ứng đều có thể ảnh hưởng đến timeline hoặc chất lượng hệ thống\.

# __PHẦN A: GIẢ ĐỊNH \(ASSUMPTIONS\)__

## __A\.1 Giả định Kỹ thuật & Hạ tầng__

__ID__

__Nhóm__

__Nội dung Giả định__

__Chủ sở hữu xác nhận__

__Rủi ro nếu sai__

__Trạng thái xác nhận__

__A\-T01__

Hạ tầng

Server bệnh viện đáp ứng: Ubuntu 22\.04, RAM 16GB\+, SSD 100GB\+, CPU 4 vCPU\+

Hospital IT

__Cao__

Chưa xác nhận

__A\-T02__

Hạ tầng

Kết nối LAN/WiFi ổn định trong tất cả khu vực kho \(< 50ms latency\)

Hospital IT

__Cao__

Đang kiểm tra

__A\-T03__

Hạ tầng

Điện lưới ổn định có UPS backup cho server và thiết bị kho

Hospital IT

__Trung bình__

Chưa xác nhận

__A\-T04__

Frappe

ERPNext v15 và Frappe v15 stable trong suốt dự án, không có breaking changes lớn

Tech Lead

__Trung bình__

Theo dõi changelog

__A\-T05__

Database

MariaDB 10\.11 hỗ trợ đầy đủ các tính năng được sử dụng \(JSON field, Full\-text search\)

Tech Lead

__Thấp__

Đã xác nhận

__A\-T06__

Thiết bị

Các thiết bị PDA/scanner tại kho tương thích với web browser hiện đại \(Chrome 100\+\)

Hospital IT

__Cao__

Chưa xác nhận

__A\-T07__

Email

SMTP server bệnh viện có thể gửi email thông báo từ hệ thống SupplyCore

Hospital IT

__Thấp__

Chưa xác nhận

__A\-T08__

Backup

Backup storage đủ dung lượng \(tối thiểu 500GB\) và được backup hàng ngày

Hospital IT

__Trung bình__

Chưa xác nhận

## __A\.2 Giả định Nghiệp vụ & Quy trình__

__ID__

__Nhóm__

__Nội dung Giả định__

__Chủ sở hữu xác nhận__

__Rủi ro nếu sai__

__Trạng thái xác nhận__

__A\-B01__

Dữ liệu

Danh mục vật tư hiện tại có thể được cung cấp đầy đủ \(mã, tên, đơn vị, nhóm\) trước T4/2026

Khoa VTYT

__Cao__

Đang thu thập

__A\-B02__

Dữ liệu

Danh sách nhà cung cấp và hợp đồng hiện tại có thể được số hóa đưa vào hệ thống

Phòng Vật tư

__Trung bình__

Chưa bắt đầu

__A\-B03__

Quy trình

Quy trình nghiệp vụ được chuẩn hóa và thống nhất trước khi design DocType

BA \+ Hospital

__Cao__

Đang thực hiện

__A\-B04__

BHYT

Danh mục vật tư BHYT chi trả và mức giá trần được cung cấp từ bệnh viện

Kế toán BV

__Cao__

Chưa xác nhận

__A\-B05__

Người dùng

Nhân viên kho có khả năng sử dụng máy tính/tablet ở mức cơ bản

Khoa VTYT

__Trung bình__

Giả định ban đầu

__A\-B06__

Người dùng

Ít nhất 1 super\-user mỗi khoa/phòng được đào tạo trước Go\-Live

PM \+ Hospital

__Trung bình__

Kế hoạch đào tạo

__A\-B07__

Tích hợp

HIS hiện tại có API hoặc database schema có thể đọc dữ liệu bệnh nhân/chẩn đoán

Hospital IT

__Cao__

Chưa xác nhận

__A\-B08__

Pháp lý

Không có thay đổi lớn về quy định pháp lý \(Thông tư BYT\) trong thời gian dự án

PM

__Thấp__

Theo dõi

## __A\.3 Giả định Tổ chức & Dự án__

__ID__

__Nhóm__

__Nội dung Giả định__

__Chủ sở hữu xác nhận__

__Rủi ro nếu sai__

__Trạng thái xác nhận__

__A\-O01__

Dự án

Ngân sách 1\.5 tỷ VNĐ được phê duyệt và giải ngân đúng milestone

Project Sponsor

__Cao__

Đã ký Project Charter

__A\-O02__

Dự án

Team 6 developer được phân bổ full\-time trong suốt dự án \(không bị rút nguồn lực\)

PM \+ MedCons

__Cao__

Cam kết nội bộ

__A\-O03__

Stakeholder

Stakeholder phía bệnh viện tham gia UAT ít nhất 20% thời gian \(2 ngày/tuần trong 2 tháng UAT\)

PM \+ Hospital

__Cao__

Chưa ký cam kết

__A\-O04__

Timeline

Không có holiday/Tết kéo dài làm gián đoạn sprint \(kế hoạch đã trừ ngày nghỉ Lễ\)

PM

__Thấp__

Đã tính vào plan

__A\-O05__

Quyết định

Thời gian phản hồi quyết định từ Sponsor: < 3 ngày làm việc với CR cấp 3\-4

Project Sponsor

__Trung bình__

Cam kết trong Charter

# __PHẦN B: PHỤ THUỘC \(DEPENDENCIES\)__

## __B\.1 Phụ thuộc Kỹ thuật__

__ID__

__Loại__

__Tên Phụ thuộc__

__Mô tả__

__Nhà cung cấp__

__Mức ảnh hưởng__

__Kế hoạch dự phòng__

__D\-T01__

Framework

Frappe v15

Nền tảng phát triển chính, toàn bộ app phụ thuộc

Frappe Technologies

Rất cao

Pin version; theo dõi security patches

__D\-T02__

Framework

ERPNext v15

Kế thừa Accounting, HR module

ERPNext/Frappe

Cao

Custom override nếu có conflict

__D\-T03__

Database

MariaDB 10\.11

Database engine chính

MariaDB Foundation

Rất cao

Backup plan \+ cloud DB failover

__D\-T04__

Cache

Redis 7\.x

Cache, session, background queue

Redis Ltd\.

Cao

Redis Sentinel cho HA

__D\-T05__

Web Server

Nginx \+ Gunicorn

HTTP serving, load balancing

Open source

Cao

HAProxy thay thế

__D\-T06__

CI/CD

GitHub Actions

Automated build, test, deploy

GitHub/Microsoft

Trung bình

GitLab CI dự phòng

__D\-T07__

Container

Docker 24\+

Dev và staging environment

Docker Inc\.

Trung bình

Manual setup nếu cần

__D\-T08__

PDA SDK

Frappe Mobile

Web\-based PDA interface

Frappe

Cao

PWA custom thay thế

## __B\.2 Phụ thuộc Bên ngoài \(External Dependencies\)__

__ID__

__Loại__

__Tên Phụ thuộc__

__Mô tả__

__Nhà cung cấp__

__Mức ảnh hưởng__

__Kế hoạch dự phòng__

__D\-E01__

HIS API

HIS Bệnh viện

API lấy thông tin bệnh nhân, chẩn đoán cho cấp phát theo BN

Nhà cung cấp HIS

Cao

Nhập thủ công nếu API chưa sẵn sàng

__D\-E02__

Email

SMTP Hospital

Gửi thông báo, alert, báo cáo tự động

Hospital IT

Trung bình

SendGrid backup

__D\-E03__

Barcode

Barcode/QR Library

Đọc và generate mã vạch vật tư

Open source \(zxing\)

Trung bình

Library thay thế sẵn có

__D\-E04__

PDF

wkhtmltopdf

Generate phiếu nhập/xuất kho PDF

wkhtmltopdf project

Trung bình

WeasyPrint thay thế

__D\-E05__

Auth

LDAP/AD Hospital

SSO authentication với Active Directory bệnh viện

Hospital IT

Thấp

Local auth nếu LDAP chưa sẵn sàng

__D\-E06__

Data

Danh mục VTYT BYT

Danh mục vật tư y tế chuẩn từ Bộ Y tế

Bộ Y tế

Cao

Nhập thủ công từ file Excel BYT

## __B\.3 Dependency Matrix – Tổng hợp Mức độ ảnh hưởng__

__RẤT CAO – Block project nếu thiếu__

Frappe v15, ERPNext v15, MariaDB, Danh mục VTYT BYT, HIS API

__CAO – Cần workaround ngay__

Redis, Nginx/Gunicorn, PDA SDK, SMTP Email, Thiết bị PDA

__TRUNG BÌNH – Có thể trì hoãn__

GitHub Actions, Docker, Barcode lib, PDF, LDAP/AD

__THẤP – Nice\-to\-have__

Không có dependency nào trong nhóm này

## __B\.4 Lịch xác nhận Giả định & Phụ thuộc__

__Hạng mục cần xác nhận__

__Hạn xác nhận__

__Người yêu cầu__

__Người xác nhận__

__Hậu quả nếu trễ__

Server spec audit \(A\-T01\)

15/01/2026

Tech Lead

Hospital IT

Ảnh hưởng env setup và architecture decision

Danh mục vật tư \(A\-B01\)

28/02/2026

BA

Khoa VTYT

Không thể build DocType Item đúng hạn

HIS API spec \(D\-E01\)

28/02/2026

Tech Lead

Hospital IT \+ HIS Vendor

Phải fallback manual input cho M7

Danh mục BHYT \(A\-B04\)

31/03/2026

BA

Kế toán BV

Không thể hoàn thành M8 \(Kế toán\)

Cam kết UAT resource \(A\-O03\)

30/04/2026

PM

Hospital Management

UAT phase không đủ người test, trễ Go\-Live

PDA device compatibility \(A\-T06\)

30/04/2026

Tech Lead

Hospital IT

Phải thiết kế lại M4 WMS interface

