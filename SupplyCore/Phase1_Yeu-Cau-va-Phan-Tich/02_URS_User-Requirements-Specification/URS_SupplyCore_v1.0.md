__SUPPLYCORE__

__Hệ Thống Quản Lý Chuỗi Cung Ứng Vật Tư Tiêu Hao Bệnh Viện__

__USER REQUIREMENTS SPECIFICATION \(URS\)__

*Đặc Tả Yêu Cầu Người Dùng*

Phiên bản: 1\.0  |  Ngày: 05/05/2026  |  Trạng thái: Bản chính thức

# 1\. TỔNG QUAN VÀ PHẠM VI

Tài liệu này mô tả các yêu cầu hệ thống từ góc độ người dùng cuối cho phần mềm SupplyCore\. Các yêu cầu được thu thập thông qua phỏng vấn, khảo sát và quan sát quy trình làm việc thực tế tại bệnh viện\. Mỗi yêu cầu được gắn mã định danh, ưu tiên và tiêu chí chấp nhận rõ ràng\.

# 2\. NHÓM NGƯỜI DÙNG VÀ VAI TRÒ

SupplyCore phục vụ 7 nhóm người dùng chính với các nhu cầu và quyền truy cập khác nhau:

__STT__

__Nhóm người dùng__

__Bộ phận__

__Nhiệm vụ chính trong SupplyCore__

__Mã vai trò__

1

Quản trị viên hệ thống

Phòng CNTT

Cấu hình hệ thống, phân quyền, backup

SC\-ADMIN

2

Quản lý vật tư

Phòng Vật tư \- TTBYT

Quản lý toàn bộ hoạt động vật tư

SC\-MANAGER

3

Nhân viên mua hàng

Phòng Vật tư

Tạo/theo dõi PO, quản lý NCC, hợp đồng

SC\-PURCHASER

4

Thủ kho

Kho vật tư

Nhập/xuất/kiểm kê tồn kho, QC hàng hóa

SC\-STOREKEEPER

5

Điều dưỡng / Nhân viên khoa

Các khoa lâm sàng

Đặt hàng nội bộ, nhận vật tư, cấp phát

SC\-WARD\-STAFF

6

Kế toán vật tư

Phòng Kế toán

Đối chiếu chứng từ, thanh toán NCC

SC\-ACCOUNTANT

7

Lãnh đạo / Giám sát

Ban Giám đốc

Xem báo cáo, phê duyệt ngưỡng cao

SC\-EXECUTIVE

# 3\. YÊU CẦU NGƯỜI DÙNG THEO VAI TRÒ \(USER STORIES\)

## 3\.1 Nhân Viên Mua Hàng \(SC\-PURCHASER\)

__Mã__

__Là \[người dùng\]__

__Tôi muốn \[hành động\]__

__Để \[lợi ích\]__

__Ưu tiên__

URS\-PUR\-01

Nhân viên mua hàng

xem toàn bộ danh mục vật tư kèm tồn kho hiện tại và lịch sử tiêu thụ

để đưa ra quyết định đặt hàng chính xác

Cao

URS\-PUR\-02

Nhân viên mua hàng

tạo Purchase Order từ Release Order đã được phê duyệt, tự động điền giá từ hợp đồng khung

để tiết kiệm thời gian nhập liệu và tránh sai sót giá

Cao

URS\-PUR\-03

Nhân viên mua hàng

theo dõi trạng thái PO theo thời gian thực \(chờ phê duyệt, đã gửi NCC, đã giao một phần, hoàn thành\)

để chủ động xử lý khi có vấn đề

Cao

URS\-PUR\-04

Nhân viên mua hàng

so sánh giá của cùng một vật tư từ nhiều nhà cung cấp khác nhau

để chọn NCC tốt nhất và hợp lý nhất

Trung bình

URS\-PUR\-05

Nhân viên mua hàng

nhận cảnh báo tự động khi tồn kho xuống dưới mức Reorder Point

để chủ động đặt hàng trước khi thiếu hàng

