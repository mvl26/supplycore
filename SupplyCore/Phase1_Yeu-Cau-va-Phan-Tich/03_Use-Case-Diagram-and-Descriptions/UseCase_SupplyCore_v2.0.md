__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung Ứng Vật Tư Y Tế

__SƠ ĐỒ & MÔ TẢ TRƯỜNG HỢP SỬ DỤNG__

Use Case Diagram & Descriptions

Phiên bản: v2\.0  |  Ngày: 05/05/2026

Tài liệu: SC\-PH1\-UC\-003  |  Phase 1 – Yêu cầu & Phân tích

# __1\. THÔNG TIN TÀI LIỆU__

__Thuộc tính__

__Giá trị__

__Tên tài liệu__

Use Case Diagram & Descriptions – SupplyCore

__Mã tài liệu__

SC\-PH1\-UC\-003

__Phiên bản__

v2\.0

__Ngày tạo__

01/05/2026

__Ngày cập nhật__

05/05/2026

__Tác giả__

Business Analysis Team – SupplyCore Project

__Phê duyệt__

Project Manager / Solution Architect

__Phạm vi__

37 Use Cases – 12 nhóm module \+ System Admin

__Nền tảng__

Frappe Framework v15 \+ ERPNext v15 \(Custom App\)

__Trạng thái__

Đã phê duyệt – Phase 1 Final

# __2\. DANH SÁCH TÁC NHÂN \(ACTORS\)__

Hệ thống SupplyCore có 7 tác nhân người dùng và 3 tác nhân hệ thống như sau:

__STT__

__Actor__

__Mô tả vai trò__

__1__

__SC\-PURCHASER \(Nhân viên mua hàng\)__

Tạo và quản lý Purchase Order, liên hệ NCC, theo dõi đơn hàng

__2__

__SC\-STOREKEEPER \(Thủ kho\)__

Tiếp nhận, xuất/nhập kho, kiểm kho, quản lý vị trí lưu trữ

__3__

__SC\-WARD\-STAFF \(Nhân viên khoa phòng\)__

Tạo phiếu yêu cầu cấp phát, ghi nhận sử dụng vật tư cho bệnh nhân

__4__

__SC\-ACCOUNTANT \(Kế toán\)__

Xử lý hóa đơn, thanh toán NCC, báo cáo tài chính, quyết toán BHYT

__5__

__SC\-MANAGER \(Quản lý\)__

Phê duyệt các giao dịch quan trọng, xem báo cáo, quản lý vận hành

__6__

__SC\-EXECUTIVE \(Lãnh đạo\)__

Xem Dashboard điều hành, phê duyệt mức cao, quyết định chiến lược

__7__

__SC\-SYSADMIN \(Quản trị hệ thống\)__

Quản lý user, cấu hình hệ thống, quản lý master data

__8__

__SYSTEM \(Hệ thống\)__

Tác nhân tự động: scheduled jobs, cảnh báo, tính toán FEFO, email

__9__

__ERP\-NEXT \(Nền tảng ERPNext\)__

Xử lý nghiệp vụ chuẩn: GL, Stock Ledger, Workflow, Reports

__10__

__HIS/EMR \(Tương lai\)__

Hệ thống thông tin bệnh viện – tích hợp API \(ngoài phạm vi giai đoạn 1\)

# __3\. TỔNG HỢP USE CASE__

Hệ thống SupplyCore giai đoạn 1 bao gồm tổng cộng 37 use case, phân bổ theo 12 nhóm module:

__Mã UC__

__Tên Use Case__

__Mô\-đun__

__UC\-01__

Tìm kiếm và Đánh giá Nhà Cung Cấp

M1 – Hợp đồng & Nhà cung cấp

__UC\-02__

Thêm mới / Cập nhật Nhà Cung Cấp

M1 – Hợp đồng & Nhà cung cấp

__UC\-03__

Tạo và Quản lý Hợp Đồng Khung

M1 – Hợp đồng & Nhà cung cấp

__UC\-04__

Theo dõi Trạng thái và Gia hạn Hợp Đồng

M1 – Hợp đồng & Nhà cung cấp

__UC\-05__

Thiết lập Mức Tồn Kho Tối Thiểu / Tối Đa

M2 – Kế hoạch tồn kho & Gọi hàng

__UC\-06__

Tạo Kế Hoạch Mua Hàng Định Kỳ

M2 – Kế hoạch tồn kho & Gọi hàng

__UC\-07__

Tạo Purchase Request \(Phiếu Đề Nghị Mua Hàng\)

M2 – Kế hoạch tồn kho & Gọi hàng

__UC\-08__

Tạo và Phê duyệt Purchase Order

M2 – Kế hoạch tồn kho & Gọi hàng

__UC\-09__

Tiếp Nhận Hàng và Tạo Purchase Receipt

M3 – Tiếp nhận & Kiểm tra chất lượng

__UC\-10__

Kiểm Tra Chất Lượng \(QC\) Hàng Nhập

M3 – Tiếp nhận & Kiểm tra chất lượng

__UC\-11__

Xử Lý Hàng Trả Lại Nhà Cung Cấp

M3 – Tiếp nhận & Kiểm tra chất lượng

__UC\-12__

Quản Lý Vị Trí Lưu Kho \(Bin Management\)

M4 – WMS & PDA

__UC\-13__

Nhập / Xuất Kho bằng PDA / Barcode

M4 – WMS & PDA

__UC\-14__

Tra Cứu Tồn Kho Theo Vị Trí

M4 – WMS & PDA

__UC\-15__

Quản Lý Thông Tin Lô Hàng \(Batch Tracking\)

M5 – Lô, Hạn dùng & FEFO

__UC\-16__

Xuất Kho Theo Nguyên Tắc FEFO

M5 – Lô, Hạn dùng & FEFO

__UC\-17__

Cảnh Báo Sắp Hết Hạn Sử Dụng

M5 – Lô, Hạn dùng & FEFO

__UC\-18__

Chuyển Kho Nội Bộ \(Stock Transfer\)

M6 – Luân chuyển nội bộ

__UC\-19__

Điều Chỉnh Tồn Kho \(Stock Reconciliation\)

M6 – Luân chuyển nội bộ

__UC\-20__

Tạo Phiếu Yêu Cầu Cấp Phát Vật Tư

M7 – Cấp phát & Ghi nhận sử dụng

__UC\-21__

Xử Lý và Cấp Phát Vật Tư

M7 – Cấp phát & Ghi nhận sử dụng

__UC\-22__

Ghi Nhận Sử Dụng Vật Tư Cho Bệnh Nhân

M7 – Cấp phát & Ghi nhận sử dụng

__UC\-23__

Quản Lý Mã BHYT Cho Vật Tư

M7 – Cấp phát & Ghi nhận sử dụng

__UC\-24__

Tạo và Đối Chiếu Purchase Invoice

M8 – Kế toán & Thanh toán

__UC\-25__

Tạo Payment Entry và Theo Dõi Công Nợ

M8 – Kế toán & Thanh toán

__UC\-26__

Báo Cáo Tài Chính Vật Tư

M8 – Kế toán & Thanh toán

__UC\-27__

Lập Kế Hoạch và Thực Hiện Kiểm Kê

M9 – Kiểm kê & Đối soát

__UC\-28__

Đối Soát Tồn Kho Hệ Thống vs Thực Tế

M9 – Kiểm kê & Đối soát

__UC\-29__

Truy Xuất Nguồn Gốc Vật Tư \(Batch Trace\)

M10 – Truy xuất & Điều tra

__UC\-30__

Thu Hồi Vật Tư \(Recall Management\)

M10 – Truy xuất & Điều tra

__UC\-31__

Điều Tra Sự Cố Thất Thoát Vật Tư

M10 – Truy xuất & Điều tra

__UC\-32__

Xem Dashboard Điều Hành Tổng Thể

M11 – Dashboard & Cảnh báo điều hành

__UC\-33__

Cấu Hình và Quản Lý Cảnh Báo Tự Động

M11 – Dashboard & Cảnh báo điều hành

__UC\-34__

Xem và Xử Lý Cảnh Báo Hành Động

M11 – Dashboard & Cảnh báo điều hành

__UC\-35__

Quản Lý Người Dùng và Phân Quyền

SYS – Quản trị hệ thống

__UC\-36__

Cấu Hình Tham Số Hệ Thống

SYS – Quản trị hệ thống

__UC\-37__

Quản Lý Danh Mục Master Data

SYS – Quản trị hệ thống

# __4\. MÔ TẢ CHI TIẾT TỪNG USE CASE__

## __M1 – Hợp đồng & Nhà cung cấp__

__UC\-01 – Tìm kiếm và Đánh giá Nhà Cung Cấp__

__Mô\-đun__

M1 – Hợp đồng & Nhà cung cấp

__Mô tả__

Cho phép người dùng tìm kiếm nhà cung cấp theo nhiều tiêu chí, xem thông tin chi tiết và đánh giá năng lực cung ứng dựa trên lịch sử giao dịch\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Kế toán \(SC\-ACCOUNTANT\)

__Điều kiện tiên quyết__

• Người dùng đã đăng nhập hệ thống
• Có ít nhất một nhà cung cấp trong danh mục

__Luồng chính__

1\. Người dùng mở màn hình Quản lý Nhà cung cấp
2\. Nhập tiêu chí tìm kiếm: tên, mã số thuế, loại vật tư cung ứng, tỉnh/thành phố
3\. Hệ thống hiển thị danh sách NCC phù hợp với rating và trạng thái hợp đồng
4\. Người dùng chọn một NCC để xem chi tiết
5\. Hệ thống hiển thị: thông tin pháp lý, lịch sử PO, tỉ lệ giao hàng đúng hạn, tỉ lệ hàng đạt QC
6\. Người dùng có thể xuất báo cáo đánh giá NCC dưới dạng Excel/PDF

