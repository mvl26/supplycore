# Chương 1 — Bắt đầu
H1	1	Bắt đầu
H2	1.1	Tổng quan về SupplyCore
H3	1.1.1	SupplyCore là gì?
FIRST	SupplyCore là hệ thống quản lý vật tư và cung ứng y tế dành cho bệnh viện. Thay vì theo dõi vật tư rải rác trên giấy tờ và bảng tính, SupplyCore tập hợp toàn bộ dòng chảy vật tư — từ hợp đồng với nhà cung cấp, đặt hàng, nhập kho, kiểm tra chất lượng, lưu kho theo lô, chuyển kho, cấp phát cho khoa và người bệnh, đến hóa đơn – thanh toán và kiểm kê — vào một nơi duy nhất, có kiểm soát và truy vết.
BODY	Hệ thống giúp bệnh viện:
UL	Biết mỗi vật tư đang ở kho nào, còn bao nhiêu, thuộc lô nào và hạn dùng đến khi nào.
UL	Xuất kho đúng nguyên tắc **FEFO** (lô hết hạn trước xuất trước), hạn chế tối đa vật tư hết hạn.
UL	Kiểm soát ngân sách mua sắm, đối chiếu **3 bên** (Đơn hàng – Phiếu nhập – Hóa đơn) trước khi thanh toán.
UL	Tính đúng phần chi trả **BHYT** theo mã nhóm N01–N09 khi cấp phát cho người bệnh.
UL	Lưu đầy đủ lịch sử: ai làm gì, lúc nào, trên bản ghi nào — phục vụ kiểm tra, thanh tra và thu hồi khi cần.
H3	1.1.2	Vòng đời vật tư trong SupplyCore
FIRST	Mỗi vật tư đi qua sáu giai đoạn chính. SupplyCore đồng hành và ghi nhận xuyên suốt từng giai đoạn.
TABLE	Giai đoạn|Ý nghĩa|Tác vụ trong hệ thống
ROW	Hợp đồng & Kế hoạch|Chốt nhà cung cấp, giá khung; dự trù nhu cầu|Hợp đồng khung, Kế hoạch mua sắm (M1, M2)
ROW	Mua sắm|Tạo yêu cầu mua, đặt hàng, theo dõi giao hàng|Yêu cầu mua, Đơn đặt hàng (M2)
ROW	Tiếp nhận|Nhận hàng, kiểm tra chất lượng, tạo lô|Phiếu nhập, Kiểm tra chất lượng (M3)
ROW	Lưu kho|Xếp vị trí, theo dõi tồn theo lô & hạn dùng|Quản lý kho, Lô & FEFO (M4, M5)
ROW	Cấp phát|Chuyển kho nội bộ, cấp cho khoa/người bệnh|Chuyển kho, Cấp phát & BHYT (M6, M7)
ROW	Tài chính & Kiểm soát|Hóa đơn, thanh toán, kiểm kê, truy xuất, thu hồi|Kế toán, Kiểm kê, Truy xuất (M8, M9, M10)
BODY	**Dòng chảy chính:** Hợp đồng → Kế hoạch → Mua → Nhập & QC → Lưu kho (lô/FEFO) → Chuyển kho → Cấp phát (BHYT) → Hóa đơn → Thanh toán → Kiểm kê.
H3	1.1.3	Bố cục giao diện
FIRST	Khi làm việc với SupplyCore, bạn sẽ di chuyển qua bốn lớp màn hình theo thứ tự sau.
TABLE	Màn hình|Mô tả|Cách vào
ROW	Đăng nhập|Nhập tên đăng nhập và mật khẩu|Truy cập địa chỉ hệ thống
ROW	Trang chủ — Tổng quan (Dashboard)|Bảng chỉ số (KPI) và lối tắt theo vai trò của bạn|Sau khi đăng nhập thành công
ROW	Thanh điều hướng (Sidebar)|Cột bên trái — liệt kê nhóm chức năng và module bạn được phép dùng|Luôn hiển thị ở mọi màn hình
ROW	Trang module & Danh sách / Chi tiết|Mở từng module, xem danh sách bản ghi, mở chi tiết để tạo/sửa|Bấm module trên Sidebar
BODY	SupplyCore là ứng dụng web một trang (SPA): mọi thao tác diễn ra trong cùng một cửa sổ trình duyệt, chuyển màn hình nhanh, không tải lại trang.
IMG	Tổng thể giao diện: Sidebar bên trái, thanh trên cùng (topbar) chứa tên trang và menu tài khoản, vùng nội dung ở giữa.
H3	1.1.4	Bản đồ module (M0–M11)
FIRST	SupplyCore gồm một nhóm Dữ liệu nền (M0) và mười một module nghiệp vụ. Module được nhóm theo chức năng trên Sidebar.
TABLE	Nhóm|Module|Dùng để
ROW	Thiết lập|M0 · Dữ liệu nền|Khai báo vật tư, kho, nhà cung cấp, khoa, đơn vị tính, mã BHYT (xem Chương 2)
ROW	Chiến lược|M1 · Hợp đồng khung|Quản lý nhà cung cấp và hợp đồng khung
ROW	Chiến lược|M2 · Kế hoạch & Mua|Dự trù, yêu cầu mua, đơn đặt hàng
ROW	Vận hành|M3 · Tiếp nhận|Phiếu nhập và kiểm tra chất lượng
ROW	Vận hành|M4 · Quản lý kho|Tồn kho, vị trí kệ, bản đồ kho, xếp hàng
ROW	Vận hành|M5 · Quản lý lô vật tư|Lô, hạn dùng, FEFO, cảnh báo hết hạn
ROW	Vận hành|M6 · Chuyển kho|Chuyển kho nội bộ và nhập phiếu HIS (PDF)
ROW	Vận hành|M7 · Cấp phát|Cấp phát cho khoa/người bệnh và BHYT
ROW	Tài chính|M8 · Kế toán|Hóa đơn, đối chiếu 3 bên, thanh toán, báo cáo
ROW	Chất lượng|M9 · Kiểm kê|Kiểm kê và đối chiếu chênh lệch tồn
ROW	Chất lượng|M10 · Truy xuất & Thu hồi|Truy xuất lô và thu hồi sản phẩm
ROW	Báo cáo|M11 · Dashboard & Cảnh báo|Bảng chỉ số và trung tâm cảnh báo
NOTE	Bạn chỉ nhìn thấy những module và chức năng phù hợp với vai trò của mình. Nếu thiếu một module, không phải hệ thống lỗi — xem mục 1.3.3.
H2	1.2	Đăng nhập & làm quen giao diện
H3	1.2.1	Đăng nhập hệ thống
OL	Mở trình duyệt (khuyến nghị Google Chrome hoặc Microsoft Edge bản mới) và truy cập địa chỉ hệ thống do quản trị viên cung cấp.
OL	Nhập **Tên đăng nhập** (thường là email) và **Mật khẩu**. Có thể bấm biểu tượng con mắt để hiện/ẩn mật khẩu.
OL	Nhấn **Đăng nhập**. Khi thành công, hệ thống chuyển vào **Trang chủ — Tổng quan**.
IMG	Màn hình đăng nhập: panel giới thiệu bên trái, biểu mẫu đăng nhập bên phải.
WARN	Nếu nhập sai nhiều lần hoặc tài khoản bị khóa, hãy liên hệ quản trị viên để được mở lại — đừng thử liên tục.
H3	1.2.2	Đổi mật khẩu & quên mật khẩu
OL	Để đổi mật khẩu khi đã đăng nhập: mở menu tài khoản ở góc trên bên phải và chọn mục hồ sơ cá nhân.
OL	Nếu quên mật khẩu: liên hệ quản trị viên để được **đặt lại mật khẩu** (xem mục 2.1). Hệ thống sẽ gửi email hướng dẫn nếu đã cấu hình máy chủ email.
NOTE	Đặt mật khẩu đủ mạnh (chữ hoa, chữ thường, số). Không chia sẻ tài khoản — mọi thao tác đều được ghi lại theo người đăng nhập.
H3	1.2.3	Trang chủ — Tổng quan (Dashboard)
FIRST	Trang chủ hiển thị các thẻ chỉ số (KPI) quan trọng và những lối tắt phù hợp với vai trò của bạn. Đây là điểm bắt đầu mỗi ngày.
OL	Xem nhanh các thẻ số liệu: tổng giá trị tồn kho, chi phí mua trong kỳ, công nợ nhà cung cấp, đơn hàng đang chờ, lô sắp hết hạn, vật tư dưới tồn an toàn…
OL	Dùng bộ lọc phía trên (kỳ, kho, khoa) để thu hẹp số liệu.
OL	Bấm các lối tắt (ví dụ **Tạo yêu cầu vật tư**, **Phê duyệt PO**, **Xếp hàng lên kệ**) để đi thẳng tới tác vụ thường dùng.
IMG	Trang chủ với lưới thẻ KPI và các nút lối tắt theo vai trò.
BODY	Chi tiết về Dashboard và cảnh báo xem mục 3.11.
H3	1.2.4	Thanh điều hướng (Sidebar) theo vai trò
FIRST	Cột bên trái là Sidebar — nơi mở mọi chức năng. Nội dung Sidebar thay đổi theo vai trò: thủ kho thấy nhóm nhập–xuất–tồn kho; kế toán thấy nhóm hóa đơn – thanh toán; điều dưỡng thấy nhóm yêu cầu vật tư.
OL	Bấm một mục trên Sidebar để mở module hoặc màn hình tương ứng.
OL	Bấm nút thu gọn ở đầu Sidebar để mở rộng vùng làm việc; trạng thái này được ghi nhớ cho lần sau.
OL	Trên điện thoại/máy tính bảng, Sidebar mở dạng ngăn kéo khi bạn bấm biểu tượng menu.
H3	1.2.5	Trung tâm cảnh báo
OL	Mở **Cảnh báo** trên Sidebar (hoặc địa chỉ /alerts) để xem danh sách cảnh báo: tồn thấp, lô sắp hết hạn, hợp đồng sắp hết hạn, thanh toán quá hạn, chờ kiểm tra chất lượng, thu hồi chưa xử lý.
OL	Lọc theo trạng thái (Đang mở / Đã xử lý) và mức độ (Nghiêm trọng / Cảnh báo / Thông tin).
OL	Bấm một cảnh báo để mở thẳng bản ghi liên quan và xử lý.
BODY	Nếu Trung tâm cảnh báo trống, đó là dấu hiệu tốt — không có vấn đề nào cần xử lý. Chi tiết xem mục 3.11.
H3	1.2.6	Quét mã vạch / QR vật tư
FIRST	Trên thiết bị có camera (điện thoại, máy quét), SupplyCore hỗ trợ quét mã vạch lô vật tư để tra nhanh thông tin và hỗ trợ thao tác kho.
OL	Mở chức năng quét (trong nghiệp vụ kho có camera hỗ trợ).
OL	Hướng camera vào mã vạch trên thùng/hộp vật tư; hệ thống nhận dạng và mở thông tin lô/vật tư tương ứng.
BODY	Xem thêm về lô và mã vạch ở mục 3.5; về xếp hàng lên kệ ở mục 3.4.
H3	1.2.7	Tài khoản cá nhân & đăng xuất
OL	Mở menu tài khoản ở góc trên bên phải (ảnh đại diện / tên người dùng).
OL	Xem thông tin phiên bản hệ thống khi cần báo lỗi cho bộ phận kỹ thuật.
OL	Chọn **Đăng xuất** khi rời máy, đặc biệt trên máy dùng chung.
H2	1.3	Vai trò của bạn làm được gì
H3	1.3.1	Bảng vai trò — việc làm được — chương nên đọc
FIRST	SupplyCore phân quyền theo vai trò. Bảng dưới đây giúp bạn biết mình thuộc nhóm nào và nên đọc những mục nào.
TABLE	Vai trò|Việc chính làm được|Mục nên đọc
ROW	Quản trị Hệ thống|Cấu hình hệ thống, người dùng, dữ liệu nền; xem mọi module|Chương 2; toàn bộ Chương 3
ROW	Trưởng phòng Vật tư|Duyệt đơn hàng, thanh toán, hợp đồng; theo dõi toàn chuỗi|3.1, 3.2, 3.8, 3.11
ROW	NV Mua sắm|Tạo & theo dõi đơn hàng, quản lý nhà cung cấp|3.1, 3.2
ROW	Thủ kho|Nhập – xuất – tồn, FEFO, chuyển kho, kiểm kê|3.3–3.6, 3.9
ROW	Điều dưỡng / NV Khoa|Yêu cầu vật tư cho khoa, theo dõi tồn khoa|3.7
ROW	Kế toán|Hóa đơn, đối chiếu 3 bên, thanh toán, báo cáo, BHYT|3.7 (BHYT), 3.8
ROW	Kiểm soát Chất lượng|Kiểm tra chất lượng, lô/quarantine, truy xuất, thu hồi|3.3, 3.5, 3.10
H3	1.3.2	Một người dùng có thể có nhiều vai trò
FIRST	Một tài khoản có thể được gán nhiều vai trò cùng lúc (ví dụ vừa là Thủ kho vừa là Kiểm soát Chất lượng). Khi đó Sidebar hợp nhất tất cả chức năng của các vai trò bạn có.
BODY	Giao diện được tinh chỉnh theo vai trò để gọn gàng, nhưng **quyền thực sự nằm ở máy chủ**: kể cả khi nhìn thấy một nút, hệ thống vẫn kiểm tra quyền khi bạn thao tác.
H3	1.3.3	Không thấy chức năng? Liên hệ quản trị viên
FIRST	Nếu bạn không thấy một module, một nút, hoặc bị chặn vào một trang (màn hình "Không có quyền"), nguyên nhân thường là vai trò của bạn chưa được cấp quyền đó.
OL	Ghi lại tên chức năng/đường dẫn bạn cần và thông báo bị chặn (nếu có).
OL	Liên hệ Quản trị Hệ thống để được bổ sung vai trò phù hợp (xem mục 2.1).
NOTE	Nguyên tắc của hệ thống: "không có phận sự thì không thấy" — ẩn bớt chức năng giúp giao diện an toàn và đỡ rối, không phải lỗi.