Cao

URS\-PUR\-06

Nhân viên mua hàng

gửi PO điện tử đến NCC qua email trực tiếp từ hệ thống

để giảm thiểu bước thủ công

Trung bình

## 3\.2 Thủ Kho \(SC\-STOREKEEPER\)

__Mã__

__Là \[người dùng\]__

__Tôi muốn \[hành động\]__

__Để \[lợi ích\]__

__Ưu tiên__

URS\-SK\-01

Thủ kho

scan barcode/QR code vật tư nhập kho để tự động điền thông tin lô, hạn dùng

để tăng tốc độ nhập kho và giảm lỗi nhập liệu thủ công

Cao

URS\-SK\-02

Thủ kho

xem hướng dẫn QC rõ ràng cho từng loại vật tư khi tiếp nhận hàng

để đảm bảo kiểm tra đúng tiêu chuẩn

Cao

URS\-SK\-03

Thủ kho

in phiếu nhập kho, phiếu xuất kho có đầy đủ thông tin lô và hạn dùng

để lưu hồ sơ và ký xác nhận

Cao

URS\-SK\-04

Thủ kho

thực hiện kiểm kê theo từng vị trí kho, nhập số lượng thực tế trực tiếp trên thiết bị PDA

để kiểm kê nhanh và chính xác

Cao

URS\-SK\-05

Thủ kho

xem ngay danh sách vật tư sắp hết hạn trong 30/60/90 ngày

để lên kế hoạch sử dụng ưu tiên hoặc trả NCC

Cao

URS\-SK\-06

Thủ kho

hệ thống tự động gợi ý lô hàng xuất kho theo nguyên tắc FEFO

để không cần tính toán thủ công và đảm bảo tuân thủ

Cao

URS\-SK\-07

Thủ kho

tìm kiếm vị trí lưu trữ của một vật tư cụ thể trong kho bằng cách nhập mã hoặc scan

để lấy hàng nhanh khi có yêu cầu cấp phát

Trung bình

## 3\.3 Điều Dưỡng / Nhân Viên Khoa \(SC\-WARD\-STAFF\)

__Mã__

__Là \[người dùng\]__

__Tôi muốn \[hành động\]__

__Để \[lợi ích\]__

__Ưu tiên__

URS\-WD\-01

Điều dưỡng khoa

đặt yêu cầu vật tư cần bổ sung cho khoa trực tiếp trên hệ thống, không cần điện thoại hoặc viết giấy

để tiết kiệm thời gian và có bằng chứng yêu cầu rõ ràng

Cao

URS\-WD\-02

Điều dưỡng khoa

xem trạng thái đơn yêu cầu vật tư của khoa mình \(đang xử lý/đã duyệt/đã giao\)

để chủ động theo dõi và không cần hỏi lại kho

Cao

URS\-WD\-03

Điều dưỡng khoa

ghi nhận vật tư đã sử dụng cho bệnh nhân \(gắn mã bệnh nhân, mã BHYT\) ngay tại đầu giường hoặc phòng điều trị

để dữ liệu tiêu thụ chính xác và phục vụ quyết toán BHYT

Cao

URS\-WD\-04

Điều dưỡng khoa

xem lịch sử cấp phát của khoa mình trong tháng, so sánh với định mức

để kiểm soát chi phí khoa

Trung bình

URS\-WD\-05

Điều dưỡng khoa

tạo yêu cầu bổ sung khẩn cấp ngoài định kỳ khi có ca mổ đột xuất hoặc nhu cầu đặc biệt

để đáp ứng kịp thời nhu cầu lâm sàng

Cao

## 3\.4 Kế Toán Vật Tư \(SC\-ACCOUNTANT\)

__Mã__

__Là \[người dùng\]__

__Tôi muốn \[hành động\]__

__Để \[lợi ích\]__

__Ưu tiên__

URS\-ACC\-01

Kế toán vật tư

đối chiếu hóa đơn NCC với Purchase Order và phiếu nhận hàng \(3\-way matching\) chỉ với vài click

