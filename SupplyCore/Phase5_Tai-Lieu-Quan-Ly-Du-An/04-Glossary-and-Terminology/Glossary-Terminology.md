__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung ứng Vật tư Y tế Bệnh viện

__GLOSSARY & TERMINOLOGY – TỪ ĐIỂN THUẬT NGỮ__

Tài liệu này định nghĩa thống nhất các thuật ngữ chuyên ngành được sử dụng trong toàn bộ hệ thống SupplyCore và các tài liệu dự án, bao gồm thuật ngữ quản lý chuỗi cung ứng, y tế, kỹ thuật phần mềm và quản lý dự án\.

Cột 'Áp dụng' ký hiệu: SC = SupplyCore system, BV = Bệnh viện/nghiệp vụ, IT = Kỹ thuật, PM = Quản lý dự án

# __A – Thuật ngữ Chuỗi Cung ứng & Kho vận__

__Thuật ngữ \(EN\)__

__Viết tắt__

__Tiếng Việt__

__Định nghĩa__

__Áp dụng__

__Batch / Lot__

__—__

Lô hàng

Nhóm sản phẩm được sản xuất hoặc nhập kho cùng một thời điểm, chia sẻ chung số lô và hạn sử dụng\. Dùng để truy xuất nguồn gốc\.

SC, BV

__FEFO__

__FEFO__

Hết hạn trước, xuất trước

First Expired, First Out – Nguyên tắc xuất kho ưu tiên sản phẩm có hạn sử dụng gần nhất để tránh hàng hết hạn\. Áp dụng bắt buộc cho vật tư y tế\.

SC, BV

__FIFO__

__FIFO__

Nhập trước, xuất trước

First In, First Out – Nguyên tắc xuất kho sản phẩm nhập vào trước được xuất ra trước\. Thường kết hợp với FEFO trong môi trường y tế\.

SC, BV

__GRN__

__GRN__

Phiếu nhập kho

Goods Receipt Note – Chứng từ ghi nhận việc nhận hàng từ nhà cung cấp vào kho, xác nhận số lượng và chất lượng\.

SC, BV

__Inventory Count__

__—__

Kiểm kê kho

Quy trình đếm và đối chiếu số lượng vật tư thực tế trong kho với số liệu trên hệ thống\.

SC, BV

__Lead Time__

__—__

Thời gian giao hàng

Khoảng thời gian từ khi đặt hàng đến khi nhận được hàng từ nhà cung cấp\. Dùng để tính điểm đặt hàng lại\.

SC, BV

__Min/Max Level__

__—__

Mức tồn kho tối thiểu/tối đa

Ngưỡng tồn kho định sẵn: tối thiểu \(Reorder Point\) kích hoạt đặt hàng; tối đa giới hạn lượng hàng mua\.

SC, BV

__Putaway__

__—__

Định vị vào kho

Quy trình xác định và gán vị trí lưu trữ cụ thể cho hàng hóa mới nhận trong kho \(slot/bin assignment\)\.

SC, BV

__Reorder Point__

__ROP__

Điểm đặt hàng lại

Mức tồn kho khi đạt tới cần tạo đơn đặt hàng mới để đảm bảo không hết hàng trước khi giao hàng kế tiếp\.

SC, BV

__Release Order__

__RO__

Lệnh gọi hàng

Yêu cầu xuất hàng theo hợp đồng khung \(Frame Agreement\) đã ký với nhà cung cấp, không cần đấu thầu lại\.

SC, BV

__SKU__

__SKU__

Mã vật tư

Stock Keeping Unit – Mã định danh duy nhất cho từng loại vật tư trong hệ thống kho\.

SC, BV

__Stock Transfer__

__—__

Điều chuyển kho

Chuyển vật tư từ kho nguồn sang kho đích trong cùng bệnh viện, không thay đổi quyền sở hữu\.

SC, BV

__Stockout__

__—__

Hết hàng

Tình trạng tồn kho về 0, không còn vật tư để cấp phát\. Cần cảnh báo và xử lý khẩn cấp\.

SC, BV

__WMS__

__WMS__

Hệ thống quản lý kho

Warehouse Management System – Phân hệ quản lý vị trí, di chuyển và truy xuất hàng hóa trong kho vật lý\.

SC, IT

# __B – Thuật ngữ Y tế & Bệnh viện__

__Thuật ngữ \(EN\)__

__Viết tắt__

__Tiếng Việt__

__Định nghĩa__

__Áp dụng__

__Consumable Medical Supply__

__—__

Vật tư tiêu hao y tế

Vật tư y tế dùng một lần hoặc có thời hạn sử dụng, như găng tay, băng gạc, kim tiêm, ống nội soi\.\.\. Phân biệt với thiết bị y tế dùng lâu dài\.

SC, BV

__Expiry Date__

__EXP__

Ngày hết hạn

Ngày mà vật tư y tế không còn được phép sử dụng theo tiêu chuẩn an toàn\. Phải được quản lý và cảnh báo trước\.

SC, BV

__HIS__

__HIS__

