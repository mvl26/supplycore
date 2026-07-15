__SUPPLYCORE__

__Hệ Thống Quản Lý Chuỗi Cung Ứng Vật Tư Tiêu Hao Bệnh Viện__

__BUSINESS REQUIREMENTS DOCUMENT \(BRD\)__

*Tài Liệu Yêu Cầu Kinh Doanh*

Phiên bản: 1\.0

Ngày: 05/05/2026

Trạng thái: Bản chính thức

Nền tảng: Frappe Framework v15 \+ ERPNext v15

# 1\. THÔNG TIN TÀI LIỆU

## 1\.1 Lịch Sử Phiên Bản

__Phiên bản__

__Ngày__

__Tác giả__

__Mô tả thay đổi__

1\.0

05/05/2026

Team SupplyCore

Tạo tài liệu ban đầu

## 1\.2 Danh Sách Phê Duyệt

__Vai trò__

__Họ tên__

__Chữ ký__

__Ngày phê duyệt__

Giám đốc dự án

Trưởng khoa CNTT

Trưởng phòng Vật tư

Phòng Kế toán

# 2\. TÓM TẮT ĐIỀU HÀNH

SupplyCore là hệ thống phần mềm quản lý chuỗi cung ứng vật tư tiêu hao chuyên dụng cho môi trường bệnh viện, được xây dựng trên nền tảng Frappe Framework v15 kết hợp ERPNext v15\. Hệ thống được thiết kế dưới dạng một Frappe custom app độc lập, tận dụng tối đa các module chuẩn của ERPNext đồng thời bổ sung các nghiệp vụ đặc thù của ngành y tế\.

Các bệnh viện hiện đang đối mặt với nhiều thách thức nghiêm trọng trong quản lý vật tư tiêu hao: tình trạng thiếu hụt hoặc tồn kho quá mức, khó kiểm soát hạn sử dụng và lô sản xuất, quy trình thủ công gây lãng phí thời gian và dễ xảy ra sai sót, thiếu khả năng truy xuất nguồn gốc khi xảy ra sự cố an toàn y tế\. SupplyCore được phát triển để giải quyết toàn diện các vấn đề này\.

## 2\.1 Mục Tiêu Chiến Lược

- Số hóa toàn bộ quy trình quản lý vật tư từ đặt hàng đến cấp phát sử dụng
- Đảm bảo truy xuất nguồn gốc 100% theo lô, hạn dùng \(FEFO\)
- Tích hợp với hệ thống tài chính – kế toán ERPNext, quản lý hợp đồng nhà cung cấp
- Hỗ trợ quy định BHYT, Bộ Y tế về mã vật tư, nhóm BHYT N01–N09
- Cung cấp dashboard điều hành thời gian thực cho lãnh đạo bệnh viện
- Nền tảng sẵn sàng tích hợp HIS/EMR trong tương lai

# 3\. BỐI CẢNH KINH DOANH

## 3\.1 Hiện Trạng Ngành

Các bệnh viện Việt Nam đang trong giai đoạn chuyển đổi số mạnh mẽ theo Đề án 06 của Chính phủ\. Quản lý vật tư y tế tiêu hao chiếm tỷ trọng lớn trong chi phí vận hành bệnh viện \(thường từ 25\-40% tổng chi phí\), nhưng phần lớn vẫn được thực hiện thủ công hoặc trên các phần mềm rời rạc thiếu tích hợp\.

## 3\.2 Các Thách Thức Hiện Tại

__STT__

__Thách thức__

__Biểu hiện__

__Tác động__

1

Quản lý tồn kho thủ công

Excel, sổ tay ghi chép, không đồng bộ

Thiếu/thừa hàng, lãng phí

2

Kiểm soát hạn dùng kém

Vật tư hết hạn phát hiện muộn

Rủi ro an toàn bệnh nhân

3

Thiếu truy xuất nguồn gốc

Không theo dõi lô sản xuất

Không xử lý được recall

4

Quy trình phê duyệt chậm

PO, phiếu xuất qua email/giấy

Chậm trễ điều trị

5

Thiếu báo cáo tổng hợp

Dữ liệu phân tán, khó tổng hợp

Quyết định thiếu cơ sở

6

Quản lý BHYT phức tạp

Mã BHYT thay đổi thường xuyên

Sai sót thanh toán BHYT

## 3\.3 Cơ Hội Cải Tiến