để phát hiện sai lệch trước khi thanh toán

Cao

URS\-ACC\-02

Kế toán vật tư

xem tổng hợp công nợ phải trả theo NCC, theo thời hạn thanh toán

để lên kế hoạch thanh toán hợp lý

Cao

URS\-ACC\-03

Kế toán vật tư

xuất báo cáo tổng hợp nhập xuất tồn theo tháng/quý/năm phục vụ kiểm toán

để cung cấp đủ hồ sơ khi kiểm toán yêu cầu

Cao

URS\-ACC\-04

Kế toán vật tư

xem hạch toán kế toán tự động được tạo cho từng phiếu nhập/xuất kho

để kiểm tra tính chính xác trước khi kết sổ

Cao

URS\-ACC\-05

Kế toán vật tư

tạo và in lệnh chi thanh toán NCC từ hệ thống

để gửi ngân hàng mà không cần tạo lại trên phần mềm khác

Trung bình

## 3\.5 Quản Lý Vật Tư \(SC\-MANAGER\)

__Mã__

__Là \[người dùng\]__

__Tôi muốn \[hành động\]__

__Để \[lợi ích\]__

__Ưu tiên__

URS\-MGR\-01

Quản lý vật tư

xem dashboard tổng quan toàn bộ hoạt động kho: tồn kho, đơn hàng đang mở, cảnh báo

để nắm bắt tình hình nhanh chóng mỗi sáng

Cao

URS\-MGR\-02

Quản lý vật tư

phê duyệt Release Order và Purchase Order trên điện thoại di động

để không bị gián đoạn quy trình khi vắng mặt tại văn phòng

Cao

URS\-MGR\-03

Quản lý vật tư

cấu hình mức tồn kho Min/Max/Reorder Point cho từng vật tư

để hệ thống tự động quản lý mức tồn phù hợp

Cao

URS\-MGR\-04

Quản lý vật tư

xem báo cáo phân tích ABC/XYZ vật tư để tối ưu mức tồn kho

để tập trung nguồn lực quản lý vào vật tư quan trọng nhất

Trung bình

URS\-MGR\-05

Quản lý vật tư

nhận cảnh báo khi có lô hàng sắp recall hoặc có khuyến cáo của Bộ Y tế

để xử lý kịp thời và đảm bảo an toàn bệnh nhân

Cao

## 3\.6 Lãnh Đạo \(SC\-EXECUTIVE\)

__Mã__

__Là \[người dùng\]__

__Tôi muốn \[hành động\]__

__Để \[lợi ích\]__

__Ưu tiên__

URS\-EXE\-01

Lãnh đạo bệnh viện

xem dashboard điều hành với các KPI chuỗi cung ứng: chi phí vật tư/bệnh nhân, vòng quay tồn kho, tỷ lệ hết hàng

để đánh giá hiệu quả hoạt động

Cao

URS\-EXE\-02

Lãnh đạo

nhận báo cáo tự động định kỳ qua email vào cuối tháng

để không cần đăng nhập hệ thống vẫn nắm được tình hình

Trung bình

URS\-EXE\-03

Lãnh đạo

xem so sánh chi phí vật tư giữa các khoa, theo dõi xu hướng theo thời gian

để phát hiện bất thường và ra quyết định kịp thời

Cao

# 4\. TIÊU CHÍ CHẤP NHẬN \(ACCEPTANCE CRITERIA\)

Dưới đây là tiêu chí chấp nhận chi tiết cho các yêu cầu quan trọng nhất:

## 4\.1 Tiêu Chí cho Quản Lý Nhập Kho \(URS\-SK\-01, SK\-02\)

__Điều kiện__

__Kết quả kỳ vọng__

__Kết quả__

Scan barcode hợp lệ

Hệ thống tự động điền mã vật tư, tên, đơn vị tính\. Người dùng chỉ cần nhập số lô và hạn dùng

□ Pass  □ Fail

Hạn dùng < 30 ngày

