# Mục 3.6 — M6 · Chuyển kho. Soạn theo AUTHOR_GUIDE; nhãn lấy đúng từ code.
H2	3.6	M6 · Chuyển kho
H3	3.6.1	Mục đích & khi nào dùng
FIRST	Module M6 dùng để luân chuyển vật tư giữa các kho trong nội bộ công ty: từ Kho tổng sang Kho phụ, từ Kho phụ xuống kho phân phối khu vực, hoặc trả hàng ngược về Kho chính. Mỗi lần chuyển được lập thành một **Phiếu luân chuyển** (SC Transfer Request, mã SC-TR-…); khi phiếu được duyệt và xác nhận xuất, hệ thống tự sinh một bút toán kho **Material Transfer** để trừ tồn ở kho nguồn và cộng tồn ở kho đích.
BODY	Bạn dùng M6 khi: bổ sung hàng cho kho phân phối khu vực (Replenishment), điều phối khẩn giữa các kho (Urgent), chuyển định kỳ theo kế hoạch (Routine), hoặc thu hồi hàng tồn về kho chính (Return to Main).
H3	3.6.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Thủ kho (SupplyCore Storekeeper / Warehouse Officer) lập và nộp phiếu, tạo bút toán xuất. Trưởng phòng (SupplyCore Manager) bắt buộc cho các phiếu chuyển liên tầng (cross-tier) có liên quan kho phân phối khu vực.
BODY	**Cần có trước:** Kho nguồn và kho đích đã khai báo trong Dữ liệu nền (không phải kho nhóm, không bị ngừng dùng); vật tư cần chuyển đã có mã trong SC Item; kho nguồn còn đủ tồn khả dụng (không tính lô đang chờ QC, bị từ chối hoặc bị khóa).
H3	3.6.3	Các bước thực hiện
H4	3.6.3.1	Lập phiếu luân chuyển mới
OL	Từ Trang chủ, mở **M6**, bấm thẻ **SC Transfer Request** rồi nhấn **Tạo mới** (hoặc vào **Danh sách** rồi **Tạo mới**).
OL	Điền **Ngày yêu cầu**, **Loại chuyển kho** (Routine / Urgent / Replenishment / Return to Main) và **Ngày cần**. Có thể chọn **Người yêu cầu** và **Phòng ban yêu cầu**.
OL	Tại mục **Kho nguồn → Kho đích**, chọn **Kho nguồn** và **Kho đích** (phải khác nhau — xem lỗi SC-E024 ở mục 3.6.6).
OL	Trong bảng **Vật tư cần chuyển**, thêm từng dòng: **Mã VT**, **UOM**, **SL yêu cầu**. Ô **Tên** tự điền theo mã. Để trống **Lô** nếu muốn hệ thống tự chọn theo FEFO; nhập **SL duyệt** nếu muốn duyệt khác số yêu cầu.
OL	Nhấn **Lưu**. Hệ thống chụp tồn kho nguồn vào cột **Tồn tại kho nguồn** và tính **Tổng SL yêu cầu**.
IMG	Màn hình tạo phiếu luân chuyển với mục Kho nguồn → Kho đích và bảng Vật tư cần chuyển.
NOTE	Nếu kho đích (hoặc kho nguồn) là kho phân phối khu vực, ô **Cần phê duyệt Manager** sẽ tự bật; phiếu trở thành chuyển liên tầng và chỉ Trưởng phòng mới nộp được.
H4	3.6.3.2	Nộp & duyệt phiếu
OL	Mở phiếu ở trạng thái **Nháp**, kiểm tra lại các dòng vật tư và **SL duyệt**.
OL	Nhấn **Nộp**. Khi nộp thành công, trạng thái chuyển sang **Đã duyệt (Approved)**, hệ thống ghi **Người duyệt** và **Thời điểm duyệt**.
OL	Với phiếu liên tầng, nếu tài khoản của bạn không có quyền Trưởng phòng, hệ thống chặn bằng lỗi SC-E-TRANSFER-MANAGER-REQUIRED; hãy chuyển cho người có vai trò phù hợp nộp.
WARN	Khi nộp, hệ thống kiểm tra **SL duyệt** từng dòng không được vượt tồn kho nguồn. Nếu vượt sẽ báo SC-E-TRANSFER-INSUFFICIENT kèm số lượng tối đa có thể chuyển.
H4	3.6.3.3	Tạo bút toán xuất kho (Material Transfer) & nhận hàng
FIRST	Sau khi phiếu ở trạng thái **Đã duyệt**, Thủ kho tạo bút toán kho để thực sự chuyển tồn.
OL	Mở phiếu đã duyệt, chạy lệnh tạo Stock Entry. Hệ thống sinh một **SC Stock Entry** loại **Material Transfer** ở dạng nháp, liên kết về phiếu này.
OL	Với vật tư quản lý lô mà dòng không chỉ định **Lô**, hệ thống tự chọn lô theo **FEFO** (hết hạn trước — xuất trước); phần tồn cũ chưa gắn lô được chuyển nguyên trạng. Trạng thái phiếu chuyển sang **Đang chuyển (In Transit)**.
OL	Mở **SC Stock Entry** vừa tạo, kiểm tra các dòng/lô rồi **Nộp**. Khi đó tồn kho nguồn bị trừ, tồn kho đích được cộng (ghi vào Sổ kho), cột **SL đã chuyển** trên phiếu được cập nhật và trạng thái phiếu chuyển thành **Đã nhận (Received)**.
IMG	Phiếu luân chuyển đã duyệt và bút toán Material Transfer sinh kèm.
NOTE	Nếu hủy bút toán Stock Entry, phiếu tự quay lại trạng thái **Đã duyệt** và **SL đã chuyển** về 0 để bạn xử lý lại.
H3	3.6.4	Trạng thái & phê duyệt
FIRST	Vòng đời phiếu luân chuyển: Nháp → (Đã duyệt khi nộp) → Đang chuyển (khi tạo bút toán) → Đã nhận (khi nộp bút toán). Phiếu chuyển liên tầng tới kho phân phối khu vực cần vai trò Trưởng phòng mới nộp được.
TABLE	Trạng thái|Ý nghĩa|Ai thực hiện
ROW	Nháp (Draft)|Đang soạn, chưa nộp; có thể sửa/xóa|Thủ kho
ROW	Chờ duyệt (Pending Approval)|Phiếu liên tầng chờ Trưởng phòng nộp/duyệt|Trưởng phòng
ROW	Đã duyệt (Approved)|Đã nộp, đã ghi Người duyệt; sẵn sàng tạo bút toán|Hệ thống khi nộp
ROW	Đang chuyển (In Transit)|Đã sinh bút toán Material Transfer (nháp), chờ nộp|Thủ kho
ROW	Đã nhận (Received)|Bút toán đã nộp, tồn đã chuyển sang kho đích|Hệ thống khi nộp SE
ROW	Đã hủy (Cancelled)|Phiếu bị hủy (phải hủy bút toán Stock Entry trước nếu có)|Thủ kho / Manager
H3	3.6.5	Kết quả & truy vết
UL	Tạo bản ghi phiếu luân chuyển mã **SC-TR-YYYY-#####**.
UL	Khi nộp bút toán, sinh **SC Stock Entry** loại **Material Transfer** và ghi vào **Sổ kho (Stock Ledger)**: trừ tồn kho nguồn, cộng tồn kho đích; cập nhật **SL đã chuyển** từng dòng.
UL	Lưu **Người duyệt**, **Thời điểm duyệt**, và liên kết tới Stock Entry trên phiếu.
H3	3.6.6	Lỗi thường gặp & mẹo
UL	**SC-E024 SAME_WAREHOUSE — Kho nguồn trùng kho đích:** chọn lại hai kho khác nhau (chuyển trong cùng một kho tạo bút toán ảo làm sai số liệu).
UL	**SC-E-TRANSFER-MANAGER-REQUIRED — Phiếu liên tầng cần Manager:** phiếu liên quan kho phân phối khu vực phải do Trưởng phòng nộp.
UL	**SC-E-TRANSFER-INSUFFICIENT — SL duyệt vượt tồn:** giảm SL duyệt xuống tối đa bằng tồn kho nguồn được báo.
UL	**SC-E-TRANSFER-SHORTAGE — Kho nguồn không đủ để FEFO chọn:** kiểm tra lại tồn theo lô; bổ sung tồn hoặc giảm số lượng.
UL	**Ngày cần phải sau hoặc bằng Ngày yêu cầu:** sửa lại Ngày cần.
UL	**Phải cancel SC Stock Entry trước:** muốn hủy phiếu đã có bút toán đã nộp thì hủy bút toán Stock Entry trước.
UL	**Mẹo —** dùng nút **Xuất** ở màn hình Danh sách để tải danh sách phiếu luân chuyển ra Excel.
H3	3.6.7	Liên quan
UL	Xem Chương 2 — Dữ liệu nền (khai báo SC Item, SC Warehouse).
UL	Xem mục Tồn kho & FEFO để hiểu cách chọn lô hết hạn trước và tồn khả dụng.
UL	Xem mục Bút toán kho (SC Stock Entry) cho chi tiết loại giao dịch Material Transfer.
UL	Xem 3.3 — Tiếp nhận & Kiểm tra chất lượng (lô đang chờ QC không tính vào tồn khả dụng để chuyển).