__Luồng thay thế__

• 4a\. Không tìm thấy NCC: Hệ thống hiển thị thông báo và gợi ý thêm mới NCC
• 6a\. Người dùng click 'Thêm vào danh sách ưu tiên' để đánh dấu NCC

__Hậu điều kiện__

• Danh sách NCC được lọc và hiển thị đúng tiêu chí
• Lịch sử tìm kiếm được lưu để tham chiếu sau

__Xử lý ngoại lệ__

• Mất kết nối mạng: Hệ thống hiển thị thông báo lỗi, dữ liệu cache vẫn xem được
• NCC bị vô hiệu hóa: Hiển thị cảnh báo trạng thái không hoạt động

__UC\-02 – Thêm mới / Cập nhật Nhà Cung Cấp__

__Mô\-đun__

M1 – Hợp đồng & Nhà cung cấp

__Mô tả__

Tạo mới hoặc cập nhật thông tin nhà cung cấp trong hệ thống, bao gồm thông tin pháp lý, tài khoản ngân hàng, điều khoản thanh toán và danh mục vật tư cung ứng\.

__Actor chính__

Kế toán \(SC\-ACCOUNTANT\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Người dùng có quyền tạo/sửa Supplier
• Có mã số thuế hợp lệ của NCC

__Luồng chính__

1\. Người dùng mở form Nhà cung cấp, chọn 'Tạo mới' hoặc chọn NCC cần cập nhật
2\. Nhập thông tin bắt buộc: Tên NCC, Mã số thuế, Địa chỉ, Số điện thoại, Email liên hệ
3\. Nhập thông tin thanh toán: Số tài khoản, Ngân hàng, Điều khoản thanh toán \(30/60/90 ngày\)
4\. Chọn loại NCC: Nhà sản xuất / Nhà phân phối / Đại lý
5\. Thêm danh mục vật tư mà NCC cung ứng \(Item Group\)
6\. Upload giấy tờ pháp lý: GPKD, Chứng chỉ ISO \(nếu có\)
7\. Nhấn Lưu; hệ thống kiểm tra trùng mã số thuế
8\. Hệ thống tạo Supplier Code tự động và lưu vào ERPNext Supplier

__Luồng thay thế__

• 7a\. Trùng mã số thuế: Hệ thống cảnh báo NCC đã tồn tại, cho phép xem hoặc merge
• 6a\. File upload > 10MB: Hệ thống từ chối và yêu cầu nén file

__Hậu điều kiện__

• NCC được tạo/cập nhật trong ERPNext
• Supplier Code được sinh tự động
• Log thay đổi được ghi vào audit trail

__Xử lý ngoại lệ__

• Lỗi validate mã số thuế: Hiển thị thông báo định dạng không hợp lệ
• Không có quyền: Hiển thị thông báo yêu cầu liên hệ admin

__UC\-03 – Tạo và Quản lý Hợp Đồng Khung__

__Mô\-đun__

M1 – Hợp đồng & Nhà cung cấp

__Mô tả__

Tạo hợp đồng khung \(Framework Contract\) với nhà cung cấp, xác định giá, điều khoản, danh mục vật tư và hạn mức theo từng giai đoạn hợp đồng\.

__Actor chính__

Kế toán \(SC\-ACCOUNTANT\), Quản lý \(SC\-MANAGER\), Lãnh đạo \(SC\-EXECUTIVE\)

__Điều kiện tiên quyết__

• NCC đã tồn tại trong hệ thống
• Người dùng có quyền tạo Framework Contract

__Luồng chính__

1\. Người dùng mở Doctype Framework Contract, chọn 'Tạo mới'
2\. Chọn Nhà cung cấp từ danh sách
3\. Nhập thông tin hợp đồng: Số hợp đồng, Ngày ký, Ngày hiệu lực, Ngày hết hạn
4\. Nhập danh mục vật tư theo hợp đồng: Mã vật tư, Đơn vị tính, Đơn giá, Số lượng tối đa
5\. Thiết lập điều khoản thanh toán và điều khoản giao hàng
6\. Gửi phê duyệt qua Workflow \(Kế toán → Quản lý → Lãnh đạo\)
7\. Sau khi được duyệt, trạng thái chuyển sang 'Có hiệu lực'
8\. Hệ thống tự động cảnh báo khi hợp đồng sắp hết hạn \(30 ngày trước\)

__Luồng thay thế__

• 6a\. Quản lý từ chối: Workflow trả về Kế toán kèm ghi chú lý do
• 4a\. Vật tư chưa có trong Item Master: Hệ thống cho phép tạo mới vật tư song song

__Hậu điều kiện__

• Hợp đồng khung được lưu và phê duyệt
• Các Release Order có thể tham chiếu hợp đồng này
• Alert được kích hoạt cho việc theo dõi hết hạn

__Xử lý ngoại lệ__

• Ngày hết hạn < Ngày hiệu lực: Hệ thống báo lỗi validate
• NCC đã bị blacklist: Hệ thống cảnh báo và yêu cầu xác nhận từ Lãnh đạo

__UC\-04 – Theo dõi Trạng thái và Gia hạn Hợp Đồng__

__Mô\-đun__

M1 – Hợp đồng & Nhà cung cấp

__Mô tả__

Theo dõi tình trạng thực hiện hợp đồng khung: tỉ lệ giải ngân, số lượng đã đặt, còn lại và thực hiện gia hạn hoặc thanh lý hợp đồng\.

__Actor chính__

Kế toán \(SC\-ACCOUNTANT\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Hợp đồng khung đã được phê duyệt và có hiệu lực

__Luồng chính__

1\. Người dùng mở Dashboard hợp đồng hoặc vào chi tiết từng Framework Contract
2\. Hệ thống hiển thị: Tổng giá trị hợp đồng, Đã sử dụng \(Release Orders\), Còn lại, % thực hiện
3\. Người dùng xem danh sách Release Order liên kết với hợp đồng
4\. Khi hợp đồng < 30 ngày hết hạn, hệ thống hiển thị cảnh báo màu đỏ
5\. Người dùng chọn 'Gia hạn': Nhập ngày hết hạn mới, lý do gia hạn
6\. Gửi phê duyệt gia hạn qua Workflow
7\. Sau duyệt, hệ thống cập nhật ngày hết hạn và lưu lịch sử thay đổi

__Luồng thay thế__

• 5a\. Chọn 'Thanh lý hợp đồng': Nhập biên bản thanh lý, đổi trạng thái sang 'Đã thanh lý'
• 4a\. Vượt hạn mức: Hệ thống block tạo Release Order mới và cảnh báo

__Hậu điều kiện__

• Trạng thái hợp đồng được cập nhật
• Lịch sử thay đổi được ghi lại đầy đủ

__Xử lý ngoại lệ__

• Hợp đồng đã hết hạn quá 90 ngày: Chỉ xem, không cho phép gia hạn retroactively

## __M2 – Kế hoạch tồn kho & Gọi hàng__

__UC\-05 – Thiết lập Mức Tồn Kho Tối Thiểu / Tối Đa__

__Mô\-đun__

M2 – Kế hoạch tồn kho & Gọi hàng

__Mô tả__

Cấu hình mức tồn kho tối thiểu \(min\), tối đa \(max\) và điểm tái đặt hàng \(reorder point\) cho từng vật tư tại từng kho\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Vật tư đã tồn tại trong Item Master
• Kho đã được thiết lập trong hệ thống

__Luồng chính__

1\. Người dùng mở Item \(vật tư\) hoặc màn hình Reorder Level
2\. Chọn vật tư và kho cần thiết lập
3\. Nhập: Mức tồn tối thiểu \(Safety Stock\), Điểm tái đặt hàng \(Reorder Level\), Mức tối đa \(Max Stock\), Số lượng đặt hàng chuẩn \(EOQ\)
4\. Thiết lập Lead Time trung bình \(ngày\) cho vật tư từ NCC
5\. Nhấn Lưu; hệ thống validate không âm và min < reorder < max
6\. Hệ thống tự động theo dõi và kích hoạt cảnh báo khi tồn kho ≤ Reorder Level

__Luồng thay thế__

• 3a\. Import hàng loạt qua Excel: Upload file template, hệ thống xử lý batch
• 5a\. Lỗi validate \(min > max\): Hiển thị thông báo lỗi cụ thể

__Hậu điều kiện__

• Ngưỡng tồn kho được lưu vào ERPNext Reorder Level
• Hệ thống bắt đầu theo dõi và cảnh báo tự động

__Xử lý ngoại lệ__

• Lead Time = 0: Hệ thống cảnh báo và yêu cầu nhập giá trị > 0

__UC\-06 – Tạo Kế Hoạch Mua Hàng Định Kỳ__

__Mô\-đun__

M2 – Kế hoạch tồn kho & Gọi hàng

__Mô tả__

Lập kế hoạch mua hàng hàng tháng/quý dựa trên lịch sử tiêu thụ, tồn kho hiện tại và dự báo nhu cầu từ các khoa phòng\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Có dữ liệu tiêu thụ ít nhất 3 tháng trước
• Mức tồn kho tối thiểu đã được thiết lập

__Luồng chính__

1\. Người dùng mở màn hình Lập kế hoạch mua hàng, chọn kỳ kế hoạch
2\. Hệ thống tự động tính toán nhu cầu dựa trên: Mức tiêu thụ trung bình 3 tháng, Tồn kho hiện tại, Đơn hàng đang chờ
3\. Hệ thống gợi ý số lượng cần mua cho từng vật tư
4\. Người dùng điều chỉnh số lượng nếu có sự kiện đặc biệt \(lễ tết, dịch bệnh\.\.\.\)
5\. Nhập ngân sách dự kiến cho kỳ kế hoạch
6\. Lưu kế hoạch và gửi phê duyệt lên Quản lý
7\. Sau phê duyệt, hệ thống có thể tự động sinh Purchase Request

__Luồng thay thế__

• 2a\. Chưa đủ dữ liệu lịch sử: Hệ thống yêu cầu nhập thủ công
• 5a\. Vượt ngân sách: Hiển thị cảnh báo đỏ, yêu cầu xác nhận

__Hậu điều kiện__

• Kế hoạch mua hàng được phê duyệt
• Purchase Request được sinh tự động \(nếu bật tính năng\)

__Xử lý ngoại lệ__

• Lỗi tính toán do dữ liệu bất thường: Hệ thống flag các vật tư cần kiểm tra thủ công

__UC\-07 – Tạo Purchase Request \(Phiếu Đề Nghị Mua Hàng\)__

__Mô\-đun__

M2 – Kế hoạch tồn kho & Gọi hàng

__Mô tả__

Tạo phiếu đề nghị mua hàng \(Material Request trong ERPNext\) khi tồn kho xuống dưới ngưỡng hoặc theo yêu cầu đột xuất từ khoa phòng\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Nhân viên khoa phòng \(SC\-WARD\-STAFF\)

__Điều kiện tiên quyết__

• Người dùng đã đăng nhập
• Vật tư cần mua đã có trong Item Master

__Luồng chính__

1\. Người dùng mở Material Request, chọn loại: 'Mua hàng' hoặc 'Đột xuất'
2\. Chọn vật tư, nhập số lượng cần mua và đơn vị tính
3\. Nhập lý do đề nghị và ngày cần giao hàng mong muốn
4\. Tham chiếu Hợp đồng Khung \(nếu có\) để lấy giá
5\. Submit form; hệ thống chuyển trạng thái sang 'Chờ phê duyệt'
6\. Quản lý nhận thông báo và duyệt/từ chối
7\. Sau khi duyệt, Kế toán tạo Purchase Order từ Material Request này

__Luồng thay thế__

• 1a\. Tồn kho ≤ Reorder Level: Hệ thống tự động tạo draft Material Request
• 6a\. Từ chối: Gửi thông báo cho người tạo kèm lý do từ chối

__Hậu điều kiện__

• Material Request được tạo và phê duyệt trong ERPNext
• Kế toán có thể tạo PO từ MR này

__Xử lý ngoại lệ__

• Vật tư không có NCC: Hệ thống cảnh báo và yêu cầu tìm NCC trước

__UC\-08 – Tạo và Phê duyệt Purchase Order__

__Mô\-đun__

M2 – Kế hoạch tồn kho & Gọi hàng

__Mô tả__

Tạo đơn đặt hàng chính thức \(Purchase Order\) gửi NCC, liên kết với Material Request và Hợp đồng Khung, qua quy trình phê duyệt theo giá trị đơn hàng\.

__Actor chính__

Kế toán \(SC\-ACCOUNTANT\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Material Request đã được phê duyệt
• NCC đã được chọn
• Hợp đồng khung còn hiệu lực \(nếu có\)

__Luồng chính__

1\. Kế toán mở Purchase Order, chọn 'Tạo từ Material Request'
2\. Chọn NCC; hệ thống tự động load giá từ Hợp đồng Khung hoặc Supplier Quotation
3\. Kiểm tra và điều chỉnh số lượng, đơn giá, điều khoản giao hàng
4\. Hệ thống tính tổng giá trị đơn hàng và kiểm tra hạn mức hợp đồng
5\. Submit PO; workflow kích hoạt theo giá trị: <50tr \(Quản lý\), ≥50tr \(Lãnh đạo\)
6\. Người duyệt xem xét và phê duyệt/từ chối
7\. Sau duyệt, hệ thống tự động gửi PO qua email đến NCC
8\. PO chuyển trạng thái 'Đã gửi NCC', chờ xác nhận giao hàng

__Luồng thay thế__

• 2a\. Không có hợp đồng khung: Nhập giá thủ công và đính kèm báo giá
• 4a\. Vượt hạn mức hợp đồng: Hệ thống block và yêu cầu gia hạn/tạo hợp đồng mới

__Hậu điều kiện__

• PO được tạo và gửi NCC trong ERPNext
• Release Order được cập nhật số lượng đã đặt
• Thông báo được gửi đến NCC qua email

__Xử lý ngoại lệ__

• NCC không phản hồi sau 3 ngày: Hệ thống nhắc nhở tự động
• Giá NCC khác giá hợp đồng: Hệ thống flag để xem xét

## __M3 – Tiếp nhận & Kiểm tra chất lượng__

__UC\-09 – Tiếp Nhận Hàng và Tạo Purchase Receipt__

__Mô\-đun__

M3 – Tiếp nhận & Kiểm tra chất lượng

__Mô tả__

Ghi nhận việc nhận hàng từ NCC, đối chiếu với Purchase Order, kiểm tra số lượng và tạo Purchase Receipt trong hệ thống\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\)

__Điều kiện tiên quyết__

• Purchase Order đã được phê duyệt và gửi NCC
• Hàng hóa đã được NCC giao đến kho

__Luồng chính__

1\. Thủ kho mở Purchase Receipt, chọn 'Tạo từ Purchase Order'
2\. Chọn PO tương ứng; hệ thống load danh sách vật tư từ PO
3\. Nhập số lượng thực tế nhận được cho từng vật tư
4\. Nhập thông tin lô hàng: Số lô \(Batch No\), Ngày sản xuất, Hạn sử dụng
5\. Chọn vị trí lưu kho \(Bin/Location trong warehouse\)
6\. Đính kèm phiếu giao hàng của NCC \(scan hoặc upload\)
7\. Submit; hệ thống cập nhật tồn kho và tạo Stock Ledger Entry
8\. Nếu nhận thiếu: Tạo 'Backorder' cho phần còn lại

__Luồng thay thế__

• 3a\. Số lượng nhận > PO: Hệ thống cảnh báo, yêu cầu xác nhận Quản lý
• 8a\. Nhận đủ 100%: Hệ thống đổi trạng thái PO sang 'Hoàn thành'

__Hậu điều kiện__

• Purchase Receipt được tạo
• Tồn kho tăng tương ứng
• Stock Ledger Entry được ghi

__Xử lý ngoại lệ__

• Không tìm thấy PO: Hệ thống cho phép tạo receipt không có PO với ghi chú lý do

__UC\-10 – Kiểm Tra Chất Lượng \(QC\) Hàng Nhập__

__Mô\-đun__

M3 – Tiếp nhận & Kiểm tra chất lượng

__Mô tả__

Thực hiện kiểm tra chất lượng cơ bản khi nhận hàng: kiểm tra quy cách, bao bì, hạn sử dụng, số lô và ghi nhận kết quả QC\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Purchase Receipt đã được tạo
• Hàng đang ở trạng thái 'Chờ QC'

__Luồng chính__

1\. Thủ kho mở Quality Inspection từ Purchase Receipt
2\. Hệ thống hiển thị checklist QC cho loại vật tư
3\. Kiểm tra và ghi nhận từng tiêu chí: Bao bì nguyên vẹn, Nhãn mác đúng, Hạn dùng đủ \(≥6 tháng\), Số lô khớp chứng từ, Quy cách đúng hợp đồng
4\. Nhập kết quả: Đạt / Không đạt cho từng tiêu chí
5\. Nếu tất cả Đạt: QC Pass, hàng được nhập kho chính thức
6\. Nếu có tiêu chí Không đạt: Chọn xử lý: Trả hàng NCC / Yêu cầu đổi trả / Chấp nhận có điều kiện

__Luồng thay thế__

• 5a\. QC Pass: Cập nhật Purchase Receipt sang 'Đã nhập kho'
• 6a\. Trả hàng: Tạo Supplier Return, cập nhật tồn kho giảm

__Hậu điều kiện__

• Kết quả QC được lưu vào Quality Inspection
• Hàng đạt được nhập kho chính thức
• Hàng không đạt được xử lý theo quyết định

__Xử lý ngoại lệ__

• Thiếu thiết bị kiểm tra: Ghi chú và để trạng thái 'Chờ xử lý'

__UC\-11 – Xử Lý Hàng Trả Lại Nhà Cung Cấp__

__Mô\-đun__

M3 – Tiếp nhận & Kiểm tra chất lượng

__Mô tả__

Thực hiện quy trình trả hàng không đạt chất lượng hoặc nhầm hàng cho NCC, tạo Supplier Return và theo dõi hoàn tiền/đổi hàng\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Kế toán \(SC\-ACCOUNTANT\)

__Điều kiện tiên quyết__

• QC Fail đã được ghi nhận
• Có Purchase Receipt liên quan

__Luồng chính__

1\. Kế toán mở Purchase Return \(Debit Note\), chọn 'Từ Purchase Receipt'
2\. Chọn vật tư cần trả, nhập số lượng và lý do trả hàng
3\. Hệ thống tính giá trị hoàn trả dựa trên đơn giá trong PO
4\. Submit; hệ thống tạo Stock Entry giảm kho và Debit Note
5\. Gửi thông báo trả hàng đến NCC qua email
6\. Theo dõi trạng thái: Chờ NCC xác nhận → Đã đổi hàng / Đã hoàn tiền
7\. Khi nhận hàng đổi: Tạo Purchase Receipt mới liên kết Return

__Luồng thay thế__

• 6a\. NCC hoàn tiền: Kế toán tạo Credit Note và điều chỉnh công nợ
• 6b\. NCC đổi hàng: Quy trình nhận hàng bình thường \(UC\-09, UC\-10\)

__Hậu điều kiện__

• Return được ghi nhận, tồn kho giảm
• Debit Note được tạo
• Công nợ NCC được điều chỉnh

__Xử lý ngoại lệ__

• NCC không phản hồi: Escalate lên Quản lý sau 7 ngày

## __M4 – WMS & PDA__

__UC\-12 – Quản Lý Vị Trí Lưu Kho \(Bin Management\)__

__Mô\-đun__

M4 – WMS & PDA

__Mô tả__

Thiết lập và quản lý cấu trúc vị trí lưu kho theo 3 cấp: Kho tổng → Kho con → Kho khoa phòng, quản lý bin/shelf location cho từng vật tư\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\)

__Điều kiện tiên quyết__

• Warehouse structure đã được thiết lập trong ERPNext

__Luồng chính__

1\. Thủ kho mở Warehouse / Bin Management
2\. Xem sơ đồ kho phân cấp: Kho tổng → Kho con → Kho khoa phòng
3\. Thêm/sửa bin: Nhập mã bin, vị trí \(Row\-Shelf\-Level\), sức chứa tối đa
4\. Gán vật tư vào bin mặc định \(suggested bin\) hoặc thủ công
5\. Xem tình trạng sử dụng bin: Đang dùng / Trống / Đầy
6\. In nhãn barcode cho từng bin
7\. Cấu hình putaway rules: Vật tư theo nhóm → Bin tương ứng

__Luồng thay thế__

• 3a\. Bin đã đầy: Hệ thống gợi ý bin thay thế gần nhất
• 4a\. Vật tư chưa có bin mặc định: Hệ thống gợi ý dựa trên Item Group

__Hậu điều kiện__

• Cấu trúc kho được cập nhật
• Putaway rules được áp dụng cho lần nhập kho tiếp theo

__Xử lý ngoại lệ__

• Xóa bin đang có hàng: Hệ thống block và yêu cầu chuyển hàng trước

__UC\-13 – Nhập / Xuất Kho bằng PDA / Barcode__

__Mô\-đun__

M4 – WMS & PDA

__Mô tả__

Sử dụng thiết bị PDA hoặc điện thoại quét barcode để thực hiện nhập/xuất kho nhanh, đồng bộ real\-time với hệ thống\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\)