Hệ thống hiển thị cảnh báo màu đỏ, yêu cầu xác nhận từ cấp quản lý trước khi nhập kho

□ Pass  □ Fail

Số lượng thực tế < PO

Hệ thống ghi nhận số lượng thực tế, tự động tạo backorder cho phần còn thiếu và thông báo cho bộ phận mua hàng

□ Pass  □ Fail

Scan mã không tồn tại

Hệ thống hiển thị thông báo lỗi rõ ràng và cho phép người dùng nhập tìm kiếm thủ công hoặc tạo mã mới

□ Pass  □ Fail

## 4\.2 Tiêu Chí cho Cấp Phát Gắn BHYT \(URS\-WD\-03\)

__Điều kiện__

__Kết quả kỳ vọng__

__Kết quả__

Vật tư có mã BHYT

Hệ thống tự động hiển thị mã BHYT tương ứng \(N01\-N09\), tỷ lệ BHYT thanh toán và số tiền bệnh nhân phải trả

□ Pass  □ Fail

Giá vật tư > giá trần BHYT

Hệ thống cảnh báo và tự động tính phần vượt trần do bệnh nhân tự chi trả

□ Pass  □ Fail

Bệnh nhân không có thẻ BHYT

Hệ thống ghi nhận cấp phát theo hình thức dịch vụ, tổng chi phí 100% tự chi trả

□ Pass  □ Fail

## 4\.3 Tiêu Chí cho FEFO Tự Động \(URS\-SK\-06\)

__Điều kiện__

__Kết quả kỳ vọng__

__Kết quả__

Nhiều lô cùng mã vật tư

Hệ thống tự động gợi ý lô có hạn dùng sớm nhất\. Không cho phép xuất lô hạn dùng xa hơn khi lô gần hơn còn tồn

□ Pass  □ Fail

Xuất số lượng vượt 1 lô

Hệ thống tự động phân bổ: lấy hết lô cũ nhất trước, phần còn lại lấy từ lô tiếp theo theo FEFO

□ Pass  □ Fail

Lô đã hết hạn còn tồn kho

Hệ thống khóa không cho xuất kho\. Hiển thị cảnh báo đỏ và hướng dẫn quy trình xử lý hàng hết hạn

□ Pass  □ Fail

# 5\. YÊU CẦU GIAO DIỆN NGƯỜI DÙNG

## 5\.1 Nguyên Tắc Thiết Kế Giao Diện

- Giao diện hoàn toàn bằng tiếng Việt, có thể chuyển sang tiếng Anh theo cài đặt
- Responsive design: hoạt động tốt trên PC \(1920x1080\), tablet \(1024x768\), điện thoại \(360px\+\)
- Tuân thủ chuẩn giao diện Frappe UI – nhất quán với ERPNext để giảm thời gian học
- Màu sắc cảnh báo nhất quán: Đỏ = nguy hiểm/lỗi, Cam = cảnh báo, Xanh = bình thường
- Hỗ trợ dark mode theo cài đặt hệ điều hành

## 5\.2 Yêu Cầu Giao Diện Theo Module

__Module__

__Màn hình chính__

__Yêu cầu đặc thù__

M3 – Tiếp nhận

Màn hình nhập kho

Nút Scan to lớn ≥ 48px để dễ chạm trên tablet/PDA\. Hiển thị ảnh minh họa vật tư để đối chiếu trực quan

M4 – WMS/PDA

Giao diện PDA

Thiết kế tối giản cho màn hình nhỏ 4\-5 inch\. Font chữ ≥ 16px\. Chỉ hiện thông tin cần thiết cho thao tác hiện tại

M7 – Cấp phát

Phiếu cấp phát

Cho phép tìm kiếm bệnh nhân bằng mã BN hoặc tên\. Hiển thị rõ mã BHYT và tỷ lệ thanh toán

M11 – Dashboard

Bảng điều khiển

Dashboard có thể tùy chỉnh widget theo vai trò người dùng\. KPI hiển thị dạng số lớn \+ màu RAG \(Red/Amber/Green\)

