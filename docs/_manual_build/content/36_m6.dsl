# Mục 3.6 — M6 · Chuyển kho (và nhập phiếu HIS). Soạn theo AUTHOR_GUIDE; nhãn lấy đúng từ code.
H2	3.6	M6 · Chuyển kho
H3	3.6.1	Mục đích & khi nào dùng
FIRST	Module M6 dùng để luân chuyển vật tư giữa các kho trong nội bộ bệnh viện: từ Kho tổng sang Kho phụ, từ Kho phụ xuống kho Khoa phòng, hoặc trả hàng ngược về Kho chính. Mỗi lần chuyển được lập thành một **Phiếu luân chuyển** (SC Transfer Request, mã SC-TR-…); khi phiếu được duyệt và xác nhận xuất, hệ thống tự sinh một bút toán kho **Material Transfer** để trừ tồn ở kho nguồn và cộng tồn ở kho đích.
BODY	Bạn dùng M6 khi: cấp bổ sung vật tư cho kho khoa (Replenishment), điều phối khẩn giữa các kho (Urgent), chuyển định kỳ theo kế hoạch (Routine), hoặc thu hồi hàng tồn về kho chính (Return to Main). Ngoài lập phiếu thủ công, M6 còn cho phép **nhập tự động từ phiếu xuất điều chuyển của HIS** (file PDF) — xem mục 3.6.3.4.
H3	3.6.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Thủ kho (SupplyCore Storekeeper / Warehouse Officer) lập và nộp phiếu, tạo bút toán xuất. Trưởng phòng Vật tư (SupplyCore Manager) bắt buộc cho các phiếu chuyển liên tầng (cross-tier) có liên quan kho Khoa phòng. Điều dưỡng / NV Khoa có thể tạo phiếu yêu cầu cho khoa của mình.
BODY	**Cần có trước:** Kho nguồn và kho đích đã khai báo trong Dữ liệu nền (không phải kho nhóm, không bị ngừng dùng); vật tư cần chuyển đã có mã trong SC Item; kho nguồn còn đủ tồn khả dụng (không tính lô đang chờ QC, bị từ chối hoặc bị khóa).
BODY	**Riêng cho nhập phiếu HIS (UC-18B):** vật tư đã điền **Mã HIS** trên SC Item; mọi kho in trên phiếu HIS đã có dòng ánh xạ trong **SC HIS Warehouse Map**; nếu dùng phương thức AI (Vision) cần cấu hình API key, nếu dùng OCR offline cần cài tesseract (vie+eng).
H3	3.6.3	Các bước thực hiện
H4	3.6.3.1	Lập phiếu luân chuyển mới
OL	Từ Trang chủ, mở **M6**, bấm thẻ **SC Transfer Request** rồi nhấn **Tạo mới** (hoặc vào **Danh sách** rồi **Tạo mới**).
OL	Điền **Ngày yêu cầu**, **Loại chuyển kho** (Routine / Urgent / Replenishment / Return to Main) và **Ngày cần**. Có thể chọn **Người yêu cầu** và **Khoa phòng yêu cầu**.
OL	Tại mục **Kho nguồn → Kho đích**, chọn **Kho nguồn** và **Kho đích** (phải khác nhau — xem lỗi SC-E024 ở mục 3.6.6).
OL	Trong bảng **Vật tư cần chuyển**, thêm từng dòng: **Mã VT**, **UOM**, **SL yêu cầu**. Ô **Tên** tự điền theo mã. Để trống **Lô** nếu muốn hệ thống tự chọn theo FEFO; nhập **SL duyệt** nếu muốn duyệt khác số yêu cầu.
OL	Nhấn **Lưu**. Hệ thống chụp tồn kho nguồn vào cột **Tồn tại kho nguồn** và tính **Tổng SL yêu cầu**.
IMG	Màn hình tạo phiếu luân chuyển với mục Kho nguồn → Kho đích và bảng Vật tư cần chuyển.
NOTE	Nếu kho đích (hoặc kho nguồn) là kho Khoa phòng, ô **Cần phê duyệt Manager** sẽ tự bật; phiếu trở thành chuyển liên tầng và chỉ Trưởng phòng Vật tư mới nộp được.
H4	3.6.3.2	Nộp & duyệt phiếu
OL	Mở phiếu ở trạng thái **Nháp**, kiểm tra lại các dòng vật tư và **SL duyệt**.
OL	Nhấn **Nộp**. Khi nộp thành công, trạng thái chuyển sang **Đã duyệt (Approved)**, hệ thống ghi **Người duyệt** và **Thời điểm duyệt**.
OL	Với phiếu liên tầng, nếu tài khoản của bạn không có quyền Trưởng phòng Vật tư, hệ thống chặn bằng lỗi SC-E-TRANSFER-MANAGER-REQUIRED; hãy chuyển cho người có vai trò phù hợp nộp.
WARN	Khi nộp, hệ thống kiểm tra **SL duyệt** từng dòng không được vượt tồn kho nguồn. Nếu vượt sẽ báo SC-E-TRANSFER-INSUFFICIENT kèm số lượng tối đa có thể chuyển.
H4	3.6.3.3	Tạo bút toán xuất kho (Material Transfer) & nhận hàng
FIRST	Sau khi phiếu ở trạng thái **Đã duyệt**, Thủ kho tạo bút toán kho để thực sự chuyển tồn.
OL	Mở phiếu đã duyệt, chạy lệnh tạo Stock Entry. Hệ thống sinh một **SC Stock Entry** loại **Material Transfer** ở dạng nháp, liên kết về phiếu này.
OL	Với vật tư quản lý lô mà dòng không chỉ định **Lô**, hệ thống tự chọn lô theo **FEFO** (hết hạn trước — xuất trước); phần tồn cũ chưa gắn lô được chuyển nguyên trạng. Trạng thái phiếu chuyển sang **Đang chuyển (In Transit)**.
OL	Mở **SC Stock Entry** vừa tạo, kiểm tra các dòng/lô rồi **Nộp**. Khi đó tồn kho nguồn bị trừ, tồn kho đích được cộng (ghi vào Sổ kho), cột **SL đã chuyển** trên phiếu được cập nhật và trạng thái phiếu chuyển thành **Đã nhận (Received)**.
IMG	Phiếu luân chuyển đã duyệt và bút toán Material Transfer sinh kèm.
NOTE	Nếu hủy bút toán Stock Entry, phiếu tự quay lại trạng thái **Đã duyệt** và **SL đã chuyển** về 0 để bạn xử lý lại.
H4	3.6.3.4	Nhập phiếu chuyển kho từ HIS (UC-18B)
FIRST	Màn hình **Nhập phiếu chuyển kho HIS** (đường dẫn `/his-import`) đọc tự động file PDF "PHIẾU XUẤT ĐIỀU CHUYỂN" (Mẫu C31-HD) của HIS, đối chiếu vật tư theo Mã HIS và đối chiếu kho, rồi tạo phiếu luân chuyển tương ứng. Đây là việc **ghi nhận lại** lần xuất đã thực hiện bên HIS (HIS là nguồn sự thật), không phải yêu cầu cần Trưởng phòng duyệt.
OL	Mở **Nhập phiếu chuyển kho HIS** từ menu hoặc thẻ trên trang M6.
OL	Chọn **Phương thức đọc**: **AI (Vision)** — chính xác cao, nếu khớp 100% sẽ tự ghi nhận và submit (cần cấu hình API key); hoặc **Quét OCR (offline)** — không cần API key, luôn tạo phiếu nháp điền sẵn để bạn đối chiếu với PDF rồi submit tay.
OL	Bấm **Chọn PDF**, chọn file phiếu HIS, rồi nhấn **Nhập tự động**.
OL	Đọc bảng kết quả: số liệu **Tổng dòng**, **Khớp OK**, **Cần sửa**; danh sách **Kho chưa ánh xạ** và **Mã HIS chưa có vật tư** (nếu có); bảng **Dòng cần sửa**. Nhấn **Mở phiếu** để xem phiếu luân chuyển vừa tạo.
IMG	Màn hình nhập phiếu HIS với lựa chọn phương thức đọc và bảng kết quả đối chiếu.
BODY	**Cách đối chiếu:** kho HIS được tra trong **SC HIS Warehouse Map** (so khớp tên không phân biệt hoa/thường, bỏ khoảng trắng thừa); vật tư khớp theo **Mã HIS** trên SC Item; lô khớp theo Số lô (mã lô hoặc số lô nhà cung cấp); tồn được kiểm theo tồn khả dụng tại kho nguồn. Lô lấy đúng theo phiếu HIS nên FEFO không can thiệp khi đã có lô.
WARN	Mỗi phiếu HIS chỉ nhập được một lần: **Số phiếu HIS** là duy nhất. Nhập lại cùng phiếu sẽ bị chặn bằng lỗi SC-E-HIS-DUPLICATE để tránh trừ tồn hai lần.
H3	3.6.4	Trạng thái & phê duyệt
FIRST	Vòng đời phiếu luân chuyển: Nháp → (Đã duyệt khi nộp) → Đang chuyển (khi tạo bút toán) → Đã nhận (khi nộp bút toán). Phiếu chuyển liên tầng tới kho Khoa phòng cần vai trò Trưởng phòng Vật tư mới nộp được.
TABLE	Trạng thái|Ý nghĩa|Ai thực hiện
ROW	Nháp (Draft)|Đang soạn, chưa nộp; có thể sửa/xóa|Thủ kho / NV Khoa
ROW	Chờ duyệt (Pending Approval)|Phiếu liên tầng chờ Trưởng phòng Vật tư nộp/duyệt|Trưởng phòng Vật tư
ROW	Đã duyệt (Approved)|Đã nộp, đã ghi Người duyệt; sẵn sàng tạo bút toán|Hệ thống khi nộp
ROW	Đang chuyển (In Transit)|Đã sinh bút toán Material Transfer (nháp), chờ nộp|Thủ kho
ROW	Đã nhận (Received)|Bút toán đã nộp, tồn đã chuyển sang kho đích|Hệ thống khi nộp SE
ROW	Đã hủy (Cancelled)|Phiếu bị hủy (phải hủy bút toán Stock Entry trước nếu có)|Thủ kho / Manager
BODY	**Nguồn phiếu (import_source):** phiếu lập tay là **Manual**; phiếu đọc từ PDF là **HIS Import**. Phiếu HIS khớp 100% được tự duyệt và nộp ngay (bỏ qua kiểm tra Manager vì là ghi nhận); phiếu HIS có lỗi luôn dừng ở **Nháp** để sửa.
H3	3.6.5	Kết quả & truy vết
UL	Tạo bản ghi phiếu luân chuyển mã **SC-TR-YYYY-#####**.
UL	Khi nộp bút toán, sinh **SC Stock Entry** loại **Material Transfer** và ghi vào **Sổ kho (Stock Ledger)**: trừ tồn kho nguồn, cộng tồn kho đích; cập nhật **SL đã chuyển** từng dòng.
UL	Lưu **Người duyệt**, **Thời điểm duyệt**, và liên kết tới Stock Entry trên phiếu.
UL	Với phiếu HIS: lưu **Số phiếu HIS**, **Ngày phiếu HIS**, **File phiếu HIS gốc** (đính kèm để đối chiếu/audit) và **Nhật ký import** tóm tắt số dòng OK/lỗi cùng kho/vật tư chưa ánh xạ.
UL	Báo cáo nhập HIS trả về một trong các kết quả: **submitted** (đã ghi nhận), **draft_review** (đã quét OCR, cần đối chiếu rồi submit), **draft_with_errors** (phiếu nháp, có dòng cần sửa).
H3	3.6.6	Lỗi thường gặp & mẹo
UL	**SC-E024 SAME_WAREHOUSE — Kho nguồn trùng kho đích:** chọn lại hai kho khác nhau (chuyển trong cùng một kho tạo bút toán ảo làm sai số liệu).
UL	**SC-E-TRANSFER-MANAGER-REQUIRED — Phiếu liên tầng cần Manager:** phiếu liên quan kho Khoa phòng phải do Trưởng phòng Vật tư nộp.
UL	**SC-E-TRANSFER-INSUFFICIENT — SL duyệt vượt tồn:** giảm SL duyệt xuống tối đa bằng tồn kho nguồn được báo.
UL	**SC-E-TRANSFER-SHORTAGE — Kho nguồn không đủ để FEFO chọn:** kiểm tra lại tồn theo lô; bổ sung tồn hoặc giảm số lượng.
UL	**Ngày cần phải sau hoặc bằng Ngày yêu cầu:** sửa lại Ngày cần.
UL	**Phải cancel SC Stock Entry trước:** muốn hủy phiếu đã có bút toán đã nộp thì hủy bút toán Stock Entry trước.
UL	**SC-E-HIS-DUPLICATE — Phiếu HIS đã import:** không nhập lại; mở phiếu TR đã tạo trước đó.
UL	**SC-E-HIS-EXTRACT — Lỗi đọc phiếu:** thiếu API key / phiếu không đọc được số phiếu / lỗi mạng; kiểm tra cấu hình hoặc thử lại bằng phương thức OCR.
UL	**Dòng nhập HIS báo lỗi đối chiếu:** cột **Đối chiếu HIS** trên từng dòng có thể là Item Not Found, Batch Not Found, Insufficient Stock hoặc Warehouse Not Mapped — đọc cột **Ghi chú đối chiếu** để biết cần sửa gì.
UL	**Mẹo —** Item Not Found: điền **Mã HIS** cho SC Item tương ứng; Warehouse Not Mapped: thêm dòng trong **SC HIS Warehouse Map** với đúng tên kho như in trên phiếu.
UL	**Mẹo —** với phiếu HIS nhiều dòng, ưu tiên AI (Vision) để khớp 100% và tự ghi nhận; khi không có API key, dùng OCR rồi đối chiếu PDF trước khi nộp.
UL	**Mẹo —** dùng nút **Xuất** ở màn hình Danh sách để tải danh sách phiếu luân chuyển ra Excel.
H3	3.6.7	Liên quan
UL	Xem 3.2 — Dữ liệu nền (khai báo SC Item, SC Warehouse, SC HIS Warehouse Map).
UL	Xem mục Tồn kho & FEFO để hiểu cách chọn lô hết hạn trước và tồn khả dụng.
UL	Xem mục Bút toán kho (SC Stock Entry) cho chi tiết loại giao dịch Material Transfer.
UL	Xem 3.3 — Tiếp nhận & Kiểm tra chất lượng (lô đang chờ QC không tính vào tồn khả dụng để chuyển).