__Điều kiện tiên quyết__

• Thiết bị PDA/điện thoại có ứng dụng quét barcode
• Kết nối WiFi với hệ thống

__Luồng chính__

1\. Thủ kho mở ứng dụng PDA hoặc giao diện mobile của SupplyCore
2\. Chọn chức năng: Nhập kho / Xuất kho / Kiểm kho
3\. Quét barcode/QR của bin destination
4\. Quét barcode vật tư; hệ thống tự động nhận dạng Item Code
5\. Nhập hoặc xác nhận số lượng
6\. Quét barcode lô hàng \(nếu có\) để liên kết Batch
7\. Xác nhận giao dịch; hệ thống đồng bộ ngay lập tức vào Stock Ledger

__Luồng thay thế__

• 4a\. Barcode không nhận dạng được: Nhập mã thủ công hoặc tìm kiếm
• 7a\. Mất kết nối: Lưu offline, đồng bộ khi có kết nối lại

__Hậu điều kiện__

• Stock Ledger Entry được tạo real\-time
• Tồn kho tại bin được cập nhật

__Xử lý ngoại lệ__

• Pin PDA hết: Chuyển sang nhập thủ công trên máy tính, đồng bộ sau

__UC\-14 – Tra Cứu Tồn Kho Theo Vị Trí__

