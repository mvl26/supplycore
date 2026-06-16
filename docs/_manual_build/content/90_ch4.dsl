# Chương 4 — Tra cứu nhanh
H1	4	Tra cứu nhanh
H2	4.1	Tôi muốn làm X — tra cứu nhanh
FIRST	Bảng dưới đây giúp bạn đi thẳng tới tác vụ cần làm. Cột "Mục" trỏ tới phần hướng dẫn chi tiết.
H3	4.1.1	Nhà cung cấp & Hợp đồng
TABLE	Tôi muốn…|Vào đâu|Mục
ROW	Thêm/sửa nhà cung cấp|M1 → thẻ Nhà cung cấp|3.1
ROW	Đưa NCC vào danh sách đen|M1 → mở NCC → bật danh sách đen|3.1
ROW	Tạo hợp đồng khung|M1 → thẻ Hợp đồng khung → Tạo mới|3.1
ROW	Theo dõi giá trị còn lại của hợp đồng|M1 → mở hợp đồng|3.1
H3	4.1.2	Kế hoạch & Mua sắm
TABLE	Tôi muốn…|Vào đâu|Mục
ROW	Đặt tồn an toàn / điểm tái đặt|M0 → Vật tư (hoặc M2)|3.2
ROW	Lập kế hoạch mua theo kỳ|M2 → Kế hoạch mua sắm|3.2
ROW	Tạo yêu cầu mua (MR)|M2 → Yêu cầu mua → Tạo mới|3.2
ROW	Tạo & trình duyệt đơn hàng (PO)|M2 → Đơn đặt hàng → Tạo mới|3.2
H3	4.1.3	Tiếp nhận & Chất lượng
TABLE	Tôi muốn…|Vào đâu|Mục
ROW	Nhập hàng theo đơn|M3 → Phiếu nhập → Tạo mới|3.3
ROW	Kiểm tra chất lượng lô hàng|M3 → Kiểm tra chất lượng|3.3
ROW	Trả hàng nhà cung cấp|M3 → Phiếu nhập → tạo phiếu trả|3.3
H3	4.1.4	Kho, Lô & FEFO
TABLE	Tôi muốn…|Vào đâu|Mục
ROW	Xem tồn kho thời gian thực|Sidebar → Tồn kho|3.4
ROW	Xếp hàng lên kệ|Sidebar → Xếp hàng lên kệ|3.4
ROW	Xem bản đồ kho|Sidebar → Bản đồ kho|3.4
ROW	Xem lô & hạn dùng|M5 → Lô vật tư|3.5
ROW	Xem vật tư sắp hết hạn|Sidebar → Cảnh báo|3.5, 3.11
H3	4.1.5	Chuyển kho & Cấp phát
TABLE	Tôi muốn…|Vào đâu|Mục
ROW	Chuyển kho nội bộ|M6 → Yêu cầu chuyển kho|3.6
ROW	Nhập phiếu chuyển kho từ HIS (PDF)|Sidebar → Nhập phiếu HIS|3.6
ROW	Tạo yêu cầu vật tư cho khoa|M7 → Yêu cầu cấp phát|3.7
ROW	Cấp phát theo người bệnh (BHYT)|M7 → Cấp phát người bệnh|3.7
H3	4.1.6	Tài chính, Kiểm kê, Truy xuất
TABLE	Tôi muốn…|Vào đâu|Mục
ROW	Nhập hóa đơn & đối chiếu 3 bên|M8 → Hóa đơn mua|3.8
ROW	Tạo phiếu thanh toán|M8 → Phiếu thanh toán|3.8
ROW	Xem báo cáo tài chính|Sidebar → Báo cáo tài chính|3.8
ROW	Kiểm kê & đối chiếu chênh lệch|M9 → Phiếu kiểm kê|3.9
ROW	Truy xuất nguồn gốc lô|Sidebar → Truy xuất lô|3.10
ROW	Thu hồi sản phẩm|M10 → Phiếu thu hồi|3.10
H2	4.2	Câu hỏi thường gặp (FAQ)
BODY	**Hỏi: Tại sao tôi không thấy module/nút mà đồng nghiệp thấy?**
BODY	Đáp: Giao diện hiển thị theo vai trò. Vai trò của bạn chưa được cấp quyền đó. Liên hệ quản trị viên để bổ sung (xem 1.3.3 và 2.1).
BODY	**Hỏi: FEFO là gì và vì sao hệ thống tự chọn lô khi tôi xuất?**
BODY	Đáp: FEFO = "lô hết hạn trước, xuất trước". Khi cấp phát/chuyển kho, hệ thống tự gợi ý/chọn lô có hạn dùng gần nhất để hạn chế vật tư hết hạn (xem 3.5).
BODY	**Hỏi: Vì sao tôi không xuất được một lô nhất định?**
BODY	Đáp: Lô đó có thể đã bị khóa do thu hồi/quarantine hoặc đã hết hạn. Hệ thống chặn để bảo đảm an toàn (mã SC-E008). Kiểm tra trạng thái lô trong M5.
BODY	**Hỏi: Đối chiếu 3 bên là gì?**
BODY	Đáp: Hệ thống so khớp Đơn hàng (PO) – Phiếu nhập (PR) – Hóa đơn (PI). Lệch quá ±1% sẽ yêu cầu giải trình và giữ thanh toán cho tới khi được duyệt (xem 3.8).
BODY	**Hỏi: Vì sao đơn hàng của tôi phải qua nhiều cấp duyệt?**
BODY	Đáp: Đơn vượt ngưỡng (mặc định 50 triệu) cần thêm cấp duyệt; hợp đồng vượt ngưỡng (mặc định 100 triệu) cần cấp cao hơn. Ngưỡng do quản trị viên đặt (xem 2.3).
BODY	**Hỏi: Phần chi trả BHYT được tính thế nào?**
BODY	Đáp: Dựa trên cấu hình mã BHYT N01–N09 (tỷ lệ chi trả, giá trần) áp cho vật tư/nhóm vật tư tại thời điểm cấp phát (xem 2.4 và 3.7).
BODY	**Hỏi: Trung tâm cảnh báo trống có phải lỗi không?**
BODY	Đáp: Không. Trống nghĩa là hiện không có vấn đề cần xử lý — đó là dấu hiệu tốt.
BODY	**Hỏi: Nhập phiếu chuyển kho từ HIS bằng PDF hoạt động ra sao?**
BODY	Đáp: Tải PDF phiếu xuất điều chuyển; hệ thống đọc nội dung (AI hoặc OCR), khớp vật tư/kho và tạo phiếu chuyển kho. Nếu khớp 100% có thể tự nộp; nếu chưa, hệ thống để bản nháp cho bạn rà soát (xem 3.6).
BODY	**Hỏi: Tôi sửa được Sổ kho (Stock Ledger) không?**
BODY	Đáp: Không. Sổ kho được sinh tự động và chỉ-đọc; mọi điều chỉnh tồn phải qua phiếu (nhập, xuất, chuyển, đối chiếu kiểm kê) để bảo đảm truy vết.
H2	4.3	Thuật ngữ
TABLE	Thuật ngữ|Ý nghĩa
ROW	FEFO|First Expiry First Out — lô hết hạn trước được xuất trước
ROW	Lô (Batch)|Một lượng vật tư cùng số lô, cùng hạn dùng, cùng nguồn nhập
ROW	Sổ kho (Stock Ledger)|Nhật ký bất biến mọi biến động tồn kho, sinh tự động
ROW	PR — Phiếu nhập|Phiếu ghi nhận hàng nhận về (SC-PR-…)
ROW	PO — Đơn đặt hàng|Đơn mua gửi nhà cung cấp (SC-PO-…)
ROW	MR — Yêu cầu mua|Đề nghị mua nội bộ (SC-MR-…)
ROW	QC — Kiểm tra chất lượng|Kiểm tra lô hàng trước khi cho phép sử dụng (SC-QI-…)
ROW	Đối chiếu 3 bên|So khớp PO – PR – Hóa đơn trước khi thanh toán
ROW	BHYT|Bảo hiểm y tế; mã nhóm N01–N09 quyết định phần chi trả
ROW	Quarantine|Trạng thái cách ly lô chờ xử lý chất lượng/thu hồi
ROW	Quota khoa|Hạn mức cấp phát theo tháng cho một khoa
ROW	Persona / Vai trò|Bộ quyền và giao diện theo công việc người dùng
H2	4.4	Xử lý sự cố thường gặp
H3	4.4.1	Không đăng nhập được
OL	Kiểm tra đúng địa chỉ hệ thống, tên đăng nhập và mật khẩu (chú ý phím Caps Lock).
OL	Nếu vẫn không được, có thể tài khoản bị khóa — liên hệ quản trị viên để mở lại hoặc đặt lại mật khẩu.
H3	4.4.2	Bị chặn vào trang / không thấy nút (Không có quyền)
OL	Đây là vấn đề phân quyền, không phải lỗi kỹ thuật.
OL	Ghi lại tên chức năng/đường dẫn và liên hệ quản trị viên để bổ sung vai trò (xem 2.1).
H3	4.4.3	Không lưu/nộp được phiếu — bị chặn bởi điều kiện
OL	Đọc kỹ thông báo lỗi: thường nêu rõ trường thiếu hoặc điều kiện chưa thỏa (ví dụ chênh lệch 3 bên, vượt quota, lô bị khóa, kho nguồn trùng kho đích).
OL	Sửa theo hướng dẫn trong thông báo; mã lỗi SC-Exxx có giải thích ở mục module tương ứng (3.x.6).
H3	4.4.4	Không nhận được email thông báo
OL	Kiểm tra thư mục spam và đúng địa chỉ email.
OL	Báo quản trị viên kiểm tra cấu hình máy chủ email (SMTP) và hàng đợi email (xem 2.4).
OL	Trong lúc chờ, dùng Trung tâm cảnh báo trong ứng dụng — vẫn hoạt động bình thường.
H3	4.4.5	Tồn kho / số liệu không khớp
OL	Đối chiếu bằng màn hình Tồn kho và Sổ kho; nhớ rằng tồn chỉ thay đổi qua phiếu.
OL	Nếu có chênh lệch thực tế, lập **Kiểm kê & Đối chiếu** (M9) để điều chỉnh đúng quy trình (xem 3.9).
H3	4.4.6	Quét mã vạch không ra thông tin
OL	Kiểm tra mã còn rõ nét; thử nhập tay số lô để tra.
OL	Nếu lô chưa có trong hệ thống, có thể hàng chưa được nhập kho — kiểm tra lại Phiếu nhập (xem 3.3).
H3	4.4.7	Trang tải chậm hoặc không hiển thị dữ liệu
OL	Tải lại trang; kiểm tra kết nối mạng nội bộ.
OL	Nếu vẫn lỗi, ghi lại đường dẫn, thao tác đang làm và thời điểm, rồi báo bộ phận kỹ thuật kèm thông tin phiên bản (xem 1.2.7).
H3	4.4.8	Khi nào báo quản trị viên / kỹ thuật
UL	Nghi ngờ sai quyền hoặc cần thêm vai trò.
UL	Lỗi lặp lại nhiều lần dù đã làm đúng hướng dẫn.
UL	Số liệu bất thường nghi do dữ liệu bị can thiệp.
UL	Cần thay đổi tham số hệ thống, cấu hình BHYT, hoặc luật cảnh báo.