Với nền tảng ERPNext v15, SupplyCore có thể tận dụng hạ tầng sẵn có về Purchase Management, Inventory, Accounting để xây dựng một hệ thống tích hợp hoàn chỉnh với chi phí phát triển tối ưu, đồng thời đảm bảo khả năng mở rộng và bảo trì lâu dài\.

# 4\. CÁC BÊN LIÊN QUAN \(STAKEHOLDERS\)

## 4\.1 Bên Liên Quan Nội Bộ

__Vai trò__

__Bộ phận__

__Trách nhiệm / Kỳ vọng__

__Mức độ ảnh hưởng__

Giám đốc bệnh viện

Ban Giám đốc

Phê duyệt ngân sách, quyết định chiến lược

Cao

Trưởng phòng Vật tư

Phòng Vật tư \- TTBYT

Quản lý tồn kho, hợp đồng NCC, nhập kho

Rất cao

Kế toán trưởng

Phòng Kế toán

Thanh toán NCC, đối chiếu chứng từ

Cao

Điều dưỡng trưởng khoa

Các khoa lâm sàng

Đặt hàng nội bộ, nhận vật tư, cấp phát

Rất cao

Thủ kho tổng

Phòng Vật tư

Nhập xuất kho, kiểm kê, QC

Rất cao

Kiểm soát nội bộ

Phòng Kiểm soát

Kiểm tra tuân thủ, báo cáo

Trung bình

Đội CNTT bệnh viện

Phòng CNTT

Triển khai, vận hành hệ thống

Cao

## 4\.2 Bên Liên Quan Bên Ngoài

__Bên liên quan__

__Mối quan hệ với hệ thống__

__Mức độ ảnh hưởng__

Nhà cung cấp \(NCC\)

Nhận PO, xác nhận giao hàng, xuất hóa đơn

Cao

Cơ quan BHYT \(BHXH\)

Quy định mã vật tư BHYT, thanh toán

Cao

Bộ Y tế

Quy định danh mục, tiêu chuẩn chất lượng

Cao

Đơn vị kiểm định

Cấp chứng nhận chất lượng vật tư

Trung bình

# 5\. PHẠM VI DỰ ÁN

## 5\.1 Phạm Vi Bao Gồm \(In\-Scope\)

SupplyCore giai đoạn 1 bao gồm 11 module nghiệp vụ cốt lõi:

__Mã__

__Module__

__Mô tả chức năng chính__

__Nền tảng__

M1

Hợp đồng & Nhà cung cấp

Quản lý danh mục NCC, hợp đồng khung, bảng giá, điều khoản

ERPNext \+ Custom

M2

Kế hoạch tồn kho & Gọi hàng

Dự báo nhu cầu, lập kế hoạch mua sắm, tạo Release Order từ hợp đồng khung

ERPNext \+ Custom

M3

Tiếp nhận & Kiểm tra QC

Tiếp nhận hàng, kiểm tra lô/hạn dùng/số lượng/quy cách, ghi nhận kết quả QC

ERPNext \+ Custom

M4

WMS & PDA

Quản lý vị trí kho, vận hành PDA/barcode scanner, hỗ trợ kho 3 tầng

Custom

M5

Lô, Hạn dùng & FEFO

Theo dõi lô sản xuất, hạn sử dụng, xuất kho theo nguyên tắc FEFO tự động

ERPNext \+ Custom

M6

Luân chuyển nội bộ

Chuyển kho giữa kho tổng – kho con – kho khoa phòng, phê duyệt nội bộ

ERPNext

M7

Cấp phát & Ghi nhận sử dụng

Cấp phát cho khoa/phòng hoặc gắn bệnh nhân cụ thể, ghi nhận tiêu thụ thực tế

Custom

M8

Kế toán & Thanh toán

Tự động hạch toán, đối chiếu hóa đơn NCC với PO và phiếu nhận hàng

ERPNext

M9

Kiểm kê & Đối soát

Lập kế hoạch kiểm kê, nhập số liệu thực tế, đối chiếu sổ sách, xử lý chênh lệch

ERPNext \+ Custom

M10

Truy xuất & Điều tra

Truy xuất lịch sử lô hàng, xử lý lệnh thu hồi \(recall\), điều tra sự cố vật tư

Custom

M11

Dashboard & Cảnh báo

Bảng điều khiển điều hành, KPI, cảnh báo tồn kho thấp/hạn dùng/công nợ

Frappe UI \+ Custom