__Mô\-đun__

M4 – WMS & PDA

__Mô tả__

Tra cứu tồn kho hiện tại theo vật tư, kho, vị trí bin, lô hàng để phục vụ cấp phát, kiểm kê và lập kế hoạch\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Quản lý \(SC\-MANAGER\), Nhân viên khoa phòng \(SC\-WARD\-STAFF\)

__Điều kiện tiên quyết__

• Có dữ liệu tồn kho trong hệ thống

__Luồng chính__

1\. Người dùng mở Stock Balance hoặc Bin Wise Balance Report
2\. Lọc theo: Kho, Vật tư, Nhóm vật tư, Lô hàng, Hạn dùng
3\. Hệ thống hiển thị tồn kho: Số lượng, Giá trị, Vị trí bin, Lô, Hạn dùng
4\. Xem chi tiết từng bin: Lịch sử nhập xuất gần nhất
5\. Xuất báo cáo Excel hoặc in danh sách tồn kho

__Luồng thay thế__

• 2a\. Lọc theo ngày: Xem tồn kho tại một thời điểm trong quá khứ
• 5a\. Tồn kho âm: Hệ thống highlight đỏ để điều tra

__Hậu điều kiện__

• Báo cáo tồn kho được hiển thị chính xác

__Xử lý ngoại lệ__

• Dữ liệu không đồng bộ: Cần chạy lại Stock Ledger Reconciliation

## __M5 – Lô, Hạn dùng & FEFO__

__UC\-15 – Quản Lý Thông Tin Lô Hàng \(Batch Tracking\)__

__Mô\-đun__

M5 – Lô, Hạn dùng & FEFO

__Mô tả__

Tạo và quản lý thông tin lô hàng \(Batch\) cho vật tư có hạn sử dụng, bao gồm số lô, ngày sản xuất, hạn dùng và nhà sản xuất\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\)

__Điều kiện tiên quyết__

• Vật tư được cấu hình 'Has Batch No = Yes' trong Item Master

__Luồng chính__

1\. Khi nhập kho \(UC\-09\), hệ thống yêu cầu nhập thông tin lô
2\. Nhập: Số lô nhà sản xuất, Ngày sản xuất, Hạn sử dụng, Nhà sản xuất
3\. Hệ thống sinh Batch ID nội bộ theo format: \[ItemCode\]\-\[YYYYMM\]\-\[Seq\]
4\. In nhãn lô: Barcode chứa Batch ID, Hạn dùng
5\. Xem danh sách lô đang có trong kho theo vật tư
6\. Tra cứu lô theo số lô nhà sản xuất hoặc Batch ID nội bộ

__Luồng thay thế__

• 3a\. Số lô đã tồn tại: Hệ thống cảnh báo trùng, cho phép merge hoặc tạo mới
• 4a\. Hạn dùng < 6 tháng: Hệ thống cảnh báo màu đỏ và yêu cầu xác nhận nhập kho

__Hậu điều kiện__

• Batch được tạo và liên kết với Stock Entry
• Nhãn lô sẵn sàng để in

__Xử lý ngoại lệ__

• Nhập hạn dùng sai định dạng: Hệ thống validate DD/MM/YYYY

__UC\-16 – Xuất Kho Theo Nguyên Tắc FEFO__

__Mô\-đun__

M5 – Lô, Hạn dùng & FEFO

__Mô tả__

Hệ thống tự động gợi ý lô hàng cần xuất kho theo nguyên tắc FEFO \(First Expired First Out\) khi thực hiện cấp phát hoặc xuất kho\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Hệ thống \(SYSTEM\)

__Điều kiện tiên quyết__

• Vật tư có multiple batches trong kho
• Tất cả batch đã có thông tin hạn dùng

__Luồng chính__

1\. Thủ kho tạo yêu cầu xuất kho hoặc cấp phát cho vật tư
2\. Hệ thống tự động tính toán và gợi ý batch theo FEFO: Batch gần hết hạn nhất được xuất trước
3\. Hiển thị danh sách batch được gợi ý: Batch ID, Hạn dùng, Số lượng sẵn có
4\. Thủ kho xác nhận hoặc thay đổi batch \(cần ghi lý do nếu không theo FEFO\)
5\. Hệ thống ghi nhận giao dịch và cập nhật tồn kho theo từng batch

__Luồng thay thế__

• 4a\. Không theo FEFO: Log audit trail với lý do, cần xác nhận Quản lý
• 2a\. Chỉ có 1 batch: Bỏ qua bước gợi ý, tự động chọn batch duy nhất

__Hậu điều kiện__

• Tồn kho batch được cập nhật đúng FEFO
• Audit trail ghi nhận mọi lệnh xuất

__Xử lý ngoại lệ__

• Batch hết hàng giữa chừng: Tự động chuyển sang batch tiếp theo

__UC\-17 – Cảnh Báo Sắp Hết Hạn Sử Dụng__

__Mô\-đun__

M5 – Lô, Hạn dùng & FEFO

__Mô tả__

Hệ thống tự động phát cảnh báo và thông báo cho vật tư có hạn sử dụng sắp hết theo các ngưỡng cấu hình được\.

__Actor chính__

Hệ thống \(SYSTEM\), Quản lý \(SC\-MANAGER\), Thủ kho \(SC\-STOREKEEPER\)

__Điều kiện tiên quyết__

• Batch tracking được bật
• Email/notification đã cấu hình trong hệ thống

__Luồng chính__

1\. Hàng ngày, hệ thống chạy scheduled job kiểm tra hạn dùng của tất cả batch đang có hàng
2\. Phân loại cảnh báo: Đỏ \(< 30 ngày\), Vàng \(30–90 ngày\), Xanh \(> 90 ngày\)
3\. Hệ thống gửi email/notification đến Thủ kho và Quản lý theo danh sách cấu hình
4\. Dashboard hiển thị widget 'Vật tư sắp hết hạn' với bộ lọc theo kho
5\. Thủ kho xem chi tiết và lên kế hoạch xử lý: ưu tiên cấp phát, trả NCC, hoặc hủy

__Luồng thay thế__

• 5a\. Hủy batch hết hạn: Tạo Stock Entry loại 'Material Issue' với lý do 'Expired'
• 5b\. Cấp phát ưu tiên: Gắn batch vào lệnh cấp phát tiếp theo

