# Mục 3.12 — M12 · Cổng khách hàng (Portal). Soạn theo AUTHOR_GUIDE; nhãn lấy đúng từ code.
H2	3.12	M12 · Cổng khách hàng
H3	3.12.1	Mục đích & khi nào dùng
FIRST	Cổng khách hàng là một trang web riêng (đường dẫn `/portal`), thiết kế cho điện thoại, để khách hàng của công ty tự phục vụ: xem hợp đồng khung và bảng giá của mình, tự đặt hàng, theo dõi đơn theo bốn cột mốc, tự xác nhận đã nhận hàng, xem hóa đơn và công nợ, tải chứng từ. Khách không vào giao diện nội bộ và không nhìn thấy bất kỳ dữ liệu nào của khách khác.
BODY	Bạn quan tâm mục này khi: muốn giảm điện thoại và email nhận đơn thủ công; muốn khách tự tra tiến độ đơn thay vì hỏi nhân viên; hoặc khi cần cấp tài khoản Portal cho một khách mới.
NOTE	Cổng khách hàng **không phải một module trong Sidebar nội bộ**. Đây là trang riêng cho khách; nhân viên công ty không dùng trang này để làm việc.
H3	3.12.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Khách hàng đăng nhập bằng tài khoản có vai trò **SC Customer Portal** (không vào được giao diện nội bộ). Về phía công ty, NV Mua & Bán hàng hoặc Quản trị Hệ thống là người tạo tài khoản và gắn tài khoản đó vào đúng hồ sơ Khách hàng.
BODY	**Cần có trước:** hồ sơ **Khách hàng (SC Customer)** đã tạo và đã điền **Tài khoản Portal**. Nếu bán theo hợp đồng: **HĐ khung bán** còn hiệu lực. Nếu bán lẻ theo giá niêm yết: vật tư đã bật cho phép bán online và có **Giá bán**.
H3	3.12.3	Các bước thực hiện
H4	3.12.3.1	Cấp tài khoản Portal cho khách (phía công ty)
OL	Tạo tài khoản người dùng cho khách (xem mục 2.1), gán vai trò **SC Customer Portal**.
OL	Mở hồ sơ **Khách hàng** tương ứng, điền **Tài khoản Portal** đúng email vừa tạo, rồi **Lưu**.
OL	Gửi khách đường dẫn `/portal` cùng thông tin đăng nhập.
WARN	Một tài khoản Portal chỉ được gắn với **đúng một** khách hàng. Gán một tài khoản cho hai khách sẽ bị hệ thống chặn — đây là hàng rào chống rò rỉ dữ liệu chéo.
H4	3.12.3.2	Khách xem hợp đồng & bảng giá
OL	Khách đăng nhập, vào tab hồ sơ để xem thông tin công ty mình, **Hạn mức tín dụng** và **Dư nợ** hiện tại.
OL	Mở tab danh mục: hệ thống chỉ hiện **hợp đồng khung còn hiệu lực của chính khách đó**, kèm bảng giá và số lượng còn lại theo từng vật tư (hiển thị **tên vật tư**, không chỉ mã).
OL	Nếu công ty có mở danh mục bán online chung, khách xem thêm được các vật tư bán lẻ theo giá niêm yết.
IMG	Cổng khách hàng trên điện thoại: tab danh mục với hợp đồng khung và bảng giá.
H4	3.12.3.3	Khách tự đặt hàng
OL	Khách chọn hợp đồng khung (hoặc danh mục bán lẻ), chọn vật tư và nhập số lượng vào giỏ.
OL	Bấm gửi đơn. Hệ thống tạo **Đơn hàng bán** ở trạng thái Chờ duyệt, với **đơn giá tính lại phía máy chủ** theo hợp đồng — giá khách gửi lên không được tin.
OL	Đơn xuất hiện ngay trong danh sách Đơn hàng bán của nhân viên để duyệt.
NOTE	Hệ thống chặn ngay tại bước đặt nếu: số lượng nhỏ hơn hoặc bằng 0, hợp đồng khung đã hết hiệu lực, vượt số lượng trần hợp đồng, vượt hạn mức tín dụng, hoặc kho không đủ tồn khả dụng. Khách thấy thông báo lý do cụ thể thay vì đơn treo.
H4	3.12.3.4	Khách theo dõi đơn theo bốn cột mốc
OL	Mở tab đơn hàng, chọn một đơn để xem thanh tiến độ bốn mốc: (1) Đã đặt hàng, (2) Đã bàn giao và nghiệm thu, (3) Đã cấp hóa đơn, (4) Đã thu tiền.
OL	Ở mốc (2) và (3), khách bấm liên kết để tải chứng từ tương ứng (Phiếu giao hàng, Biên bản nghiệm thu, Hóa đơn bán).
OL	Dùng nút **Quay lại**, **Tiến tới** và **Làm mới dữ liệu** ở đầu trang để di chuyển và cập nhật số liệu.
IMG	Thanh tiến độ bốn cột mốc của một đơn hàng trên Cổng khách hàng.
BODY	Nếu đơn bị **Từ chối**, cổng hiển thị rõ trạng thái đó và chuỗi mốc dừng lại — không mốc nào được coi là "đang ở đây".
H4	3.12.3.5	Khách tự nghiệm thu
OL	Khi phiếu giao hàng đã ở trạng thái **Đã giao**, khách thấy nút **Lập nghiệm thu** trên đơn tương ứng.
OL	Bấm nút, kiểm tra lại thông tin rồi bấm **Xác nhận nghiệm thu** (hoặc **Hủy** nếu bấm nhầm).
OL	Hệ thống tạo và nộp **Biên bản nghiệm thu** thay cho khách. Từ đây kế toán xuất được hóa đơn.
NOTE	Đây là cách rút ngắn vòng quay tiền: khách xác nhận trên điện thoại ngay khi nhận hàng, kế toán không phải chờ biên bản giấy quay về mới xuất hóa đơn.
H4	3.12.3.6	Khách vãng lai tự đăng ký
OL	Khách chưa có tài khoản dùng chức năng đăng ký trên trang `/portal`.
OL	Hệ thống tạo tài khoản website, tạo hồ sơ **Khách hàng** ở trạng thái Hoạt động đã gắn sẵn tài khoản, và gán vai trò Portal.
OL	Nhân viên công ty rà lại hồ sơ khách mới (mã số thuế, địa chỉ, hạn mức tín dụng) trước khi duyệt đơn đầu tiên.
H3	3.12.4	Cô lập dữ liệu giữa các khách
FIRST	Đây là yêu cầu bảo mật quan trọng nhất của Cổng khách hàng. Trục cô lập là: **hồ sơ Khách hàng nào có Tài khoản Portal trùng với người đang đăng nhập** thì đó là khách của phiên làm việc này.
BODY	Hệ thống **không bao giờ tin** tham số khách hàng do trình duyệt gửi lên — mọi lệnh gọi từ cổng đều tự xác định khách từ phiên đăng nhập. Ngoài ra có nhiều lớp chặn độc lập: lọc danh sách theo khách trên sáu loại chứng từ bán và bốn bảng chi tiết; chặn đọc từng chứng từ của khách khác; chặn đọc trực tiếp dòng chi tiết; chặn các đường gọi dữ liệu thô; và chặn tài khoản Portal khỏi toàn bộ chức năng nội bộ (chỉ số, báo cáo tài chính, phê duyệt, truy xuất, kho, xuất dữ liệu hàng loạt).
TABLE	Khách hàng KHÔNG thể|Vì sao
ROW	Xem đơn hàng, hóa đơn, công nợ của khách khác|Mọi truy vấn tự lọc theo khách của phiên đăng nhập
ROW	Tự duyệt đơn hàng của chính mình|Chức năng duyệt bị chặn với vai trò Portal
ROW	Sửa giá, sửa số lượng sau khi đặt|Vai trò Portal không có quyền ghi lên chứng từ
ROW	Xuất dữ liệu hàng loạt|Các chức năng xuất dữ liệu chặn vai trò Portal
ROW	Vào giao diện nội bộ (Desk)|Vai trò Portal không có quyền truy cập Desk
WARN	Khi khách nghỉ hợp tác hoặc người liên hệ bên khách nghỉ việc, hãy **tắt tài khoản** đó ngay (mục 2.1). Chỉ gỡ vai trò mà quên tắt tài khoản là chưa đủ an toàn.
H3	3.12.5	Kết quả & truy vết
UL	Đơn khách đặt qua cổng tạo **Đơn hàng bán (SC-SO-…)** giống hệt đơn nhân viên nhập tay — cùng một luồng duyệt, cùng một quy tắc.
UL	Khách tự nghiệm thu tạo **Biên bản nghiệm thu (SC-AR-…)** đã nộp, ghi rõ người xác nhận.
UL	Khách vãng lai đăng ký tạo tài khoản website và hồ sơ **Khách hàng** mới.
UL	Mọi thao tác trên cổng đều ghi vào lịch sử bản ghi theo tài khoản đăng nhập, phục vụ đối chiếu khi có tranh chấp.
H3	3.12.6	Lỗi thường gặp & mẹo
UL	**Khách đăng nhập được nhưng không thấy dữ liệu gì:** hồ sơ Khách hàng chưa điền **Tài khoản Portal**, hoặc điền sai email. Kiểm tra lại trên hồ sơ khách.
UL	**Khách báo không đặt được hàng:** kiểm tra theo thứ tự — hợp đồng khung còn hiệu lực không, SL còn lại của vật tư đó, hạn mức tín dụng và dư nợ, cuối cùng là tồn kho khả dụng.
UL	**Khách không thấy nút nghiệm thu:** phiếu giao hàng chưa được thủ kho nộp; phải soạn hàng và quét xác nhận đủ trước.
UL	**Một tài khoản đã gắn khách khác:** mỗi tài khoản Portal chỉ gắn một khách; tạo tài khoản riêng cho khách mới.
UL	**Mẹo —** hướng dẫn khách lưu `/portal` ra màn hình chính điện thoại để dùng như một ứng dụng.
UL	**Mẹo —** khi khách hỏi "đơn của tôi đến đâu rồi", hãy chỉ họ vào thanh bốn cột mốc thay vì tra hộ — vừa nhanh cho khách vừa giảm việc cho nhân viên.
H3	3.12.7	Liên quan
UL	Xem 3.7 — M7 Bán hàng & Bàn giao (toàn bộ chuỗi chứng từ phía sau mỗi đơn khách đặt).
UL	Xem 2.1 — Quản lý người dùng & phân quyền (tạo, tắt tài khoản Portal).
UL	Xem 3.8 — M8 Kế toán (công nợ phải thu mà khách nhìn thấy trên cổng).