## 5\.2 Ngoài Phạm Vi \(Out\-of\-Scope\) \- Giai Đoạn 1

- Quản lý dược phẩm/thuốc \(có module riêng theo quy định đặc thù\)
- Tài sản cố định – trang thiết bị y tế có giá trị lớn
- Module đấu thầu tập trung \(Centralized Procurement\)
- Tích hợp cổng thanh toán điện tử
- Kết nối trực tiếp HIS/EMR/LIS \(thiết kế API sẵn sàng, chưa kết nối\)

# 6\. YÊU CẦU KINH DOANH CHI TIẾT

## 6\.1 M1 – Quản Lý Hợp Đồng & Nhà Cung Cấp

__Mã YC__

__Yêu cầu kinh doanh__

__Ưu tiên__

BR\-M1\-01

Hệ thống phải lưu trữ đầy đủ thông tin nhà cung cấp bao gồm mã NCC, tên, địa chỉ, mã số thuế, thông tin liên hệ, danh mục vật tư cung cấp

Bắt buộc \(Must Have\)

BR\-M1\-02

Hệ thống phải hỗ trợ quản lý Hợp đồng Khung \(Framework Contract\) với NCC, bao gồm: giá trị hợp đồng, thời hạn, điều khoản thanh toán, danh mục vật tư và đơn giá

Bắt buộc \(Must Have\)

BR\-M1\-03

Hệ thống phải tự động cảnh báo khi hợp đồng khung sắp hết hạn \(trước 30, 15, 7 ngày\) hoặc khi giá trị hợp đồng vượt ngưỡng sử dụng

Bắt buộc \(Must Have\)

BR\-M1\-04

Hệ thống phải lưu lịch sử đánh giá NCC \(chất lượng giao hàng, đúng hạn, đúng số lượng, đúng quy cách\) và tổng hợp điểm đánh giá theo kỳ

Nên có \(Should Have\)

BR\-M1\-05

Hệ thống phải hỗ trợ quản lý bảng giá NCC theo từng thời kỳ, cho phép so sánh giá giữa nhiều NCC cùng cung cấp một loại vật tư

Bắt buộc \(Must Have\)

## 6\.2 M2 – Kế Hoạch Tồn Kho & Gọi Hàng

__Mã YC__

__Yêu cầu kinh doanh__

__Ưu tiên__

BR\-M2\-01

Hệ thống phải hỗ trợ thiết lập mức tồn kho tối thiểu \(Min\), tối đa \(Max\) và điểm đặt hàng lại \(Reorder Point\) cho từng vật tư tại từng kho

Bắt buộc \(Must Have\)

BR\-M2\-02

Hệ thống phải tự động tạo đề xuất mua hàng khi tồn kho xuống dưới điểm Reorder Point, kèm theo gợi ý số lượng đặt hàng

Bắt buộc \(Must Have\)

BR\-M2\-03

Hệ thống phải hỗ trợ tạo Release Order từ Hợp đồng Khung hiện hành, tự động điền đơn giá theo hợp đồng, không cần chào hàng lại

Bắt buộc \(Must Have\)

BR\-M2\-04

Hệ thống phải cung cấp báo cáo dự báo nhu cầu dựa trên lịch sử tiêu thụ 3\-6\-12 tháng, điều chỉnh theo mùa và các yếu tố đặc thù bệnh viện

Nên có \(Should Have\)

## 6\.3 M3 – Tiếp Nhận & Kiểm Tra Chất Lượng

__Mã YC__

__Yêu cầu kinh doanh__

__Ưu tiên__

BR\-M3\-01

Mọi lô hàng nhập kho PHẢI đi qua quy trình QC bắt buộc: xác nhận số lô, hạn sử dụng, số lượng thực tế, kiểm tra quy cách đóng gói

Bắt buộc \(Must Have\)

BR\-M3\-02

Hệ thống phải hỗ trợ nhập kho một phần \(partial receipt\) khi hàng giao không đủ số lượng theo PO, tự động tạo backorder

Bắt buộc \(Must Have\)

BR\-M3\-03

Hệ thống phải lưu lý do từ chối nhập kho và tự động thông báo cho NCC khi lô hàng bị reject, kèm biên bản từ chối

Bắt buộc \(Must Have\)

## 6\.4 M5 – Quản Lý Lô, Hạn Dùng & FEFO

__Mã YC__

__Yêu cầu kinh doanh__

__Ưu tiên__

BR\-M5\-01