Hệ thống thông tin bệnh viện

Hospital Information System – Hệ thống quản lý thông tin bệnh nhân, khám chữa bệnh, kê đơn\.\.\. Ví dụ: HIS VinHIS, HIS VNPT\.

SC, IT

__BHYT__

__BHYT__

Bảo hiểm y tế

Bảo hiểm Y tế Việt Nam – Chế độ bảo hiểm nhà nước chi trả chi phí khám chữa bệnh\. Vật tư sử dụng cho bệnh nhân BHYT cần hạch toán riêng\.

BV

__Lot Number__

__—__

Số lô sản xuất

Mã số do nhà sản xuất gán cho một lô sản phẩm cụ thể, dùng để truy xuất nguồn gốc và thu hồi nếu cần\.

SC, BV

__QC / QA__

__QC/QA__

Kiểm tra/Đảm bảo chất lượng

Quality Control/Quality Assurance – Quy trình kiểm tra chất lượng vật tư khi nhận hàng: đúng số lô, hạn dùng, tình trạng bao bì, CO/CQ\.

SC, BV

__CO/CQ__

__CO/CQ__

Chứng nhận xuất xứ & chất lượng

Certificate of Origin / Certificate of Quality – Giấy chứng nhận xuất xứ hàng hóa và chất lượng sản phẩm từ nhà sản xuất, bắt buộc khi nhập kho vật tư y tế\.

SC, BV

__Par Level__

__—__

Mức tiêu chuẩn tại khoa

Lượng vật tư tối thiểu cần duy trì tại mỗi khoa/phòng để đảm bảo hoạt động\. Khi xuống dưới Par Level cần bổ sung từ kho trung tâm\.

SC, BV

__Issue / Dispensing__

__—__

Cấp phát vật tư

Quy trình xuất vật tư từ kho cấp phát cho khoa/phòng hoặc gắn với bệnh nhân cụ thể\.

SC, BV

__Traceability__

__—__

Truy xuất nguồn gốc

Khả năng theo dõi lịch sử đầy đủ của vật tư từ nhà cung cấp, lô hàng, nhập kho, lưu kho đến cấp phát và sử dụng\.

SC, BV

# __C – Thuật ngữ Hệ thống & Kỹ thuật__

__Thuật ngữ \(EN\)__

__Viết tắt__

__Tiếng Việt__

__Định nghĩa__

__Áp dụng__

__API__

__API__

Giao diện lập trình ứng dụng

Application Programming Interface – Tập hợp các endpoint cho phép hệ thống bên ngoài \(HIS, ERP\) trao đổi dữ liệu với SupplyCore\.

SC, IT

__Audit Log__

__—__

Nhật ký kiểm toán

Bản ghi tự động mọi thay đổi dữ liệu quan trọng: ai thay đổi, thay đổi gì, khi nào\. Không thể xóa hoặc sửa\.

SC, IT

__Custom App \(Frappe\)__

__—__

Ứng dụng tùy chỉnh Frappe

Module phần mềm viết thêm trên nền tảng Frappe Framework, không thay đổi core ERPNext\. SupplyCore là một custom app\.

SC, IT

__DocType__

__—__

Loại tài liệu \(Frappe\)

Đơn vị dữ liệu cơ bản trong Frappe Framework, tương đương một bảng trong database kết hợp với form UI\.

IT

__ERPNext__

__—__

Hệ thống ERP mã nguồn mở

Enterprise Resource Planning system mã nguồn mở, xây dựng trên Frappe Framework\. SupplyCore kế thừa module kế toán, HR từ ERPNext\.

SC, IT

__Frappe Framework__

__—__

Nền tảng phát triển web

Full\-stack web framework Python/JavaScript mã nguồn mở, nền tảng của ERPNext và SupplyCore\. Phiên bản sử dụng: v15\.

IT

__MariaDB__

__—__

Hệ quản trị CSDL

Hệ quản trị cơ sở dữ liệu quan hệ mã nguồn mở, được Frappe sử dụng làm database chính\. Phiên bản: 10\.6\+\.

IT

__PDA__

__PDA__

Thiết bị cầm tay kho

Portable Device for Automation – Thiết bị cầm tay \(handheld scanner/tablet\) tích hợp barcode/QR reader cho nhân viên kho thao tác trực tiếp\.

SC, IT

__Redis__

__—__

Bộ nhớ đệm phân tán

In\-memory data store dùng làm cache và message queue trong Frappe, cải thiện hiệu năng hệ thống\.

IT

__REST API__

__—__

API kiểu REST

Representational State Transfer API – Kiến trúc API chuẩn mà SupplyCore cung cấp để tích hợp với HIS và các hệ thống ngoài\.

SC, IT

__Role\-Based Access Control__

__RBAC__

Phân quyền theo vai trò

Cơ chế phân quyền dựa trên vai trò người dùng \(kho trung tâm, khoa, kế toán\.\.\.\) để giới hạn quyền xem/sửa/xóa dữ liệu\.

SC, IT

__SLA__

__SLA__