__Hậu điều kiện__

• Cảnh báo được gửi đúng đối tượng
• Dashboard được cập nhật real\-time

__Xử lý ngoại lệ__

• Email server lỗi: Lưu notification trong hệ thống, gửi lại khi email hoạt động

## __M6 – Luân chuyển nội bộ__

__UC\-18 – Chuyển Kho Nội Bộ \(Stock Transfer\)__

__Mô\-đun__

M6 – Luân chuyển nội bộ

__Mô tả__

Thực hiện chuyển vật tư giữa các kho nội bộ: từ Kho tổng xuống Kho con, hoặc giữa các Kho khoa phòng, có kiểm soát phê duyệt\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Vật tư có tồn kho đủ tại kho nguồn
• Kho đích đã tồn tại trong hệ thống

__Luồng chính__

1\. Thủ kho tạo Stock Entry loại 'Material Transfer'
2\. Chọn kho nguồn và kho đích
3\. Thêm danh sách vật tư: Mã, Số lượng, Batch \(nếu có\)
4\. Hệ thống kiểm tra tồn kho tại kho nguồn đủ để chuyển
5\. Submit; nếu chuyển qua kho khoa phòng: cần phê duyệt Quản lý
6\. Sau phê duyệt: Stock Entry được submit, tồn kho kho nguồn giảm, kho đích tăng
7\. In phiếu chuyển kho để đi kèm hàng hóa

__Luồng thay thế__

• 4a\. Tồn kho không đủ: Hệ thống báo lỗi, hiển thị số lượng tối đa có thể chuyển
• 5a\. Chuyển kho trong cùng warehouse \(sub\-location\): Không cần phê duyệt

__Hậu điều kiện__

• Tồn kho được cập nhật tại cả 2 kho
• Stock Ledger Entry được ghi đầy đủ

__Xử lý ngoại lệ__

• Chuyển kho bị lỗi giữa chừng: Rollback và thông báo lỗi

__UC\-19 – Điều Chỉnh Tồn Kho \(Stock Reconciliation\)__

__Mô\-đun__

M6 – Luân chuyển nội bộ

__Mô tả__

Điều chỉnh tồn kho thực tế so với hệ thống sau kiểm kê hoặc phát hiện sai lệch, tạo chứng từ điều chỉnh và ghi nhận vào kế toán\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Quản lý \(SC\-MANAGER\), Kế toán \(SC\-ACCOUNTANT\)

__Điều kiện tiên quyết__

• Có biên bản kiểm kê hoặc phát hiện sai lệch tồn kho

__Luồng chính__

1\. Thủ kho mở Stock Reconciliation trong ERPNext
2\. Chọn kho và ngày điều chỉnh
3\. Upload hoặc nhập danh sách vật tư: Tồn kho hệ thống vs Tồn kho thực tế
4\. Hệ thống tính chênh lệch \(\+/\-\) và giá trị điều chỉnh tương ứng
5\. Nhập lý do điều chỉnh cho từng dòng có chênh lệch
6\. Submit; Quản lý xem xét và phê duyệt
7\. Sau phê duyệt: Hệ thống tạo Accounting Entry điều chỉnh giá trị tồn kho

__Luồng thay thế__

• 3a\. Import từ file kiểm kê: Upload Excel template đã điền
• 6a\. Từ chối: Trả về Thủ kho kèm ghi chú

__Hậu điều kiện__

• Tồn kho hệ thống khớp thực tế
• GL Entry được tạo tự động
• Biên bản điều chỉnh được lưu

__Xử lý ngoại lệ__

• Điều chỉnh âm vượt tồn kho: Hệ thống block, yêu cầu kiểm tra lại

## __M7 – Cấp phát & Ghi nhận sử dụng__

__UC\-20 – Tạo Phiếu Yêu Cầu Cấp Phát Vật Tư__

__Mô\-đun__

M7 – Cấp phát & Ghi nhận sử dụng

__Mô tả__

Nhân viên khoa phòng tạo phiếu yêu cầu lĩnh vật tư từ kho để phục vụ hoạt động chuyên môn hoặc theo dõi sử dụng cho bệnh nhân cụ thể\.

__Actor chính__

Nhân viên khoa phòng \(SC\-WARD\-STAFF\)

__Điều kiện tiên quyết__

• Nhân viên đã đăng nhập
• Vật tư cần lĩnh đang có trong kho

__Luồng chính__

1\. Nhân viên khoa phòng mở màn hình 'Yêu cầu cấp phát'
2\. Chọn khoa phòng của mình \(tự động từ user profile\)
3\. Thêm vật tư cần lĩnh: Tìm kiếm theo tên/mã, nhập số lượng
4\. Tùy chọn: Gắn yêu cầu với bệnh nhân \(nhập mã bệnh nhân/mã BHYT\)
5\. Nhập lý do yêu cầu và ngày cần
6\. Submit; hệ thống gửi yêu cầu đến Thủ kho để xử lý
7\. Nhân viên theo dõi trạng thái yêu cầu: Chờ xử lý / Đang chuẩn bị / Đã cấp phát

__Luồng thay thế__

• 3a\. Vật tư hết hàng: Hệ thống thông báo và gợi ý vật tư thay thế
• 4a\. Không gắn bệnh nhân: Cấp phát cho khoa, không theo dõi từng BN

__Hậu điều kiện__

• Phiếu yêu cầu được tạo và gửi đến Thủ kho
• Nhân viên nhận được confirmation

__Xử lý ngoại lệ__

• Khoa phòng vượt hạn mức cấp phát tháng: Cảnh báo, cần phê duyệt đặc biệt

__UC\-21 – Xử Lý và Cấp Phát Vật Tư__

__Mô\-đun__

M7 – Cấp phát & Ghi nhận sử dụng

__Mô tả__

Thủ kho xử lý phiếu yêu cầu cấp phát, chuẩn bị và xuất vật tư cho khoa phòng theo FEFO, ghi nhận vào hệ thống\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\)

__Điều kiện tiên quyết__

• Phiếu yêu cầu cấp phát đã được tạo \(UC\-20\)
• Vật tư có đủ tồn kho

__Luồng chính__

1\. Thủ kho mở danh sách phiếu yêu cầu chờ xử lý
2\. Chọn phiếu, xem chi tiết yêu cầu
3\. Hệ thống tự động gợi ý batch theo FEFO cho từng vật tư
4\. Thủ kho xác nhận số lượng cấp và batch
5\. Tạo Stock Entry loại 'Material Issue' \(Phiếu Cấp Phát\)
6\. In phiếu cấp phát có barcode để đi kèm vật tư
7\. Submit; hệ thống giảm tồn kho và cập nhật Stock Ledger
8\. Gửi notification đến khoa phòng: vật tư đã sẵn sàng

__Luồng thay thế__

• 4a\. Một số vật tư hết hàng: Cấp phát partial, ghi chú phần thiếu
• 3a\. Override FEFO: Ghi lý do, cần xác nhận Quản lý

__Hậu điều kiện__

• Vật tư được xuất kho chính xác
• Phiếu cấp phát được in và lưu hệ thống
• Tồn kho được cập nhật

__Xử lý ngoại lệ__

• Tồn kho hệ thống ≠ tồn kho thực: Dừng cấp phát, tạo phiếu điều chỉnh trước

__UC\-22 – Ghi Nhận Sử Dụng Vật Tư Cho Bệnh Nhân__

__Mô\-đun__

M7 – Cấp phát & Ghi nhận sử dụng

__Mô tả__

Nhân viên khoa phòng ghi nhận vật tư đã thực sự sử dụng cho từng bệnh nhân sau khi đã nhận cấp phát, phục vụ tính toán chi phí và quyết toán BHYT\.

__Actor chính__

Nhân viên khoa phòng \(SC\-WARD\-STAFF\)

__Điều kiện tiên quyết__

• Vật tư đã được cấp phát cho khoa
• Bệnh nhân đang điều trị có mã trong hệ thống

__Luồng chính__

1\. Nhân viên mở màn hình 'Ghi nhận sử dụng' hoặc Phiếu Cấp Phát Bệnh Nhân
2\. Chọn bệnh nhân \(nhập mã BN hoặc quét thẻ BHYT\)
3\. Chọn vật tư từ danh sách đã cấp phát cho khoa
4\. Nhập số lượng thực tế đã sử dụng cho BN
5\. Hệ thống tự động tra cứu mã BHYT \(N01–N09\) của vật tư
6\. Lưu; hệ thống tính chi phí: Phần BHYT chi trả \+ Phần BN tự trả
7\. Tổng hợp chi phí vật tư vào hồ sơ bệnh nhân cho quyết toán

__Luồng thay thế__

• 3a\. Vật tư không có mã BHYT: Ghi nhận là vật tư ngoài BHYT, BN tự trả 100%
• 2a\. Bệnh nhân không có thẻ BHYT: Ghi nhận chi phí tự trả toàn bộ

__Hậu điều kiện__

• Chi phí vật tư được ghi vào hồ sơ BN
• Dữ liệu sẵn sàng cho quyết toán BHYT

__Xử lý ngoại lệ__

• Mã BHYT thay đổi quy định: Hệ thống cảnh báo, cần cập nhật cấu hình trước khi tiếp tục

__UC\-23 – Quản Lý Mã BHYT Cho Vật Tư__

__Mô\-đun__

M7 – Cấp phát & Ghi nhận sử dụng

__Mô tả__

Cấu hình và cập nhật mã BHYT \(nhóm N01–N09 theo Thông tư Bộ Y tế\) cho từng vật tư, hỗ trợ tính toán chi phí BHYT tự động\.

__Actor chính__

Quản lý \(SC\-MANAGER\), Kế toán \(SC\-ACCOUNTANT\)