Hệ thống PHẢI áp dụng nguyên tắc FEFO \(First Expired, First Out\) tự động khi xuất kho, ưu tiên lô có hạn dùng gần nhất

Bắt buộc \(Must Have\)

BR\-M5\-02

Hệ thống phải cảnh báo vật tư sắp hết hạn trong vòng 30, 60, 90 ngày\. Vật tư đã hết hạn phải bị khóa không cho xuất kho

Bắt buộc \(Must Have\)

BR\-M5\-03

Hệ thống phải hỗ trợ xử lý lệnh thu hồi \(product recall\) theo số lô: truy vết toàn bộ lô hàng đã sử dụng, đang tồn kho, và thông báo cho các khoa liên quan

Bắt buộc \(Must Have\)

## 6\.5 M7 – Cấp Phát & Ghi Nhận Sử Dụng

__Mã YC__

__Yêu cầu kinh doanh__

__Ưu tiên__

BR\-M7\-01

Hệ thống phải hỗ trợ hai hình thức cấp phát: \(1\) Cấp phát theo khoa/phòng \(không gắn bệnh nhân\), \(2\) Cấp phát gắn với mã bệnh nhân cụ thể

Bắt buộc \(Must Have\)

BR\-M7\-02

Vật tư cấp phát cho bệnh nhân PHẢI được gắn mã BHYT tương ứng \(nhóm N01\-N09\) để phục vụ quyết toán BHYT

Bắt buộc \(Must Have\)

BR\-M7\-03

Hệ thống phải cho phép ghi nhận số lượng vật tư thực tế đã sử dụng cho bệnh nhân \(thực tế có thể khác số lượng cấp phát ban đầu\)

Bắt buộc \(Must Have\)

## 6\.6 M8 – Kế Toán & Thanh Toán NCC

__Mã YC__

__Yêu cầu kinh doanh__

__Ưu tiên__

BR\-M8\-01

Hệ thống phải tự động tạo bút toán kế toán \(GL Entry\) khi nhập kho, xuất kho, trả hàng, phù hợp với chuẩn mực kế toán Việt Nam

Bắt buộc \(Must Have\)

BR\-M8\-02

Hệ thống phải hỗ trợ 3 chiều đối chiếu \(3\-way matching\): Purchase Order – Purchase Receipt – Purchase Invoice trước khi phê duyệt thanh toán

Bắt buộc \(Must Have\)

BR\-M8\-03

Hệ thống phải quản lý hạn mức tín dụng NCC và cảnh báo khi công nợ vượt hạn mức hoặc quá hạn thanh toán

Nên có \(Should Have\)

# 7\. YÊU CẦU ĐẶC THÙ BHYT

Đây là nhóm yêu cầu đặc thù nhất của SupplyCore so với phần mềm ERP thông thường\. Tất cả logic BHYT phải được thiết kế tham số hóa, không hard\-code, do quy định Bộ Y tế thay đổi thường xuyên\.

__Mã YC__

__Yêu cầu__

__Chi tiết__

__Ưu tiên__

BR\-BH\-01

Danh mục mã BHYT

Mỗi vật tư có thể gắn 1\-N mã BHYT thuộc nhóm N01–N09 theo Thông tư Bộ Y tế\. Hỗ trợ cập nhật danh mục theo định kỳ

Bắt buộc

BR\-BH\-02

Tỷ lệ thanh toán BHYT

Cấu hình tỷ lệ thanh toán theo nhóm vật tư, đối tượng bệnh nhân \(BHYT đúng tuyến, trái tuyến\), mức hưởng \(80%, 95%, 100%\)

Bắt buộc

BR\-BH\-03

Đơn vị tính kép

Mỗi vật tư có tối thiểu 2 đơn vị: đơn vị mua \(hộp, thùng\) và đơn vị sử dụng/BHYT \(cái, bộ, ml\)\. Hệ thống tự động quy đổi

Bắt buộc

BR\-BH\-04

Giá trần BHYT

Quản lý giá trần thanh toán BHYT theo từng mã vật tư\. Cảnh báo khi giá NCC vượt giá trần BHYT

Bắt buộc

BR\-BH\-05

Báo cáo quyết toán

Tự động tổng hợp dữ liệu vật tư BHYT theo bệnh nhân, khoa phòng, mã BHYT phục vụ quyết toán BHXH định kỳ

Bắt buộc

# 8\. YÊU CẦU PHI CHỨC NĂNG