Thỏa thuận mức dịch vụ

Service Level Agreement – Cam kết về hiệu năng hệ thống: uptime, response time, thời gian xử lý sự cố\.

IT, PM

__Webhook__

__—__

Cơ chế thông báo tức thì

HTTP callback tự động gửi dữ liệu đến hệ thống ngoài khi có sự kiện xảy ra trong SupplyCore \(ví dụ: nhập kho thành công\)\.

IT

# __D – Thuật ngữ Quản lý Dự án__

__Thuật ngữ \(EN\)__

__Viết tắt__

__Tiếng Việt__

__Định nghĩa__

__Áp dụng__

__Backlog__

__—__

Danh sách tồn đọng

Danh sách tất cả các tính năng, yêu cầu, bug cần thực hiện trong dự án, được ưu tiên và quản lý bởi PM/BA\.

PM

__Baseline__

__—__

Đường cơ sở

Phiên bản tài liệu đã được phê duyệt và ký duyệt, làm mốc tham chiếu cho mọi thay đổi sau này\.

PM

__BRD__

__BRD__

Tài liệu yêu cầu kinh doanh

Business Requirements Document – Tài liệu mô tả nhu cầu kinh doanh, mục tiêu và phạm vi dự án từ góc nhìn tổ chức\.

PM

__Change Request__

__CR__

Yêu cầu thay đổi

Đề xuất chính thức để sửa đổi phạm vi, thiết kế, timeline hoặc ngân sách đã được baseline\. Phải qua quy trình Change Control\.

PM

__FRS__

__FRS__

Tài liệu yêu cầu chức năng

Functional Requirements Specification – Tài liệu mô tả chi tiết từng chức năng hệ thống phải thực hiện\.

PM

__Go\-Live__

__—__

Đưa vào vận hành

Thời điểm hệ thống SupplyCore chính thức được triển khai và người dùng thật bắt đầu sử dụng trong môi trường production\.

PM

__Hypercare__

__—__

Giai đoạn hỗ trợ tăng cường

Khoảng thời gian sau Go\-Live \(thường 1–3 tháng\) team dự án hỗ trợ 24/7 để xử lý sự cố, ổn định hệ thống\.

PM

__Milestone__

__—__

Mốc quan trọng

Điểm kiểm tra tiến độ quan trọng trong dự án, thường gắn với một deliverable cụ thể và yêu cầu phê duyệt\.

PM

__MoSCoW__

__—__

Phương pháp ưu tiên yêu cầu

Must have / Should have / Could have / Won't have – Phương pháp phân loại yêu cầu theo mức độ cần thiết\.

PM

__Sprint__

__—__

Chu kỳ phát triển

Khoảng thời gian cố định \(2 tuần\) trong Scrum, team phát triển cam kết hoàn thành một tập hợp user stories cụ thể\.

PM, IT

__UAT__

__UAT__

Kiểm thử nghiệm thu người dùng

User Acceptance Testing – Giai đoạn người dùng cuối kiểm tra hệ thống theo kịch bản thực tế để xác nhận đáp ứng yêu cầu\.

PM, BV

__URS__

__URS__

Tài liệu yêu cầu người dùng

User Requirements Specification – Tài liệu mô tả yêu cầu từ góc nhìn người dùng cuối, thường dưới dạng user stories\.

PM

# __E – Từ viết tắt tổng hợp__

__Viết tắt__

__Đầy đủ__

__API__

Application Programming Interface

__BA__

Business Analyst

__BHYT__

Bảo hiểm Y tế

__BRD__

Business Requirements Document

__CCB__

Change Control Board

__CO/CQ__

Certificate of Origin / Certificate of Quality

__CR__

Change Request

__DB__

Database \(Cơ sở dữ liệu\)

__ERP__

Enterprise Resource Planning

__FEFO__

First Expired, First Out

__FIFO__

First In, First Out

__FRS__

Functional Requirements Specification

__GRN__

Goods Receipt Note \(Phiếu nhập kho\)

__HIS__

Hospital Information System

__KPI__

Key Performance Indicator

__PDA__

Portable Device / Handheld Scanner

__PM__

Project Manager

__QA__

Quality Assurance

__QC__

Quality Control

__RACI__

Responsible, Accountable, Consulted, Informed

__RBAC__

Role\-Based Access Control

__RO__

Release Order \(Lệnh gọi hàng\)

__ROP__

Reorder Point \(Điểm đặt hàng lại\)

__SC__

SupplyCore

__SKU__

Stock Keeping Unit \(Mã vật tư\)

__SLA__

Service Level Agreement

__UAT__

User Acceptance Testing

__URS__

User Requirements Specification

__VT__

Vật tư

__VTYT__

Vật tư Y tế

__WMS__

Warehouse Management System

## __Ghi chú cập nhật tài liệu__

Tài liệu này được cập nhật theo vòng đời dự án\. Khi có thuật ngữ mới phát sinh, BA/PM cập nhật vào tài liệu và thông báo cho toàn team trong Sprint Planning hoặc qua email dự án\.