__Điều kiện tiên quyết__

• Vật tư đã có trong Item Master
• Có văn bản quy định BHYT hiện hành

__Luồng chính__

1\. Quản lý mở màn hình cấu hình Mã BHYT
2\. Tìm kiếm vật tư theo tên hoặc mã vật tư
3\. Xem danh sách mã BHYT hiện tại của vật tư \(có thể có 1\-N mã\)
4\. Thêm/sửa mã BHYT: Nhóm \(N01–N09\), Tỉ lệ thanh toán BHYT \(%\), Hiệu lực từ ngày
5\. Hệ thống lưu lịch sử thay đổi để audit
6\. Khi quy định thay đổi: Chỉ cần cập nhật cấu hình, không cần sửa code
7\. Batch update: Upload file Excel để cập nhật hàng loạt

__Luồng thay thế__

• 4a\. Mã BHYT chưa có trong danh mục: Thêm mới vào bảng danh mục BHYT
• 7a\. Import lỗi: Hệ thống báo cáo dòng lỗi và tiếp tục dòng hợp lệ

__Hậu điều kiện__

• Mã BHYT được cập nhật và có hiệu lực từ ngày chỉ định
• Lịch sử thay đổi được lưu đầy đủ

__Xử lý ngoại lệ__

• Tỉ lệ > 100%: Hệ thống validate và báo lỗi

## __M8 – Kế toán & Thanh toán__

__UC\-24 – Tạo và Đối Chiếu Purchase Invoice__

__Mô\-đun__

M8 – Kế toán & Thanh toán

__Mô tả__

Nhận hóa đơn từ NCC, tạo Purchase Invoice trong hệ thống và đối chiếu với Purchase Receipt và Hợp đồng Khung để xác nhận thanh toán\.

__Actor chính__

Kế toán \(SC\-ACCOUNTANT\)

__Điều kiện tiên quyết__

• Purchase Receipt đã được tạo và đã nhập kho
• Nhận được hóa đơn từ NCC

__Luồng chính__

1\. Kế toán mở Purchase Invoice, chọn 'Tạo từ Purchase Receipt'
2\. Hệ thống tự động load thông tin: Vật tư, Số lượng, Đơn giá từ PO
3\. Nhập thông tin hóa đơn NCC: Số hóa đơn, Ngày xuất, Tổng tiền
4\. Hệ thống đối chiếu 3 chiều: Hóa đơn vs PO vs Receipt
5\. Nếu khớp \(3\-way match\): Hiển thị xanh, tự động approve
6\. Nếu chênh lệch: Highlight đỏ, yêu cầu giải trình
7\. Submit Invoice; hệ thống tạo GL Entry và cập nhật công nợ NCC

__Luồng thay thế__

• 5a\. Chênh lệch nhỏ \(≤1%\): Hệ thống gợi ý 'Accept với điều chỉnh'
• 6a\. Chênh lệch lớn: Escalate lên Quản lý, tạm hold thanh toán

__Hậu điều kiện__

• Purchase Invoice được tạo và submit
• GL Entry được ghi tự động
• Công nợ NCC được cập nhật

__Xử lý ngoại lệ__

• Hóa đơn trùng số: Hệ thống cảnh báo duplicate

__UC\-25 – Tạo Payment Entry và Theo Dõi Công Nợ__

__Mô\-đun__

M8 – Kế toán & Thanh toán

__Mô tả__

Thực hiện thanh toán cho NCC, tạo Payment Entry, đối chiếu với Purchase Invoice và theo dõi công nợ còn lại\.

__Actor chính__

