# Chương 2 — Quản trị hệ thống
H1	2	Quản trị hệ thống
FIRST	Chương này dành cho Quản trị Hệ thống. Trước khi các khoa/phòng bắt đầu nghiệp vụ, hệ thống cần có người dùng, dữ liệu nền (vật tư, kho, nhà cung cấp…), tham số vận hành và cấu hình cảnh báo. Hãy thiết lập theo đúng thứ tự trong chương này.
H2	2.1	Quản lý người dùng & phân quyền
H3	2.1.1	Tổng quan mô hình phân quyền
FIRST	SupplyCore phân quyền theo **vai trò (role)**. Mỗi người dùng được gán một hoặc nhiều vai trò; vai trò quyết định module nào hiện ra, màn hình nào vào được và thao tác nào (xem, tạo, sửa, nộp, hủy) được phép. Quyền được kiểm tra ở máy chủ trên từng bản ghi.
BODY	Các vai trò chính của SupplyCore:
TABLE	Vai trò|Phạm vi công việc
ROW	System Manager / Quản trị Hệ thống|Toàn quyền cấu hình, người dùng, dữ liệu nền
ROW	SupplyCore Manager / Trưởng phòng Vật tư|Duyệt PO, thanh toán, hợp đồng; giám sát chuỗi cung ứng
ROW	SupplyCore Storekeeper / Thủ kho|Nhập – xuất – tồn, FEFO, chuyển kho, kiểm kê
ROW	SupplyCore Ward Staff / NV Khoa|Yêu cầu vật tư cho khoa
ROW	SupplyCore Accountant / Kế toán|Hóa đơn, đối chiếu 3 bên, thanh toán
ROW	Pharmacy / QC Officer / Kiểm soát Chất lượng|Kiểm tra chất lượng, lô, truy xuất, thu hồi
ROW	SupplyCore Auditor / Kiểm toán|Xem dữ liệu, không chỉnh sửa
H3	2.1.2	Tạo người dùng mới
OL	Trên Sidebar, mở **Người dùng & Quyền** (địa chỉ /users).
OL	Nhấn nút tạo người dùng mới, điền **Email**, **Họ tên**.
OL	Chọn một hoặc nhiều **Vai trò** phù hợp công việc của người đó.
OL	Tùy chọn đặt mật khẩu hoặc cho hệ thống gửi email mời (nếu đã cấu hình email).
OL	Nhấn lưu. Người dùng có thể đăng nhập ngay với vai trò đã cấp.
IMG	Màn hình Người dùng & Quyền với danh sách người dùng và hộp thoại tạo mới.
H3	2.1.3	Cấp và thu hồi quyền
OL	Tại danh sách người dùng, tìm theo tên/email và mở người dùng cần sửa.
OL	Thêm hoặc bỏ **Vai trò**; lưu lại để áp dụng.
WARN	Thay đổi vai trò ảnh hưởng ngay tới những gì người dùng nhìn thấy và làm được. Chỉ cấp vai trò đúng nhu cầu công việc (nguyên tắc tối thiểu quyền).
H3	2.1.4	Đặt lại mật khẩu, khóa / mở tài khoản
OL	Mở người dùng cần xử lý.
OL	Chọn **Đặt lại mật khẩu** để gửi email đặt lại (hoặc đặt mật khẩu mới trực tiếp).
OL	Dùng **Bật/Tắt** để mở hoặc tạm khóa tài khoản khi nhân sự nghỉ/chuyển công tác.
H3	2.1.5	Liên quan
UL	Xem 1.3 — Vai trò của bạn làm được gì.
H2	2.2	Dữ liệu nền tảng (M0)
H3	2.2.1	Vì sao cần dữ liệu nền trước
FIRST	Mọi nghiệp vụ đều dựa trên dữ liệu nền. Không thể tạo đơn hàng nếu chưa có vật tư và nhà cung cấp; không thể nhập kho nếu chưa khai báo kho. Hãy khai báo dữ liệu nền M0 trước khi mở nghiệp vụ.
BODY	**Thứ tự khuyến nghị:** Đơn vị tính → Nhóm vật tư → Vật tư → Kho (3 tầng) → Nhà cung cấp → Khoa/Phòng → Tài khoản kế toán → Mã BHYT.
H3	2.2.2	Khai báo từng loại dữ liệu nền
FIRST	Mỗi loại dữ liệu nền là một DocType, truy cập qua module **M0 · Dữ liệu nền** hoặc màn hình Danh sách tương ứng.
TABLE	Dữ liệu nền|Dùng để|Ghi chú quan trọng
ROW	Đơn vị tính (SC UOM)|cái, hộp, lọ, thùng…|Khai hệ số quy đổi giữa đơn vị mua và đơn vị dùng
ROW	Nhóm vật tư (SC Item Group)|Phân loại vật tư theo cây|Dùng cho lọc, báo cáo, cấu hình BHYT theo nhóm
ROW	Vật tư (SC Item)|Danh mục vật tư|Bật **Theo lô** với vật tư cần quản lý hạn dùng; khai tồn an toàn, điểm tái đặt; mã HIS để khớp khi nhập phiếu HIS
ROW	Kho (SC Warehouse)|Kho 3 tầng: Kho chính → Kho lẻ → Kho khoa|Khai đúng **Loại kho** và **Kho cha** để giữ cấu trúc phân cấp
ROW	Nhà cung cấp (SC Supplier)|Hồ sơ NCC|Mã số thuế duy nhất; có thể đưa vào danh sách đen để chặn đặt hàng
ROW	Khoa/Phòng (SC Department)|Đơn vị sử dụng vật tư|Có thể đặt **hạn mức cấp phát/tháng**
ROW	Người bệnh (SC Patient)|Phục vụ cấp phát theo người bệnh|Cần cho cấp phát BHYT theo bệnh nhân
ROW	Tài khoản kế toán (SC GL Account)|Hệ thống tài khoản|Dùng cho bút toán nhập/xuất/chênh lệch
ROW	Mã BHYT (SC BHYT Code Config)|Mã nhóm N01–N09|Khai tỷ lệ chi trả, giá trần (xem 2.4)
H3	2.2.3	Nhập dữ liệu hàng loạt bằng CSV/Excel
FIRST	Với khối lượng lớn (ví dụ hàng nghìn vật tư), dùng chức năng nhập hàng loạt thay vì gõ tay từng dòng.
OL	Mở màn hình **Danh sách** của loại dữ liệu cần nhập.
OL	Nhấn **Nhập**, tải về **mẫu** (template) CSV/Excel để biết đúng cột cần điền.
OL	Điền dữ liệu vào mẫu; có thể chạy **thử (dry run)** để hệ thống kiểm lỗi trước khi ghi thật.
OL	Tải tệp lên, chọn cập nhật bản ghi đã có nếu cần, rồi xác nhận nhập.
OL	Dùng **Xuất** để tải dữ liệu hiện có ra Excel khi cần sao lưu hoặc chỉnh sửa hàng loạt.
NOTE	Mẹo: luôn chạy thử trước. Hệ thống sẽ báo dòng nào lỗi (thiếu trường bắt buộc, tham chiếu sai) để bạn sửa trước khi ghi chính thức.
H3	2.2.4	Kho 3 tầng — lưu ý cấu trúc
FIRST	SupplyCore tổ chức kho theo ba tầng: **Kho chính** (nhập từ nhà cung cấp) → **Kho lẻ/khu vực** → **Kho khoa**. Vật tư chảy từ trên xuống qua các phiếu chuyển kho.
OL	Tạo Kho chính trước (đặt là kho nhóm nếu chỉ dùng để chứa kho con).
OL	Tạo các Kho lẻ và Kho khoa, gán **Kho cha** đúng để giữ phân cấp.
OL	Khai bản đồ kho/vị trí kệ nếu dùng (xem 3.4).
H3	2.2.5	Liên quan
UL	Xem 3.4 — Quản lý kho; 3.5 — Lô & FEFO; 2.4 — BHYT.
H2	2.3	Cấu hình tham số hệ thống
H3	2.3.1	Cấu hình SupplyCore Settings
FIRST	SupplyCore Settings là nơi đặt các ngưỡng và quy tắc vận hành áp dụng cho toàn hệ thống. Chỉ Quản trị Hệ thống chỉnh sửa. Thay đổi tại đây ảnh hưởng tới phê duyệt, FEFO và cảnh báo.
TABLE	Tham số|Ý nghĩa|Mặc định
ROW	Ngưỡng duyệt PO|Đơn hàng vượt mức này cần Trưởng phòng/Ban giám đốc duyệt|50 triệu VND
ROW	Ngưỡng duyệt Hợp đồng khung|Hợp đồng vượt mức này cần cấp cao duyệt|100 triệu VND
ROW	Nhắc NCC phản hồi PO|Số ngày trước khi gửi email nhắc nhà cung cấp|3 ngày
ROW	Ngưỡng chênh lệch kiểm kê|Chênh lệch vượt mức này phải lập điều tra|10 triệu VND
ROW	FEFO nghiêm ngặt|Bật = chặn vi phạm FEFO; Tắt = chỉ cảnh báo|Bật
ROW	Hạn dùng tối thiểu khi nhập|Số ngày hạn dùng còn lại tối thiểu khi nhập kho|30 ngày
ROW	Cảnh báo hết hạn — Cảnh báo|Ngưỡng vàng trước hạn|90 ngày
ROW	Cảnh báo hết hạn — Nghiêm trọng|Ngưỡng đỏ trước hạn|30 ngày
ROW	Cảnh báo hợp đồng sắp hết hạn|Số ngày trước khi báo|30 ngày
BODY	Ngoài ra còn cấu hình bản đồ khuôn viên (tên, kích thước lưới, lối vào) và các điểm tích hợp (HIS, BHYT, SMS) nếu bệnh viện sử dụng.
WARN	Đừng tắt FEFO nghiêm ngặt trừ khi có lý do rõ ràng — đây là hàng rào chống xuất nhầm lô sắp hết hạn.
H3	2.3.2	Liên quan
UL	Xem 3.2 — duyệt PO; 3.5 — FEFO & cảnh báo hết hạn; 3.9 — ngưỡng chênh lệch kiểm kê.
H2	2.4	BHYT, Cảnh báo & Email
H3	2.4.1	Cấu hình mã BHYT N01–N09
FIRST	Để hệ thống tính đúng phần chi trả khi cấp phát cho người bệnh, cần khai cấu hình mã BHYT. Mỗi cấu hình gắn với một mã nhóm N01–N09 và áp cho một vật tư cụ thể hoặc cả nhóm vật tư.
OL	Mở Danh sách **Mã BHYT (SC BHYT Code Config)**, nhấn **Tạo mới**.
OL	Chọn **Nhóm BHYT** (N01–N09), nhập **Tỷ lệ chi trả** (%) và **Giá trần** (VND/đơn vị).
OL	Gán cho **Vật tư** cụ thể hoặc **Nhóm vật tư**; đặt **Hiệu lực từ / đến**.
OL	Ghi **Căn cứ pháp lý** (số văn bản) và lưu.
NOTE	Khi một vật tư có cấu hình riêng và cấu hình theo nhóm, hệ thống ưu tiên cấu hình cụ thể cho vật tư đó. Chi tiết cách tính khi cấp phát xem mục 3.7.
H3	2.4.2	Cấu hình cảnh báo tự động (Alert Rule)
FIRST	Trung tâm cảnh báo lấy dữ liệu từ các **luật cảnh báo (SC Alert Rule)** do quản trị viên đặt: tồn thấp, lô sắp hết hạn, hợp đồng sắp hết hạn, thanh toán quá hạn, chờ kiểm tra chất lượng, thu hồi chưa xử lý…
OL	Mở Danh sách **Luật cảnh báo**, nhấn **Tạo mới**.
OL	Chọn loại điều kiện, đặt **ngưỡng**, phạm vi (kho/khoa/nhà cung cấp), kênh gửi (trong ứng dụng / Email / SMS) và người nhận.
OL	Dùng chức năng gửi thử để kiểm tra, rồi bật luật.
BODY	Chi tiết vận hành cảnh báo và Dashboard xem mục 3.11.
H3	2.4.3	Cấu hình Email & thông báo
OL	Khai máy chủ gửi email (SMTP) ở cấu hình hệ thống để gửi được email mời người dùng, đặt lại mật khẩu và cảnh báo qua email.
OL	Gửi thử một email để xác nhận cấu hình đúng.
OL	Nếu email không tới: kiểm tra hàng đợi email, địa chỉ người nhận, và thư mục spam.
NOTE	Chuông/Trung tâm cảnh báo trong ứng dụng vẫn hoạt động kể cả khi chưa cấu hình email — email chỉ là kênh gửi thêm.
H3	2.4.4	Liên quan
UL	Xem 3.7 — Cấp phát & BHYT; 3.11 — Dashboard & Cảnh báo.