## 8\.1 Hiệu Năng \(Performance\)

- Thời gian phản hồi màn hình chính: ≤ 2 giây với 50 người dùng đồng thời
- Thời gian load báo cáo phức tạp: ≤ 10 giây
- Xử lý giao dịch nhập/xuất kho: ≤ 3 giây mỗi giao dịch
- Uptime hệ thống: ≥ 99\.5% trong giờ làm việc \(6:00\-22:00\)

## 8\.2 Bảo Mật \(Security\)

- Xác thực 2 yếu tố \(2FA\) bắt buộc cho tài khoản quản trị
- Phân quyền chi tiết theo vai trò \(Role\-Based Access Control\) trên từng Doctype
- Audit log đầy đủ cho mọi thao tác: tạo, sửa, xóa, phê duyệt
- Mã hóa dữ liệu nhạy cảm \(thông tin bệnh nhân, hợp đồng\) khi lưu trữ
- Tuân thủ Nghị định 13/2023/NĐ\-CP về bảo vệ dữ liệu cá nhân

## 8\.3 Khả Năng Mở Rộng \(Scalability\)

- Hỗ trợ tối thiểu 200 người dùng đồng thời
- Lưu trữ dữ liệu giao dịch tối thiểu 5 năm không ảnh hưởng hiệu năng
- Kiến trúc hỗ trợ multi\-site \(nhiều bệnh viện trên cùng một hạ tầng\)

## 8\.4 Khả Năng Sử Dụng \(Usability\)

- Giao diện tiếng Việt hoàn toàn, hỗ trợ mobile responsive
- Thời gian đào tạo người dùng mới: ≤ 8 giờ cho nghiệp vụ cơ bản
- Hỗ trợ barcode/QR code scanning trên thiết bị di động và PDA

# 9\. TIÊU CHÍ THÀNH CÔNG

__STT__

__Tiêu chí__

__Chỉ số đo lường \(KPI\)__

__Mục tiêu__

1

Giảm tồn kho dư thừa

Giá trị tồn kho trung bình / tháng

Giảm 20% sau 6 tháng

2

Loại bỏ vật tư hết hạn

% vật tư hết hạn phải hủy

< 0\.5% giá trị tồn kho

3

Rút ngắn chu kỳ đặt hàng

Thời gian từ đề xuất đến PO

< 24 giờ \(so với 3\-5 ngày\)

4

Độ chính xác tồn kho

% chênh lệch kiểm kê thực tế vs sổ sách

< 1%

5

Tuân thủ FEFO

% giao dịch xuất kho đúng FEFO

100% tự động

6

Tỷ lệ sai sót BHYT

% từ chối thanh toán do sai mã BHYT

< 0\.1%

7

Hài lòng người dùng

Điểm khảo sát sau đào tạo

≥ 80/100

# 10\. LỘ TRÌNH TRIỂN KHAI DỰ KIẾN

__Giai đoạn__

__Thời gian__

__Nội dung chính__

__Deliverable__

Phase 1

Tháng 1\-2

Phân tích yêu cầu, thiết kế hệ thống, thiết kế CSDL

BRD, URS, DB Design

Phase 2

Tháng 3\-5

Phát triển core modules: M1\-M3, M8 \(ERPNext base \+ custom\)

Prototype M1\-M3

Phase 3

Tháng 6\-8

Phát triển M4\-M7, M9\-M11, tích hợp BHYT

Full system

Phase 4

Tháng 9\-10

UAT tại bệnh viện pilot, đào tạo người dùng

UAT sign\-off

Phase 5

Tháng 11\-12

Go\-live, hỗ trợ vận hành, chuyển giao

Go\-live

## 10\.1 Giả Định & Ràng Buộc

- Bệnh viện đã có hạ tầng máy chủ đủ năng lực hoặc sẵn sàng nâng cấp
- Dữ liệu danh mục vật tư, NCC, tài khoản kế toán được cung cấp đầy đủ trước khi go\-live
- Ban lãnh đạo bệnh viện cam kết hỗ trợ thay đổi quy trình \(change management\)
- Đội ngũ CNTT bệnh viện được đào tạo vận hành Frappe/ERPNext ít nhất 2 người

─────────────────────────────────────────────────────────────────────────────

Tài liệu BRD này là cơ sở chính thức cho việc phát triển SupplyCore\. Mọi thay đổi phạm vi phải được phê duyệt bởi các bên liên quan chính và cập nhật vào tài liệu này\.

