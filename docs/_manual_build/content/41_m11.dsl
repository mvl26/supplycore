# SupplyCore — Hướng dẫn sử dụng — Mục 3.11 (M11 Dashboard & Cảnh báo)
# Nguồn: kpi.py, sc_alert(.json/.py), sc_alert_rule(.json), Dashboard.vue, AlertCenter.vue, UC-32/33/34_FLOW.md
H2	3.11	M11 · Dashboard & Cảnh báo
H3	3.11.1	Mục đích & khi nào dùng
FIRST	Module M11 là "buồng lái" của SupplyCore: nó gộp toàn bộ số liệu vận hành thành các thẻ chỉ số (KPI) trên màn hình Tổng quan và biến những việc cần xử lý gấp thành Cảnh báo. Bạn vào đây mỗi đầu ca làm việc để nắm nhanh tình hình kho — tiền hàng, công nợ, lô sắp hết hạn, vật tư xuống dưới tồn an toàn, hợp đồng sắp đáo hạn — rồi mở Trung tâm cảnh báo để xử lý từng cảnh báo (xác nhận, tạm ẩn, phân công). M11 không tự tạo phiếu nghiệp vụ; nó chỉ tổng hợp, nhắc việc và dẫn bạn tới đúng bản ghi cần thao tác ở các module khác.
BODY	Dashboard hiển thị **theo chân dung (persona)**: mỗi vai trò chỉ thấy những KPI và lối tắt liên quan đến công việc của mình, nên hai người dùng khác vai trò mở cùng một trang sẽ thấy hai bố cục khác nhau. Toàn bộ số liệu được lưu đệm (cache) 5 phút để tải nhanh; bấm nút tải lại để lấy số mới nhất.
H3	3.11.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Tất cả các vai trò đều có Dashboard và Trung tâm cảnh báo riêng theo chân dung — Quản trị Hệ thống, Trưởng phòng Vật tư, NV Mua sắm, Thủ kho, Điều dưỡng/NV Khoa, Kế toán, Kiểm soát Chất lượng. Mọi vai trò được **xem và xử lý** cảnh báo (xác nhận, tạm ẩn, phân công); riêng **Điều dưỡng/NV Khoa** chỉ được xem cảnh báo. Việc **cấu hình Quy tắc cảnh báo (SC Alert Rule)** chỉ dành cho **Quản trị Hệ thống** và **Trưởng phòng Vật tư**.
BODY	**Cần có trước:** Hệ thống đã có dữ liệu vận hành (Sổ kho, Hóa đơn mua, Đơn đặt hàng, Hợp đồng khung, Lô, Cảnh báo) thì các KPI mới có số. Để cảnh báo được sinh tự động và gửi đi, cần ít nhất một **Quy tắc cảnh báo** đang bật; gửi Email cần Tài khoản Email đã cấu hình, gửi SMS cần khai báo **sms_gateway_endpoint** trong SupplyCore Settings.
H3	3.11.3	Các bước thực hiện
H4	3.11.3.1	Xem & lọc KPI Dashboard
OL	Sau khi đăng nhập, hệ thống mở thẳng **Tổng quan** (đường dẫn `/dashboard`, mã màn hình SCR-01). Tiêu đề trang ghi rõ chân dung của bạn, ví dụ "Dashboard — Thủ kho".
OL	Đọc các thẻ KPI ở đầu trang. Tùy chân dung bạn sẽ thấy một phần trong các thẻ: **Tổng giá trị tồn kho**, **Chi phí mua kỳ này**, **Công nợ NCC**, **PO đang chờ**, **Lô sắp hết hạn (30 ngày)**, **Vật tư dưới tồn an toàn**, **HĐ sắp hết hạn**, **PO quá hạn giao**.
OL	Bấm vào một thẻ KPI để **đi sâu (drill-down)** sang danh sách bản ghi tương ứng, ví dụ bấm "PO đang chờ" sẽ mở danh sách Đơn đặt hàng.
OL	Dùng các bộ lọc ở góc trên phải để thu hẹp số liệu: ô **— Tất cả kho —** (lọc theo kho), ô **— Tất cả khoa —** (lọc theo khoa/phòng), và ô kỳ thời gian gồm **Hôm nay**, **Tuần này**, **Tháng này**, **Quý này**, **Năm nay**.
OL	Nếu cần xem nhanh bố cục của vai trò khác, mở ô chọn **Theo chân dung** và chọn một vai trò (View đầy đủ (Executive), Vai trò Quản lý, Vai trò Kế toán, Vai trò Thủ kho, Vai trò Dược viên). Đây chỉ là lăng kính hiển thị, không mở thêm quyền.
OL	Cuộn xuống để xem biểu đồ **Xu hướng chi phí 12 tháng**, ô **Cảnh báo đang mở** (bấm "Tất cả →" để sang Trung tâm cảnh báo) và bảng **Top 10 vật tư tiêu thụ**. Cả biểu đồ và bảng đều có nút **CSV** để tải dữ liệu.
OL	Khi số liệu có vẻ cũ (dòng phụ đề ghi "đã cache 5 phút"), bấm nút tải lại để truy vấn số mới nhất bỏ qua bộ đệm.
IMG	Màn hình Tổng quan với hàng thẻ KPI, biểu đồ xu hướng chi phí 12 tháng và bảng Top 10 vật tư tiêu thụ.
NOTE	Các thẻ lối tắt (quick-action) hiện ngay trên hàng KPI cũng đổi theo chân dung — ví dụ Thủ kho thấy **Xếp hàng lên kệ**, **Cấp phát FEFO**, **Kiểm kê**, **Bản đồ kho**; Kế toán thấy **Hóa đơn mới**, **Phiếu thanh toán**, **Báo cáo tài chính**. Bấm thẻ để đi thẳng tới tác vụ đó.
H4	3.11.3.2	Xuất Snapshot PDF của Dashboard
OL	Trên trang Tổng quan, đặt sẵn kỳ thời gian và kho mong muốn (bộ lọc khoa không áp dụng cho bản snapshot).
OL	Bấm nút **Snapshot PDF** ở góc trên phải. Một hộp thoại "SupplyCore — Dashboard Snapshot" hiện ra, kèm thời điểm tạo, người tạo, kỳ báo cáo, các KPI, bảng Top vật tư và ô chữ ký cho Lãnh đạo / Trưởng phòng / Kế toán.
OL	Bấm **In / Xuất PDF** để mở hộp thoại in của trình duyệt; chọn "Save as PDF" để lưu file, hoặc **Đóng** để thoát.
IMG	Hộp thoại Snapshot Dashboard trước khi in ra PDF.
H4	3.11.3.3	Xem & xử lý cảnh báo trong Trung tâm cảnh báo
OL	Mở **Trung tâm cảnh báo** từ thanh bên (mục Cảnh báo) hoặc đường dẫn `/alerts` (mã màn hình SCR-13). Mặc định hiển thị các cảnh báo **Đang mở**.
OL	Lọc danh sách bằng các nút **Đang mở**, **Đã xử lý**, **Tất cả**; lọc theo mức độ **Nghiêm trọng**, **Cảnh báo**, **Thông tin** (hoặc **Tất cả mức**); gõ vào ô **Tìm theo tiêu đề...** và đổi cách sắp xếp (Ngày cảnh báo, Mức độ, Tiêu đề, Cập nhật).
OL	Mỗi cảnh báo hiện một thẻ với badge mức độ, tiêu đề, nội dung, thời điểm và (nếu có) các nhãn **ĐÃ ĐẨY LÊN**, **Đã xử lý**, **Tạm ẩn**, hoặc tên người được phân công.
OL	Bấm dòng tham chiếu (biểu tượng liên kết, ví dụ "SC Batch …" hay "SC Purchase Invoice …") để **mở thẳng bản ghi gốc** liên quan tới cảnh báo.
OL	Với cảnh báo chưa xử lý, dùng các nút hành động bên phải thẻ: **Xử lý** (đánh dấu đã xử lý kèm ghi chú hành động), **Tạm ẩn** (nhập số giờ và lý do để tạm ẩn), **Phân công** (nhập email người phụ trách để chuyển việc).
OL	Trong hộp thoại tương ứng, điền thông tin rồi bấm **Xác nhận** (hoặc **Hủy**). Hệ thống báo thành công và làm mới danh sách.
IMG	Trung tâm cảnh báo: danh sách thẻ cảnh báo theo mức độ với các nút Xử lý / Tạm ẩn / Phân công.
NOTE	"Tạm ẩn" chỉ làm cảnh báo tạm biến khỏi đếm "đang mở" cho tới thời điểm hết hạn ẩn; cảnh báo sẽ hiện lại nếu điều kiện vẫn còn. "Phân công" tạo thêm một việc (ToDo) cho người được giao và gửi email nhắc.
H4	3.11.3.4	Cấu hình Quy tắc cảnh báo (SC Alert Rule)
OL	Quy tắc cảnh báo được cấu hình ở màn hình quản trị DocType **SC Alert Rule** (đường dẫn `/app/sc-alert-rule`), chỉ Quản trị Hệ thống và Trưởng phòng Vật tư mở được. Bấm **New** để tạo quy tắc mới.
OL	Nhập **Tiêu đề**, chọn **Loại cảnh báo** trong 7 loại (low_stock — hết hàng; expiring_batch — lô sắp hết hạn; contract_expiring — hợp đồng sắp hết; fc_remaining_low — hợp đồng khung còn ít hạn mức; overdue_payment — thanh toán quá hạn; qc_pending — chờ kiểm chất lượng; recall_outstanding — thu hồi chưa xong) và đặt **Mức độ** (Critical/Warning/Info).
OL	Đặt **Ngưỡng**: **Giá trị ngưỡng**, **Phép so sánh** (<, <=, =, >=, >) và **Đơn vị** (days/percent/VND/qty). Ví dụ 30 ngày cho lô sắp hết hạn hoặc hợp đồng sắp hết.
OL	Chọn **Kênh gửi cảnh báo**: tick **Email**, **In-app notification** (tạo cảnh báo trong Trung tâm cảnh báo), và/hoặc **SMS**; nếu bật SMS phải nhập **Số điện thoại SMS** (phân cách dấu phẩy).
OL	Khai **Người nhận**: nhập **Roles nhận** (ví dụ SupplyCore Manager, SupplyCore Storekeeper) và/hoặc **Email bổ sung**.
OL	Đặt **Tần suất quét** (Daily / Hourly / Realtime / Weekly), **Giờ chạy** cho Daily/Weekly (mặc định 08:00) và **Thứ trong tuần** nếu chọn Weekly.
OL	Bấm nút **Test Alert** để gửi thử một thông báo trên từng kênh đang bật; kết quả test (Success / Partial / Failed) và lỗi chi tiết được lưu vào mục "Kết quả test gần nhất".
OL	Bấm **Save**. Quy tắc bật (**Đang sử dụng**) sẽ được bộ quét cảnh báo theo lịch dùng ngay từ lần chạy kế tiếp.
IMG	Màn hình SC Alert Rule với mục Ngưỡng, Kênh gửi và nút Test Alert.
WARN	Phải bật ít nhất một kênh và có ít nhất một người nhận, nếu không hệ thống sẽ chặn lưu (SC-E-AR-NO-CHANNEL / SC-E-AR-NO-RECIPIENT). Bật SMS mà bỏ trống số điện thoại sẽ báo SC-E-AR-SMS-NO-PHONES.
H3	3.11.4	Trạng thái & vòng đời cảnh báo
FIRST	Cảnh báo (SC Alert) không có quy trình phê duyệt, nhưng có vòng đời từ lúc sinh ra tới lúc đóng. Một cảnh báo có thể được đẩy lên (escalate) tự động nếu để quá lâu, và có thể tự đóng khi điều kiện không còn.
TABLE	Trạng thái|Ý nghĩa|Ai/điều kiện chuyển
ROW	Đang mở (resolved = 0)|Cảnh báo mới sinh, cần xử lý; tính vào "Cảnh báo đang mở" trên Dashboard.|Bộ quét theo lịch tạo tự động từ Quy tắc cảnh báo.
ROW	Tạm ẩn (snooze)|Tạm ẩn khỏi danh sách "đang mở" đến thời điểm hết hạn ẩn, kèm lý do.|Người dùng bấm **Tạm ẩn**.
ROW	Đã phân công|Đã giao cho một người phụ trách (tạo ToDo + email).|Người dùng bấm **Phân công**.
ROW	Đã đẩy lên (escalated)|Cảnh báo Critical/Warning quá 48 giờ chưa xử lý: nâng mức lên Critical và gửi cho cấp trên (Executive/Manager).|Bộ lập lịch escalate_overdue_alerts chạy hằng ngày.
ROW	Đã xử lý (resolved = 1)|Đã đóng; ghi người xử lý, thời điểm và hành động (Acknowledged / Acted Upon / Dismissed / Escalated).|Người dùng bấm **Xử lý**, hoặc hệ thống tự đóng (auto-resolve) khi điều kiện không còn.
BODY	**Mức độ (severity):** Critical = **Nghiêm trọng** (đỏ), Warning = **Cảnh báo** (vàng), Info = **Thông tin** (xanh). Cảnh báo HĐ sắp hết hạn và PO quá hạn giao được tô đỏ trên Dashboard khi số lượng lớn hơn 0.
H3	3.11.5	Kết quả & truy vết
UL	Mỗi cảnh báo là một bản ghi **SC Alert** mã **SC-ALR-{NĂM}-{########}**, lưu loại, mức độ, tiêu đề, nội dung, liên kết tham chiếu (DocType + Document), người xử lý và thời điểm xử lý.
UL	Mỗi quy tắc là một bản ghi **SC Alert Rule** mã **SC-AR-{#####}**, lưu cấu hình ngưỡng, kênh, người nhận, tần suất và kết quả test gần nhất (last_test_at / last_test_status / last_test_error).
UL	Khi bấm **Xử lý** trên một cảnh báo low_stock đã có Yêu cầu mua liên kết, hệ thống có thể tạo **SC Purchase Order** nháp; cảnh báo overdue_payment tạo **SC Payment Entry** nháp; cảnh báo expiring_batch tạo **SC Stock Entry** (Material Transfer) chuyển lô vào Kho Cách ly QC — các liên kết này lưu ở trường "Document đã tạo".
UL	Dashboard không tạo bản ghi; nó chỉ đọc Sổ kho (SC Stock Ledger Entry), Hóa đơn mua, Đơn đặt hàng, Hợp đồng khung, Lô và Cảnh báo. Bản **Snapshot PDF** in ra qua trình duyệt, không lưu vào hệ thống.
UL	Mọi cảnh báo gửi qua Email đi qua Hàng đợi Email của Frappe (tự động thử lại khi máy chủ thư trở lại).
H3	3.11.6	Lỗi thường gặp & mẹo
UL	**SC-E-DSH-INVALID-PERIOD —** kỳ thời gian không hợp lệ: chỉ dùng các lựa chọn có sẵn trong ô kỳ (Hôm nay/Tuần này/Tháng này/Quý này/Năm nay).
UL	**SC-E-DSH-INVALID-WAREHOUSE —** kho lọc không tồn tại: chọn lại kho từ danh sách.
UL	**SC-E-AR-NO-CHANNEL —** chưa chọn kênh gửi: tick ít nhất một trong Email / In-app / SMS.
UL	**SC-E-AR-NO-RECIPIENT —** chưa có người nhận: nhập Roles nhận hoặc Email bổ sung (hoặc số SMS).
UL	**SC-E-AR-SMS-NO-PHONES —** đã bật SMS nhưng bỏ trống số điện thoại: nhập danh sách số, phân cách dấu phẩy.
UL	**SC-E-ALERT-RESOLVED —** thao tác trên cảnh báo đã đóng: chỉ Tạm ẩn/Phân công/Xử lý được cảnh báo còn đang mở.
UL	**SC-E-ALERT-SNOOZE-HOURS —** số giờ tạm ẩn phải lớn hơn 0.
UL	**SC-E-ALERT-NO-USER —** email người phân công không tồn tại trong hệ thống: kiểm tra lại đúng tài khoản người dùng.
UL	**Mẹo —** Số liệu cũ là do bộ đệm 5 phút; bấm nút tải lại để lấy số mới nhất ngay lập tức.
UL	**Mẹo —** Trước khi bật một Quy tắc cảnh báo mới cho cả phòng, hãy bấm **Test Alert** để chắc chắn Email/SMS gửi được, tránh quy tắc "câm".
UL	**Mẹo —** Dùng nút **CSV** dưới biểu đồ xu hướng và bảng Top 10 vật tư để xuất dữ liệu sang Excel làm báo cáo.
UL	**Mẹo —** Cảnh báo bị "Tạm ẩn" vẫn còn trong hệ thống; chọn bộ lọc **Tất cả** trong Trung tâm cảnh báo để thấy lại.
H3	3.11.7	Liên quan
UL	Xem 3.5 — M5 · Lô vật tư & FEFO (nguồn cảnh báo lô sắp hết hạn).
UL	Xem 3.4 — M4 · Quản lý kho (nguồn cảnh báo vật tư dưới tồn an toàn).
UL	Xem 3.1 — M1 · Hợp đồng khung (nguồn cảnh báo hợp đồng sắp hết hạn và hạn mức còn ít).
UL	Xem 3.8 — M8 · Kế toán (nguồn cảnh báo thanh toán quá hạn và KPI công nợ).
UL	Xem 3.2 — M2 · Kế hoạch & Mua sắm (nguồn KPI PO đang chờ và PO quá hạn giao).
