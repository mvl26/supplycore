H2	3.2	M2 · Kế hoạch & Mua sắm
H3	3.2.1	Mục đích & khi nào dùng
FIRST	Module M2 (thẻ **Kế hoạch & Mua** trên màn hình chính) giúp bạn chủ động quản lý việc bổ sung vật tư: đặt sẵn ngưỡng tồn kho cho từng vật tư, lập kế hoạch mua sắm định kỳ dựa trên lịch sử tiêu thụ, tạo Yêu cầu mua khi khoa phòng hoặc kho cần hàng, và lập Đơn mua hàng gửi nhà cung cấp. Bạn vào đây khi cần: cấu hình mức tái đặt hàng / tồn an toàn, dự trù mua hàng cho tháng/quý/năm, đề nghị mua một danh mục vật tư, hoặc chuyển một đề nghị đã duyệt thành đơn đặt hàng chính thức.
BODY	Bốn nghiệp vụ trong M2 nối tiếp nhau thành một chuỗi: **Ngưỡng tái đặt hàng → Kế hoạch mua sắm → Yêu cầu mua (MR) → Đơn mua hàng (PO)**. Mỗi bước có thể đứng riêng, nhưng khi đi liền mạch, hệ thống tự gợi ý số lượng và đơn giá nên bạn ít phải nhập tay.
H3	3.2.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** NV Mua sắm và Thủ kho tạo Kế hoạch mua sắm, Yêu cầu mua, Đơn mua hàng. Trưởng phòng Vật tư phê duyệt Yêu cầu mua và Đơn mua hàng. Với đơn giá trị lớn (từ ngưỡng phê duyệt trở lên), Lãnh đạo / Quản trị Hệ thống duyệt cấp hai. Kế toán xem được nhưng không sửa Kế hoạch / Yêu cầu mua.
BODY	**Cần có trước:** Vật tư (SC Item), Kho (SC Warehouse), Nhà cung cấp (SC Supplier) và Đơn vị tính (SC UOM) đã khai báo trong Dữ liệu nền (M0). Vật tư phải có ít nhất một nhà cung cấp (NCC mặc định, hoặc thuộc nhóm vật tư của một NCC, hoặc nằm trong Hợp đồng khung còn hiệu lực) thì mới đề nghị mua được. Muốn hệ thống tự gợi ý số lượng cần mua thì kho phải có lịch sử xuất kho (Sổ kho – Stock Ledger) ít nhất vài tháng.
H3	3.2.3	Các bước thực hiện
H4	3.2.3.1	Thiết lập mức tái đặt hàng & tồn an toàn
OL	Mở thẻ vật tư cần cấu hình trong M0 (SC Item), vào mục **Lập kế hoạch**.
OL	Nhập các ngưỡng ở cấp vật tư: **Tồn kho an toàn**, **Mức tái đặt hàng**, **Tồn kho tối đa**, **Số lượng đặt hàng chuẩn (EOQ)**, **Lead time NCC (ngày)** (mặc định 30).
OL	Nếu mỗi kho có ngưỡng khác nhau, mở mục **Ngưỡng tái đặt theo kho** rồi thêm dòng trong bảng **Mức tồn theo kho**: chọn **Kho** và nhập **Tồn kho an toàn / Mức tái đặt hàng / Tồn kho tối đa / Số lượng đặt hàng chuẩn (EOQ)** riêng cho kho đó.
OL	Nhấn **Lưu**. Khi tồn thực tế của một (vật tư, kho) tụt xuống bằng hoặc thấp hơn **Mức tái đặt hàng**, hệ thống chạy nền hằng ngày sẽ tự tạo một Yêu cầu mua bản nháp (xem 3.2.3.3).
IMG	Mục Lập kế hoạch trên thẻ SC Item với bảng Mức tồn theo kho.
NOTE	Ngưỡng theo kho được ưu tiên hơn ngưỡng cấp vật tư, nhưng chỉ khi giá trị trong dòng kho lớn hơn 0; để trống hoặc bằng 0 thì hệ thống tự dùng lại giá trị cấp vật tư. Riêng Lead time luôn lấy theo cấp vật tư.
H4	3.2.3.2	Lập Kế hoạch mua sắm định kỳ (Procurement Plan)
OL	Từ màn hình chính mở **M2 (Kế hoạch & Mua)**, bấm thẻ **Procurement Plan** rồi nhấn **Tạo mới**.
OL	Chọn **Kỳ kế hoạch** (Hằng tháng / Hằng quý / Hằng năm / Đột xuất — Monthly/Quarterly/Yearly/Adhoc), nhập **Từ ngày**, **Đến ngày**, **Ngày lập kế hoạch**.
OL	Chọn **Kho** cần lập kế hoạch. Đặt **Số tháng lịch sử để tính avg** (mặc định 3) và **Hệ số safety stock (%)** (mặc định 20). Nếu cần, điền **Ngày cần hàng** — giá trị này sẽ truyền sang Yêu cầu mua.
OL	Nhấn nút **Tự nạp danh mục từ lịch sử tiêu thụ**. Hệ thống quét Sổ kho, tính bình quân tiêu thụ/tháng, tồn hiện tại, lượng PO đang chờ nhận, rồi đề xuất **SL kế hoạch mua** cho từng vật tư. Ngoài ra có thể nạp theo ngưỡng tái đặt để bổ sung các vật tư đang dưới mức tái đặt hàng.
OL	Kiểm tra bảng vật tư, chỉnh **SL kế hoạch mua** và **Đơn giá ước tính** nếu cần (ví dụ tăng cho dịp lễ, mùa dịch). Hệ thống tự tính **Thành tiền** từng dòng và **Tổng chi phí ước tính**.
OL	(Tùy chọn) Nhập **Ngân sách dự kiến** cho kỳ. Nếu để 0 nghĩa là không kiểm soát ngân sách.
OL	(Tùy chọn) Tick **Tự tạo Material Request sau Submit** nếu muốn hệ thống tự sinh Yêu cầu mua ngay khi duyệt kế hoạch.
OL	Nhấn **Lưu** rồi **Nộp** để duyệt kế hoạch. Nếu chưa tick tự tạo, sau khi nộp bạn bấm nút **Tạo Material Request** để sinh phiếu thủ công.
IMG	Màn hình Procurement Plan với bảng vật tư đã tự nạp và tổng chi phí ước tính.
WARN	Nếu **Tổng chi phí ước tính** vượt **Ngân sách dự kiến** (và ngân sách lớn hơn 0), hệ thống chặn nộp với lỗi **SC-E-BUDGET-EXCEEDED**. Phải tick ô **Xác nhận vượt ngân sách** rồi lưu lại mới nộp được.
NOTE	Nếu kho chưa có dữ liệu tiêu thụ trong khoảng tháng đã chọn, nút tự nạp sẽ báo "Không có dữ liệu tiêu thụ…" (màu cam) và không thêm dòng nào — khi đó bạn tự thêm vật tư vào bảng theo cách thủ công.
H4	3.2.3.3	Tạo Yêu cầu mua (Material Request) & phê duyệt
OL	Mở **M2**, bấm thẻ **Yêu cầu mua** (SC Material Request) rồi **Tạo mới**. Hoặc để hệ thống tự sinh phiếu từ Kế hoạch mua sắm / từ cảnh báo tồn dưới mức tái đặt.
OL	Chọn **Loại yêu cầu**: **Purchase** (mua hàng), **Internal Transfer** (điều chuyển nội bộ) hoặc **Urgent** (đột xuất). Nhập **Ngày yêu cầu** và **Ngày cần**.
OL	Chọn **Khoa phòng yêu cầu**, **Kho đích** và **Người yêu cầu** khi cần.
OL	Thêm dòng vật tư: chọn vật tư, nhập **SL** và **UOM**. Nếu mua theo Hợp đồng khung, chọn **HĐ khung** trên dòng — hệ thống tự lấy đơn giá hợp đồng làm **Đơn giá ước tính**.
OL	Nhập **Lý do đề nghị** nếu cần, kiểm tra **Tổng ước tính**, rồi **Lưu** và **Nộp**. Khi nộp, phiếu chuyển sang trạng thái **Pending** (Chờ duyệt) và hệ thống gửi email báo Trưởng phòng Vật tư.
OL	Trưởng phòng Vật tư mở phiếu, bấm **Duyệt** (chuyển sang Approved) hoặc **Từ chối** (phải nhập lý do, chuyển sang Rejected).
OL	Sau khi phiếu **Approved**, NV Mua sắm bấm **Tạo Purchase Order** để chuyển sang đơn mua hàng (gom theo nhà cung cấp và hợp đồng khung).
IMG	Phiếu Yêu cầu mua ở trạng thái Pending với nút Duyệt / Từ chối.
NOTE	Với (vật tư, kho) tụt dưới mức tái đặt hàng, tác vụ nền hằng ngày tự tạo một Yêu cầu mua **bản nháp** loại Purchase cho từng kho (số lượng = Số lượng đặt hàng chuẩn, hoặc bù lên Tồn kho tối đa, hoặc gấp đôi mức tái đặt trừ tồn). Bạn nhận email tóm tắt, mở phiếu nháp, soát lại số lượng rồi Nộp như bình thường.
H4	3.2.3.4	Tạo & phê duyệt Đơn mua hàng (Purchase Order)
OL	Tạo PO từ Yêu cầu mua đã duyệt (nút **Tạo Purchase Order**) hoặc mở thẻ **Đơn mua hàng** (SC Purchase Order) trong M2 và **Tạo mới**.
OL	Chọn **NCC**, **Ngày PO**, **Ngày giao DK**, **Kho nhận**. Nếu mua theo hợp đồng, chọn **Hợp đồng khung** (và **Release Order** nếu có) — hệ thống tự nạp đơn giá theo hợp đồng.
OL	Nếu không có hợp đồng khung, nhập **Đơn giá** từng dòng thủ công và đính kèm **Báo giá** ở ô tương ứng.
OL	Điều chỉnh **SL**, **Đơn giá**, **Điều khoản giao hàng**, **Điều khoản TT** nếu cần. Hệ thống tính **Tổng giá trị** và đánh dấu **Có lệch giá so với FC** khi đơn giá lệch quá ±1% so với giá hợp đồng khung.
OL	Gửi duyệt: bấm **Gửi duyệt (Manager)** để chuyển sang chặng **Manager Review**. Trưởng phòng Vật tư bấm **Manager duyệt**. Nếu **Tổng giá trị** dưới ngưỡng phê duyệt thì đơn được duyệt luôn; nếu bằng hoặc vượt ngưỡng, đơn chuyển sang **Executive Review** chờ Lãnh đạo bấm **Lãnh đạo duyệt**.
OL	Khi chặng phê duyệt đạt **Approved**, nhấn **Nộp**. Hệ thống tự gửi email đơn hàng tới NCC và đặt trạng thái **Sent to Supplier** (Đã gửi NCC), kèm thời điểm gửi.
IMG	Đơn mua hàng với panel Workflow Phê duyệt và nút Manager duyệt / Lãnh đạo duyệt.
NOTE	Ngưỡng phê duyệt hai cấp lấy từ **SupplyCore Settings · po_approval_threshold**, mặc định 50.000.000 VND. Quản trị có thể đổi trong Cấu hình hệ thống.
NOTE	Nếu nộp đơn trực tiếp mà chưa qua chặng duyệt, hệ thống xem như tự duyệt ở cấp Manager (ghi nhận người nộp là người duyệt) rồi vẫn gửi NCC. Dùng luồng **Gửi duyệt → Manager duyệt → Lãnh đạo duyệt** khi cần đúng quy trình kiểm soát theo giá trị.
H4	3.2.3.5	Gửi NCC, nhắc nhở & nhận hàng
OL	Sau khi PO ở trạng thái **Sent to Supplier**, NCC nhận email đơn hàng và xác nhận ngoài hệ thống. Khi NCC đã xác nhận, mở PO và tick **NCC đã xác nhận**.
OL	Nếu quá số ngày quy định mà NCC chưa xác nhận, tác vụ nền hằng ngày tự gửi email nhắc và ghi lại thời điểm nhắc gần nhất.
OL	Khi hàng về, từ PO bấm nút tạo Phiếu nhập (Purchase Receipt) — hệ thống tạo phiếu nháp điền sẵn các dòng còn thiếu, đơn giá và kho nhận (xem 3.3). Nhận một phần thì PO chuyển **Partially Received**; nhận đủ thì PO chuyển **Received**.
IMG	Đơn mua hàng đã gửi NCC với ô NCC đã xác nhận.
NOTE	Số ngày nhắc NCC lấy từ **SupplyCore Settings · po_response_reminder_days**, mặc định 3 ngày.
H3	3.2.4	Trạng thái & phê duyệt
BODY	**Kế hoạch mua sắm (Procurement Plan):**
TABLE	Trạng thái|Ý nghĩa|Ai duyệt
ROW	Draft (Nháp)|Đang soạn, chưa nộp|NV Mua sắm / Thủ kho
ROW	Approved (Đã duyệt)|Đã nộp, kế hoạch được chốt|Tự chuyển khi Nộp
ROW	Generated (Đã sinh MR)|Đã tạo Yêu cầu mua từ kế hoạch|—
ROW	Cancelled (Đã hủy)|Kế hoạch bị hủy|—
BODY	**Yêu cầu mua (SC Material Request):**
TABLE	Trạng thái|Ý nghĩa|Ai duyệt
ROW	Draft (Nháp)|Đang soạn|NV Mua sắm / Thủ kho / NV Khoa
ROW	Pending (Chờ duyệt)|Đã nộp, chờ phê duyệt|—
ROW	Approved (Đã duyệt)|Được duyệt, cho phép tạo PO|Trưởng phòng Vật tư
ROW	Rejected (Từ chối)|Bị từ chối kèm lý do|Trưởng phòng Vật tư
ROW	Ordered (Đã đặt) / Received (Đã nhận)|Đã chuyển thành PO / đã nhận hàng|—
ROW	Cancelled (Đã hủy)|Phiếu bị hủy|—
BODY	**Đơn mua hàng (SC Purchase Order)** — trạng thái phiếu và chặng phê duyệt chạy song song:
TABLE	Trạng thái|Ý nghĩa|Ai duyệt
ROW	Draft (Nháp)|Đang soạn|NV Mua sắm
ROW	Pending Approval / Manager Review|Chờ Trưởng phòng Vật tư duyệt|Trưởng phòng Vật tư
ROW	Executive Review|Đơn từ ngưỡng trở lên, chờ Lãnh đạo duyệt|Lãnh đạo / Quản trị
ROW	Approved (Đã duyệt)|Đã duyệt đủ cấp, sẵn sàng nộp|—
ROW	Sent to Supplier (Đã gửi NCC)|Đã nộp và gửi email cho NCC|Tự chuyển khi Nộp
ROW	Partially Received / Received|Đã nhận một phần / nhận đủ|Tự chuyển theo Phiếu nhập
ROW	Closed / Cancelled|Đã đóng / đã hủy|—
H3	3.2.5	Kết quả & truy vết
UL	Kế hoạch mua sắm tạo bản ghi mã **SC-PP-YYYY-#####**, lưu tổng chi phí ước tính và link tới Yêu cầu mua đã sinh.
UL	Yêu cầu mua tạo bản ghi mã **SC-MR-YYYY-#####**, ghi người yêu cầu, khoa phòng, lý do, và link ngược về Procurement Plan nếu sinh tự động.
UL	Đơn mua hàng tạo bản ghi mã **SC-PO-YYYY-#####**, lưu người duyệt từng cấp, thời điểm gửi NCC và cờ lệch giá so với hợp đồng khung.
UL	PO có liên kết Hợp đồng khung sẽ cập nhật giá trị đã dùng / còn lại của hợp đồng; Release Order liên quan chuyển sang Converted.
UL	Mọi thay đổi đều được ghi nhật ký (track changes) phục vụ kiểm toán; email gửi NCC, nhắc nhở và thông báo duyệt đều lưu vết.
H3	3.2.6	Lỗi thường gặp & mẹo
UL	**SC-E-BUDGET-EXCEEDED — Vượt ngân sách kế hoạch:** tick **Xác nhận vượt ngân sách** rồi lưu lại, hoặc giảm số lượng / đơn giá cho khớp ngân sách.
UL	**SC-E-NO-SUPPLIER — Vật tư chưa có NCC:** khai báo NCC mặc định cho vật tư, hoặc gắn vật tư vào nhóm của một NCC, hoặc thêm vào Hợp đồng khung còn hiệu lực trước khi đề nghị mua.
UL	**SC-E023 ZERO_MR_COST — MR không có cơ sở giá:** Yêu cầu mua loại Purchase/Urgent phải có đơn giá > 0 ở mọi dòng; nhập đơn giá ước tính hoặc gắn hợp đồng khung.
UL	**SC-E-QTY / SC-E-DATE:** số lượng phải lớn hơn 0; **Ngày cần** phải không sớm hơn **Ngày yêu cầu**.
UL	**SC-E-MR-NOT-APPROVED — Tạo PO khi MR chưa duyệt:** chờ Trưởng phòng Vật tư bấm **Duyệt** rồi mới tạo Purchase Order.
UL	**SC-E-REJECT-REASON — Từ chối thiếu lý do:** phải nhập lý do khi từ chối Yêu cầu mua hoặc Đơn mua hàng.
UL	**SC-E002 FC_EXCEEDED / FC_INACTIVE — Vượt hoặc dùng sai hợp đồng khung:** tổng PO vượt hạn mức còn lại của hợp đồng, hoặc hợp đồng không còn Active; gia hạn hợp đồng, chia nhỏ PO, hoặc bỏ liên kết hợp đồng.
UL	**SC-E-PO-NO-SUPPLIER-EMAIL — NCC thiếu email:** PO không nộp được vì không gửi được cho NCC; bổ sung email cho NCC trong M0.
UL	**Mẹo —** dùng **Tự nạp danh mục từ lịch sử tiêu thụ** để hệ thống tính sẵn số lượng, tránh nhập tay cả trăm dòng.
UL	**Mẹo —** với mua định kỳ ổn định, cấu hình **Số lượng đặt hàng chuẩn (EOQ)** theo kho để Yêu cầu mua tự sinh đúng số lượng cần đặt.
UL	**Mẹo —** kiểm tra cờ **Có lệch giá so với FC** trên PO trước khi nộp để phát hiện đơn giá lệch hợp đồng khung quá 1%.
H3	3.2.7	Liên quan
UL	Xem 3.1 — M1 Hợp đồng & Nhà cung cấp (Hợp đồng khung, Release Order, NCC).
UL	Xem 3.3 — M3 Tiếp nhận & Kiểm tra chất lượng (tạo Phiếu nhập từ PO).
UL	Xem chương Dữ liệu nền (M0) để khai báo Vật tư, Kho, NCC, Đơn vị tính và ngưỡng tái đặt.
UL	Xem chương Cấu hình hệ thống cho ngưỡng phê duyệt PO và số ngày nhắc NCC.