Kế toán \(SC\-ACCOUNTANT\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Purchase Invoice đã được submit
• Có kế hoạch thanh toán trong kỳ

__Luồng chính__

1\. Kế toán mở Payment Entry, chọn loại 'Pay' và NCC
2\. Chọn hóa đơn cần thanh toán từ danh sách outstanding
3\. Nhập số tiền thanh toán, ngày thanh toán, tài khoản ngân hàng
4\. Tham chiếu số chứng từ chuyển khoản ngân hàng
5\. Submit; Quản lý phê duyệt nếu giá trị ≥ mức giới hạn cấu hình
6\. Hệ thống tạo GL Entry: Ghi nợ tài khoản NCC, Ghi có tài khoản ngân hàng
7\. Invoice được đánh dấu 'Đã thanh toán' hoặc 'Thanh toán một phần'

__Luồng thay thế__

• 3a\. Thanh toán partial: Nhập số tiền < tổng hóa đơn, ghi chú lý do
• 5a\. Vượt hạn mức: Cần phê duyệt Lãnh đạo

__Hậu điều kiện__

• Payment Entry được ghi nhận
• Công nợ NCC được giảm
• GL Entry cân bằng

__Xử lý ngoại lệ__

• Số dư tài khoản ngân hàng không đủ: Hệ thống cảnh báo nhưng vẫn cho phép submit

__UC\-26 – Báo Cáo Tài Chính Vật Tư__

__Mô\-đun__

M8 – Kế toán & Thanh toán

__Mô tả__

Xem và xuất các báo cáo tài chính liên quan đến vật tư: Giá trị tồn kho, Chi phí vật tư theo kỳ, Công nợ NCC, Báo cáo quyết toán BHYT\.

__Actor chính__

Kế toán \(SC\-ACCOUNTANT\), Quản lý \(SC\-MANAGER\), Lãnh đạo \(SC\-EXECUTIVE\)

__Điều kiện tiên quyết__

• Có dữ liệu giao dịch trong kỳ cần báo cáo

__Luồng chính__

1\. Người dùng mở mục Reports hoặc Dashboard tài chính
2\. Chọn loại báo cáo: Tồn kho / Công nợ NCC / Chi phí vật tư / BHYT
3\. Thiết lập bộ lọc: Kỳ báo cáo, Kho, Nhóm vật tư, NCC
4\. Hệ thống tổng hợp dữ liệu từ GL Entry và Stock Ledger
5\. Hiển thị báo cáo với biểu đồ và bảng số liệu
6\. Xuất Excel / PDF hoặc print

__Luồng thay thế__

• 2a\. Báo cáo BHYT: Tổng hợp chi phí vật tư theo mã nhóm N01–N09 và khoa phòng
• 5a\. Drill\-down: Click vào số liệu để xem chi tiết giao dịch gốc

__Hậu điều kiện__

• Báo cáo được xuất đúng kỳ và bộ lọc yêu cầu

__Xử lý ngoại lệ__

• Dữ liệu chưa được close kỳ: Cảnh báo báo cáo tạm thời, chưa finalized

## __M9 – Kiểm kê & Đối soát__

__UC\-27 – Lập Kế Hoạch và Thực Hiện Kiểm Kê__

__Mô\-đun__

M9 – Kiểm kê & Đối soát

__Mô tả__

Lập lịch kiểm kê định kỳ hoặc đột xuất, phân công nhân sự, in phiếu kiểm kê và ghi nhận kết quả đếm thực tế vào hệ thống\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Người dùng có quyền tạo Stock Count / Physical Inventory

__Luồng chính__

1\. Quản lý tạo lịch kiểm kê: Chọn kho, ngày kiểm kê, phạm vi \(toàn bộ / theo nhóm\)
2\. Hệ thống in phiếu kiểm kê: Danh sách vật tư, vị trí bin, tồn kho hệ thống \(ẩn đi\)
3\. Thủ kho thực hiện đếm thực tế, nhập số lượng vào phiếu
4\. Nhập kết quả đếm vào hệ thống \(thủ công hoặc qua PDA scan\)
5\. Hệ thống tính chênh lệch: Thực tế \- Hệ thống
6\. Đếm lại các dòng chênh lệch > ngưỡng \(ví dụ > 5%\)
7\. Hoàn tất kiểm kê, submit để tạo Stock Reconciliation \(UC\-19\)

__Luồng thay thế__

• 4a\. Kiểm kê bằng PDA: Quét barcode tại bin, nhập số lượng trực tiếp
• 6a\. Chênh lệch lớn: Đếm lần 3 với sự chứng kiến của Quản lý

__Hậu điều kiện__

• Kết quả kiểm kê được lưu
• Biên bản kiểm kê được in và ký duyệt
• Sẵn sàng tạo Stock Reconciliation

__Xử lý ngoại lệ__

• Kiểm kê bị gián đoạn: Lưu partial kết quả, tiếp tục sau

__UC\-28 – Đối Soát Tồn Kho Hệ Thống vs Thực Tế__

__Mô\-đun__

M9 – Kiểm kê & Đối soát

__Mô tả__

Phân tích nguyên nhân chênh lệch sau kiểm kê, lập biên bản giải trình và thực hiện điều chỉnh tồn kho kế toán\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Kế toán \(SC\-ACCOUNTANT\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Kết quả kiểm kê đã được nhập \(UC\-27\)
• Có chênh lệch cần xử lý

__Luồng chính__

1\. Kế toán mở báo cáo đối soát kiểm kê
2\. Xem danh sách chênh lệch: Dư/Thiếu, Số lượng, Giá trị
3\. Phân tích nguyên nhân: Thất thoát, Nhập liệu sai, Phát sinh chưa ghi
4\. Ghi chú nguyên nhân cho từng dòng chênh lệch
5\. Lập biên bản đối soát với chữ ký xác nhận
6\. Tạo Stock Reconciliation để điều chỉnh hệ thống
7\. Submit; Kế toán trưởng phê duyệt và tạo GL Entry điều chỉnh

__Luồng thay thế__

• 3a\. Phát hiện hàng không có trong danh sách: Ghi nhận hàng thừa và điều tra nguồn gốc
• 6a\. Chênh lệch do lỗi hệ thống: Tạo phiếu điều chỉnh với ghi chú đặc biệt

__Hậu điều kiện__

• Tồn kho hệ thống được điều chỉnh về đúng thực tế
• Biên bản được lưu trữ cho audit

__Xử lý ngoại lệ__

• Chênh lệch giá trị lớn \(>10tr\): Yêu cầu điều tra nội bộ trước khi điều chỉnh

## __M10 – Truy xuất & Điều tra__

__UC\-29 – Truy Xuất Nguồn Gốc Vật Tư \(Batch Trace\)__

__Mô\-đun__

M10 – Truy xuất & Điều tra

__Mô tả__

Truy xuất toàn bộ lịch sử vòng đời của một lô vật tư: từ nhập kho \(NCC, ngày, PO\) đến cấp phát \(khoa phòng, bệnh nhân, ngày\)\.

__Actor chính__

Quản lý \(SC\-MANAGER\), Thủ kho \(SC\-STOREKEEPER\)

__Điều kiện tiên quyết__

• Vật tư đã được nhập kho với thông tin Batch đầy đủ

__Luồng chính__

1\. Người dùng mở chức năng Batch Traceability
2\. Nhập Batch ID hoặc số lô nhà sản xuất
3\. Hệ thống hiển thị toàn bộ chuỗi cung ứng:
4\.   \- Nguồn gốc: NCC, PO số, ngày nhập, QC result
5\.   \- Nhập kho: Kho nào, bin nào, ngày nào
6\.   \- Xuất kho / Cấp phát: Khoa nào, bệnh nhân nào \(nếu có\), ngày nào
7\.   \- Tồn kho hiện tại \(nếu còn\)
8\. Xuất báo cáo trace dưới dạng PDF để lưu hồ sơ

__Luồng thay thế__

• 2a\. Nhập tên vật tư: Hệ thống list tất cả batch của vật tư đó
• 7a\. Batch đã hết hàng: Hiển thị đầy đủ lịch sử đã xuất hết

__Hậu điều kiện__

• Báo cáo truy xuất đầy đủ được tạo
• Lịch sử được lưu cho audit

__Xử lý ngoại lệ__

• Batch không có đủ thông tin truy xuất: Hệ thống báo cáo dữ liệu thiếu

__UC\-30 – Thu Hồi Vật Tư \(Recall Management\)__

__Mô\-đun__

M10 – Truy xuất & Điều tra

__Mô tả__

Thực hiện quy trình thu hồi khẩn cấp khi phát hiện vật tư có vấn đề về chất lượng hoặc có thông báo recall từ nhà sản xuất\.

__Actor chính__

Quản lý \(SC\-MANAGER\), Thủ kho \(SC\-STOREKEEPER\)

__Điều kiện tiên quyết__

• Có thông báo recall từ NCC/nhà sản xuất hoặc phát hiện vấn đề nội bộ

__Luồng chính__

1\. Quản lý tạo Recall Notice: Nhập lý do, batch số bị ảnh hưởng
2\. Hệ thống tự động truy xuất tất cả batch liên quan \(UC\-29\)
3\. Hiển thị danh sách: Còn trong kho \(cần cô lập\), Đã cấp phát cho khoa nào
4\. Block tất cả giao dịch của batch bị recall
5\. Tạo lệnh thu hồi: In phiếu gửi đến từng khoa phòng
6\. Theo dõi tình trạng thu hồi từ từng khoa
7\. Khi thu hồi đủ: Tạo phiếu trả NCC hoặc hủy \(tùy theo quyết định\)
8\. Lưu hồ sơ recall đầy đủ

__Luồng thay thế__

• 3a\. Một phần đã sử dụng cho BN: Báo cáo ngay cho bác sĩ điều trị và quản lý y tế
• 7a\. Hủy vật tư: Tạo Stock Entry 'Write Off' với lý do 'Recall'

__Hậu điều kiện__

• Tất cả batch bị recall được thu hồi và xử lý
• Hồ sơ recall được lưu đầy đủ

__Xử lý ngoại lệ__

• Không thể xác định khoa phòng đã nhận: Audit toàn bộ cấp phát giai đoạn recall

__UC\-31 – Điều Tra Sự Cố Thất Thoát Vật Tư__

__Mô\-đun__

M10 – Truy xuất & Điều tra

__Mô tả__

Điều tra nguyên nhân thất thoát hoặc sai lệch tồn kho thông qua audit trail đầy đủ các giao dịch liên quan\.

__Actor chính__

Quản lý \(SC\-MANAGER\), Quản trị hệ thống \(SC\-SYSADMIN\)

__Điều kiện tiên quyết__

• Phát hiện sai lệch tồn kho hoặc nghi ngờ thất thoát

__Luồng chính__

1\. Quản lý mở Audit Trail / Stock Ledger chi tiết
2\. Lọc theo: Vật tư, Khoảng thời gian, Kho, Người thực hiện
3\. Hệ thống hiển thị toàn bộ giao dịch: Người tạo, Thời gian, IP, Thay đổi
4\. So sánh tồn kho lý thuyết vs thực tế theo từng giao dịch
5\. Xác định giao dịch bất thường: Sửa xóa không có lý do, nhập quá ngưỡng
6\. Xuất báo cáo điều tra có chữ ký điện tử

__Luồng thay thế__

• 5a\. Phát hiện gian lận: Khóa tài khoản user liên quan và escalate
• 4a\. Lỗi hệ thống: Tạo phiếu điều chỉnh với ghi chú 'System Error'

__Hậu điều kiện__

• Báo cáo điều tra được tạo và lưu
• Biện pháp khắc phục được đề xuất

__Xử lý ngoại lệ__

• Audit log bị xóa: Hệ thống phải có backup audit log không thể sửa

## __M11 – Dashboard & Cảnh báo điều hành__

__UC\-32 – Xem Dashboard Điều Hành Tổng Thể__

__Mô\-đun__

M11 – Dashboard & Cảnh báo điều hành

__Mô tả__

Xem dashboard tổng hợp các chỉ số KPI quan trọng của chuỗi cung ứng: tồn kho, chi phí, công nợ, hiệu suất NCC và cảnh báo\.

__Actor chính__

Lãnh đạo \(SC\-EXECUTIVE\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Có dữ liệu hoạt động trong hệ thống

__Luồng chính__

1\. Người dùng đăng nhập; hệ thống tự động hiển thị Dashboard theo role
2\. Xem các widget KPI: Tổng giá trị tồn kho, Chi phí vật tư tháng, Công nợ NCC, Số PO đang chờ duyệt
3\. Xem biểu đồ xu hướng: Chi phí theo tháng, Top 10 vật tư tiêu thụ nhiều nhất
4\. Xem bảng cảnh báo: Hết hàng, Sắp hết hạn, Hợp đồng sắp hết, PO chưa nhận
5\. Click vào widget để drill\-down chi tiết
6\. Thiết lập filter: Khoảng thời gian, Kho, Khoa phòng

__Luồng thay thế__

• 6a\. Export dashboard: Xuất PDF snapshot cho báo cáo hội đồng
• 1a\. Role khác: Dashboard hiển thị widget phù hợp với role

__Hậu điều kiện__

• Dashboard hiển thị dữ liệu real\-time hoặc near\-real\-time \(cache 5 phút\)

__Xử lý ngoại lệ__

• Dữ liệu chưa kịp tổng hợp: Hiển thị timestamp cập nhật cuối cùng

__UC\-33 – Cấu Hình và Quản Lý Cảnh Báo Tự Động__

__Mô\-đun__

M11 – Dashboard & Cảnh báo điều hành

__Mô tả__

Cấu hình các loại cảnh báo tự động: ngưỡng tồn kho, hạn dùng, hạn hợp đồng, và kênh nhận cảnh báo \(email, SMS, notification\)\.

__Actor chính__

Quản trị hệ thống \(SC\-SYSADMIN\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Người dùng có quyền cấu hình hệ thống

__Luồng chính__

1\. Admin mở màn hình Alert Configuration
2\. Chọn loại cảnh báo cần cấu hình
3\. Thiết lập ngưỡng: Ví dụ 'Tồn kho ≤ X ngày tiêu thụ' hoặc 'Hạn dùng ≤ 30 ngày'
4\. Chọn kênh cảnh báo: Email, In\-app notification, SMS \(nếu có tích hợp\)
5\. Chọn người nhận: Theo role hoặc email cụ thể
6\. Thiết lập tần suất: Ngay lập tức / Hàng ngày 8h sáng / Hàng tuần thứ Hai
7\. Test gửi cảnh báo để kiểm tra
8\. Lưu cấu hình; hệ thống bắt đầu áp dụng ngay

__Luồng thay thế__

• 5a\. Email bounce: Hệ thống thử lại 3 lần, sau đó log lỗi
• 7a\. Test fail: Hiển thị lỗi cụ thể \(SMTP, số điện thoại sai\.\.\.\)

__Hậu điều kiện__

• Cấu hình cảnh báo được lưu và kích hoạt
• Cảnh báo test được gửi thành công

__Xử lý ngoại lệ__

• Email server không khả dụng: Lưu queue, gửi khi server phục hồi

__UC\-34 – Xem và Xử Lý Cảnh Báo Hành Động__

__Mô\-đun__

M11 – Dashboard & Cảnh báo điều hành

__Mô tả__

Xem danh sách cảnh báo đang hoạt động, ưu tiên hóa và thực hiện hành động khắc phục ngay từ màn hình cảnh báo\.

__Actor chính__

Thủ kho \(SC\-STOREKEEPER\), Quản lý \(SC\-MANAGER\), Kế toán \(SC\-ACCOUNTANT\)

__Điều kiện tiên quyết__

• Có cảnh báo được kích hoạt trong hệ thống

__Luồng chính__

1\. Người dùng mở Notification Center hoặc Alert Dashboard
2\. Xem danh sách cảnh báo phân loại theo mức độ: Khẩn / Quan trọng / Thông tin
3\. Click vào cảnh báo để xem chi tiết và link đến dữ liệu liên quan
4\. Thực hiện hành động trực tiếp: 'Tạo PO', 'Cấp phát ưu tiên', 'Liên hệ NCC'
5\. Đánh dấu cảnh báo đã xử lý kèm ghi chú hành động đã thực hiện
6\. Hệ thống auto\-resolve cảnh báo khi điều kiện không còn thỏa mãn

__Luồng thay thế__

• 4a\. Chuyển cảnh báo cho người khác: Assign to another user
• 5a\. Snooze cảnh báo: Tạm ẩn trong X giờ với lý do

__Hậu điều kiện__

• Cảnh báo được xử lý và ghi chú hành động
• Cảnh báo resolved tự động khi điều kiện thay đổi

__Xử lý ngoại lệ__

• Cảnh báo không resolve sau 48h: Escalate lên cấp trên

## __SYS – Quản trị hệ thống__

__UC\-35 – Quản Lý Người Dùng và Phân Quyền__

__Mô\-đun__

SYS – Quản trị hệ thống

__Mô tả__

Tạo, sửa, vô hiệu hóa tài khoản người dùng và phân quyền theo role trong hệ thống SupplyCore\.

__Actor chính__

Quản trị hệ thống \(SC\-SYSADMIN\)

__Điều kiện tiên quyết__

• Admin có quyền System Manager trong Frappe

__Luồng chính__

1\. Admin mở User Management trong Frappe
2\. Tạo người dùng mới: Email, Tên, Số điện thoại
3\. Gán Role: SC\-STOREKEEPER / SC\-ACCOUNTANT / SC\-MANAGER / SC\-EXECUTIVE / SC\-WARD\-STAFF
4\. Cấu hình phạm vi dữ liệu: Được phép thao tác kho nào, khoa phòng nào
5\. Thiết lập quyền cụ thể qua Role Permission Manager: Read/Write/Create/Delete theo Doctype
6\. Gửi email welcome với hướng dẫn đăng nhập lần đầu
7\. Thiết lập yêu cầu đổi mật khẩu lần đăng nhập đầu tiên

__Luồng thay thế__

• 2a\. User đã nghỉ việc: Deactivate account, chuyển ownership documents
• 3a\. Role phức tạp: Tạo custom role với quyền mix nhiều role

__Hậu điều kiện__

• User được tạo và kích hoạt
• Email chào mừng được gửi
• Audit log ghi nhận

__Xử lý ngoại lệ__

• Email đã tồn tại: Hệ thống báo lỗi duplicate email

__UC\-36 – Cấu Hình Tham Số Hệ Thống__

__Mô\-đun__

SYS – Quản trị hệ thống

__Mô tả__

Cấu hình các tham số vận hành của hệ thống: ngưỡng cảnh báo, quy tắc workflow, format mã tự động, tích hợp email\.

__Actor chính__

Quản trị hệ thống \(SC\-SYSADMIN\)

__Điều kiện tiên quyết__

• Admin có quyền System Manager

__Luồng chính__

1\. Admin mở System Settings / SupplyCore Settings
2\. Cấu hình Auto\-numbering: Format PO number, Material Request number, Batch ID
3\. Cấu hình Workflow: Ngưỡng phê duyệt theo giá trị, danh sách approver
4\. Cấu hình email SMTP: Server, Port, Credentials
5\. Cấu hình ngưỡng cảnh báo mặc định: Safety stock %, Hạn dùng \(ngày\)
6\. Cấu hình múi giờ, ngôn ngữ mặc định, format ngày tháng
7\. Test connection và lưu cấu hình
8\. Hệ thống áp dụng cấu hình mới ngay lập tức

__Luồng thay thế__

• 7a\. Test SMTP fail: Hiển thị lỗi chi tiết, không lưu cấu hình email sai
• 3a\. Import cấu hình từ file: Hỗ trợ migration từ môi trường khác

__Hậu điều kiện__

• Cấu hình được lưu và áp dụng
• Test connections thành công

__Xử lý ngoại lệ__

• Cấu hình sai gây lỗi hệ thống: Rollback về cấu hình trước đó

__UC\-37 – Quản Lý Danh Mục Master Data__

__Mô\-đun__

SYS – Quản trị hệ thống

__Mô tả__

Quản lý danh mục dữ liệu nền tảng: Danh mục vật tư \(Item Master\), Đơn vị tính, Nhóm vật tư, Kho, Tài khoản kế toán\.

__Actor chính__

Quản trị hệ thống \(SC\-SYSADMIN\), Quản lý \(SC\-MANAGER\)

__Điều kiện tiên quyết__

• Admin có quyền tạo/sửa Master Data

__Luồng chính__

1\. Admin/Quản lý mở màn hình Item Master
2\. Tạo/sửa vật tư: Mã vật tư, Tên, Mô tả, Đơn vị tính \(mua/dùng\), Item Group
3\. Cấu hình vật tư y tế đặc thù: Has Batch No, Has Expiry Date, Tỉ lệ quy đổi đơn vị
4\. Thiết lập UOM Conversion: Ví dụ 1 hộp = 100 cái
5\. Gán mã BHYT tương ứng \(liên kết UC\-23\)
6\. Cấu hình tài khoản kế toán mặc định cho nhóm vật tư
7\. Import hàng loạt qua Excel template
8\. Lưu và kích hoạt; vật tư sẵn sàng sử dụng trong giao dịch

__Luồng thay thế__

• 7a\. Import lỗi: Báo cáo từng dòng lỗi, tiếp tục dòng hợp lệ
• 2a\. Vô hiệu hóa vật tư: Disabled = True, không xóa để giữ lịch sử

__Hậu điều kiện__

• Danh mục vật tư được cập nhật
• Vật tư mới sẵn sàng sử dụng trong PO, Receipt, Dispensing

__Xử lý ngoại lệ__

• Mã vật tư trùng: Hệ thống báo lỗi duplicate code

# __5\. MỐI QUAN HỆ GIỮA CÁC USE CASE__

Sơ đồ phụ thuộc giữa các UC chính theo luồng nghiệp vụ:

__UC Trigger__

__Tên__

__Quan hệ__

__UC phụ thuộc / gọi đến__

__UC\-07__

Purchase Request

<<include>>

UC\-08 \(Tạo PO\)

__UC\-08__

Purchase Order

<<include>>

UC\-09 \(Nhận hàng\)

__UC\-09__

Purchase Receipt

<<include>>

UC\-10 \(QC\), UC\-15 \(Batch\)

__UC\-10__

Quality Inspection

<<extend>>

UC\-11 \(Trả hàng nếu fail\)

__UC\-15__

Batch Tracking

<<include>>

UC\-16 \(FEFO\), UC\-17 \(Cảnh báo\)

__UC\-20__

Yêu cầu cấp phát

<<include>>

UC\-21 \(Xử lý cấp phát\)

__UC\-21__

Cấp phát vật tư

<<include>>

UC\-16 \(FEFO\), UC\-22 \(Ghi nhận BN\)

__UC\-22__

Ghi nhận sử dụng BN

<<include>>

UC\-23 \(Mã BHYT\)

__UC\-09__

Purchase Receipt

<<include>>

UC\-24 \(Tạo Invoice\)

__UC\-24__

Purchase Invoice

<<include>>

UC\-25 \(Payment\)

__UC\-27__

Kiểm kê

<<include>>

UC\-28 \(Đối soát\), UC\-19 \(Điều chỉnh\)

__UC\-29__

Truy xuất lô

<<extend>>

UC\-30 \(Recall nếu cần\)

__UC\-06__

Kế hoạch mua hàng

<<include>>

UC\-07 \(Sinh MR tự động\)

__UC\-03__

Hợp đồng khung

<<extend>>

UC\-08 \(Lấy giá PO\)

# __6\. RÀNG BUỘC VÀ GIẢ ĐỊNH NGHIỆP VỤ__

## __6\.1 Ràng buộc kỹ thuật__

• Toàn bộ use case được triển khai trên Frappe Framework v15 \+ ERPNext v15

• Không sửa source code ERPNext core; mọi tùy chỉnh qua hooks\.py, custom fields, client scripts

• Phân quyền tuân thủ Role Permission Manager của Frappe

• Mọi giao dịch quan trọng phải được ghi vào audit trail không thể xóa

## __6\.2 Giả định nghiệp vụ__

• Vật tư có thể có 1\-N mã BHYT thuộc nhóm N01–N09 theo Thông tư Bộ Y tế

• Mỗi vật tư có tối thiểu 2 đơn vị tính: đơn vị mua và đơn vị sử dụng

• Kho phân cấp 3 tầng: Kho tổng → Kho con → Kho khoa phòng

• Nhập kho LUÔN đi kèm kiểm tra QC cơ bản \(lô, hạn dùng, SL, quy cách\)

• Cấp phát có thể gắn bệnh nhân cụ thể hoặc chỉ gắn khoa/phòng

• Thanh toán NCC gắn với Purchase Invoice, đối chiếu Purchase Receipt \+ hợp đồng khung

• Quy định BHYT thay đổi thường xuyên – mọi logic BHYT phải cấu hình được, không hard\-code

## __6\.3 Ngoài phạm vi \(giai đoạn 1\)__

• Quản lý dược phẩm / thuốc

• Tài sản cố định \(TSCĐ\)

• Module đấu thầu tập trung

• Tích hợp trực tiếp HIS/EMR/LIS \(thiết kế API sẵn sàng, chưa kết nối\)

• Tích hợp cổng thanh toán điện tử