## 5\.3 Yêu Cầu Trợ Năng \(Accessibility\)

- Hỗ trợ điều hướng bàn phím hoàn toàn \(Tab, Enter, Escape\)
- Ratio tương phản màu ≥ 4\.5:1 theo WCAG 2\.1 AA
- Tất cả hình ảnh có alt text mô tả
- Thông báo lỗi mô tả rõ ràng bằng tiếng Việt, không chỉ dùng màu sắc

# 6\. YÊU CẦU DỮ LIỆU

## 6\.1 Dữ Liệu Danh Mục Cần Có Trước Go\-live

__Danh mục__

__Nội dung__

__Đơn vị cung cấp__

__Hạn nộp__

Danh mục vật tư

Mã, tên, đơn vị tính, mã BHYT, nhóm vật tư

Phòng Vật tư

T\-4 tuần

Danh mục NCC

Tên, MST, địa chỉ, thông tin liên hệ, điều khoản thanh toán

Phòng Vật tư

T\-4 tuần

Hợp đồng khung hiện hành

Số HĐ, NCC, danh mục vật tư, đơn giá, thời hạn

Phòng Vật tư

T\-3 tuần

Cơ cấu kho

Danh sách kho tổng, kho con, kho khoa phòng và sơ đồ vị trí

Phòng CNTT

T\-3 tuần

Số dư tồn kho đầu kỳ

Tồn kho thực tế tại ngày go\-live, kèm lô và hạn dùng

Thủ kho

T\-1 tuần

Danh mục tài khoản kế toán

Hệ thống tài khoản theo thông tư 107/200 BTC

Kế toán

T\-4 tuần

## 6\.2 Yêu Cầu Lưu Trữ & Lịch Sử

- Lưu toàn bộ lịch sử giao dịch: không xóa vĩnh viễn, chỉ đánh dấu hủy \(soft delete\)
- Lưu lịch sử thay đổi \(audit trail\) tất cả trường dữ liệu quan trọng
- Thời gian lưu trữ tối thiểu 5 năm theo quy định lưu trữ y tế
- Hỗ trợ xuất toàn bộ dữ liệu ra file CSV/Excel khi cần kiểm toán

# 7\. RÀNG BUỘC VÀ GIẢ ĐỊNH

## 7\.1 Ràng Buộc Kỹ Thuật

- Hệ thống phải chạy trên Frappe Framework v15 và ERPNext v15, không sửa core source
- Tất cả customization qua hooks\.py, custom fields, client scripts
- Database: MariaDB 10\.6\+ hoặc MySQL 8\.0\+
- Không sử dụng thư viện frontend ngoài hệ sinh thái Frappe UI/Vue 3

## 7\.2 Ràng Buộc Nghiệp Vụ

- Logic BHYT phải được tham số hóa hoàn toàn \(không hard\-code quy định\)
- Mọi giao dịch tài chính phải tuân thủ chuẩn mực kế toán Việt Nam \(VAS\)
- Phiếu nhập/xuất kho phải có chữ ký điện tử hoặc ký số theo Nghị định 130/2018
- Kho phân cấp tối đa 3 tầng: Kho tổng → Kho con → Kho khoa phòng

## 7\.3 Giả Định

- Bệnh viện đã triển khai ERPNext làm nền tảng ERP chính trước khi deploy SupplyCore
- Mỗi khoa phòng có ít nhất 1 người được đào tạo sử dụng hệ thống
- Mạng nội bộ bệnh viện đảm bảo kết nối ổn định đến máy chủ ứng dụng
- Thiết bị barcode scanner/PDA tương thích với chuẩn HID keyboard emulation

─────────────────────────────────────────────────────────────────────────────

Tài liệu URS này được xây dựng dựa trên khảo sát người dùng thực tế và phải được đại diện các vai trò chính xem xét, ký xác nhận trước khi chuyển sang giai đoạn thiết kế hệ thống\.

