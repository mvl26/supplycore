H2	3.5	M5 · Quản lý lô vật tư & FEFO
H3	3.5.1	Mục đích & khi nào dùng
FIRST	Module M5 quản lý thông tin từng lô vật tư (batch) và áp dụng nguyên tắc FEFO — First Expiry First Out (lô gần hết hạn xuất trước). Bạn dùng M5 để: khai báo và tra cứu lô (số lô NCC, ngày sản xuất, hạn dùng, kết quả QC, CoA); để hệ thống tự gợi ý / tự chọn lô theo hạn dùng gần nhất mỗi khi xuất kho, chuyển kho hay cấp phát; theo dõi cảnh báo lô sắp hết hạn; và chặn xuất các lô đã bị khóa do thu hồi (recall) hoặc cách ly (quarantine).
BODY	Đây là tầng kiểm soát chất lượng và an toàn của kho: nó bảo đảm vật tư cấp cho khoa luôn là lô còn hạn lâu nhất hiện có, không cấp nhầm lô hết hạn hoặc lô đang bị thu hồi.
H3	3.5.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Thủ kho (Storekeeper / Warehouse Officer) tạo và tra cứu lô, in nhãn, xuất kho theo FEFO, xử lý cảnh báo hết hạn. Kiểm soát Chất lượng (QC Officer / Pharmacy Officer) cập nhật kết quả QC của lô, khóa lô để cách ly hoặc thu hồi, truy xuất lô. Trưởng phòng Vật tư (SupplyCore Manager) là người duy nhất được xác nhận nhập lô hạn ngắn và phê duyệt khi xuất trái FEFO. Quản trị Hệ thống cấu hình FEFO Picker Rule và ngưỡng cảnh báo.
BODY	**Cần có trước:** Vật tư (SC Item) đã khai báo và bật quản lý theo lô (has_batch_no); Kho (SC Warehouse) và Nhà cung cấp (SC Supplier) có trong Dữ liệu nền; ngưỡng cảnh báo trong **SupplyCore Settings** (mặc định Cảnh báo Warning 90 ngày, Critical 30 ngày); ít nhất một **FEFO Picker Rule** đang bật nếu muốn ép buộc FEFO khi xuất.
NOTE	Phần lớn lô được tạo tự động khi tiếp nhận hàng (Phiếu nhập kho ở M3) — bạn ít khi phải tạo lô bằng tay. Khi đó hệ thống tự sinh **Batch ID** theo dạng [Mã VT]-YYYYMM-NNN và lấy hạn dùng, ngày SX, số lô NCC từ phiếu nhập.
H3	3.5.3	Các bước thực hiện
H4	3.5.3.1	Tạo và tra cứu lô vật tư (SC Batch)
OL	Từ Trang chủ, mở module **M5**, bấm thẻ **SC Batch** rồi nhấn **Tạo mới** (chỉ khi cần tạo lô thủ công).
OL	Điền **Batch ID** (bắt buộc, duy nhất; chỉ dùng chữ, số và các dấu '-', '_', '.'), chọn **Mã VT**; **Tên VT** tự điền theo vật tư.
OL	Nhập **Hạn dùng** (bắt buộc) và **Ngày SX**. Hệ thống bắt buộc Hạn dùng phải sau Ngày SX.
OL	Ở mục **Nguồn gốc**, chọn **NCC**, nhập **Số lô NCC**, **Nhà sản xuất**, **Xuất xứ** nếu có.
OL	Đính kèm **CoA (Certificate of Analysis)** ở mục QC khi nhà cung cấp gửi phiếu kiểm nghiệm.
OL	Nhấn **Lưu**. Khi lưu, hệ thống tự sinh **Barcode lô** bằng chính Batch ID (có thể đè bằng mã GS1 riêng nếu cần).
OL	Để in nhãn, mở lô và dùng chức năng **In nhãn** — nhãn gồm Batch ID, barcode, mã/tên VT, nhà sản xuất, số lô NCC, ngày SX và hạn dùng.
OL	Để tra cứu nhanh: vào **Danh sách** SC Batch (mặc định sắp theo Hạn dùng tăng dần), tìm theo Batch ID, barcode, mã VT hoặc số lô NCC; hoặc dùng màn hình **Truy xuất lô** (/batch-trace).
IMG	Màn hình chi tiết một lô SC Batch với các mục Lô hàng, Nguồn gốc, QC và FEFO Block.
WARN	Nếu **Số lô NCC** trùng với một lô đang dùng của cùng vật tư, hệ thống hiện cảnh báo cam và liệt kê các lô cũ — cân nhắc dùng lại lô cũ thay vì tạo lô mới (Batch ID vẫn phải duy nhất nên bạn vẫn tạo được lô mới nếu thực sự cần).
H4	3.5.3.2	Cập nhật QC và xác nhận lô hạn ngắn
OL	**Trạng thái QC** của lô (Pending / Accepted / Rejected / Conditional) là trường chỉ đọc trên form lô, được đặt qua quy trình Tiếp nhận & Kiểm tra chất lượng (M3). Vai trò Kiểm soát Chất lượng cập nhật trạng thái này.
OL	Chỉ lô có QC là **Accepted** hoặc **Conditional** (hoặc lô chưa gắn QC) mới được FEFO gợi ý để xuất; lô **Rejected** sẽ không được đề xuất.
OL	Khi tạo lô có **Hạn dùng** còn dưới 6 tháng (180 ngày), hệ thống tự bật cờ **Hạn dùng ngắn (<6 tháng)** và hiện cảnh báo đỏ.
OL	Với lô hạn ngắn tạo thủ công, Trưởng phòng Vật tư phải tích **Xác nhận nhập lô hạn ngắn (Manager)** thì mới lưu được; hệ thống ghi lại **Người xác nhận** và **Thời điểm xác nhận**.
IMG	Mục Xác nhận hạn dùng với cờ Hạn dùng ngắn và ô tích xác nhận của Manager.
H4	3.5.3.3	Khóa lô để cách ly hoặc thu hồi
OL	Mở lô cần khóa, vào mục **FEFO Block / Recall**, tích **Block (recall hoặc lý do khác)**.
OL	Nhập **Lý do block** (bắt buộc) — ví dụ: thu hồi theo thông báo của NCC, nghi ngờ chất lượng, chờ cách ly QC.
OL	Nhấn **Lưu**. Hệ thống tự ghi **Người block** và **Thời điểm block**. Bỏ tích sẽ xóa hai thông tin này.
OL	Từ lúc bị block, lô không còn được FEFO gợi ý và không thể xuất bằng phiếu xuất kho thông thường (xem 3.5.6).
WARN	Lô đã thu hồi chỉ được xử lý qua quy trình thu hồi (Thông báo thu hồi — M10); phiếu xuất kho thường sẽ bị chặn với mã **SC-E008 BATCH_RECALLED**.
H4	3.5.3.4	Xuất / chuyển kho theo FEFO
OL	Tạo Phiếu kho (SC Stock Entry) loại **Material Issue** (cấp phát) hoặc **Material Transfer** (chuyển kho), chọn **Kho nguồn**.
OL	Thêm dòng vật tư rồi để hệ thống gợi ý lô: nó trả về danh sách lô sắp theo Hạn dùng gần nhất trước, kèm tồn khả dụng, số lượng đề xuất và mức cảnh báo màu (xanh OK / vàng Warning / đỏ Critical / Expired).
OL	Nếu vật tư chỉ có một lô, hệ thống tự chọn lô đó. Nếu cần nhiều hơn một lô để đủ số lượng, hệ thống tự chia số lượng lần lượt qua các lô theo thứ tự hết hạn.
OL	Muốn xuất một lô **không** theo thứ tự FEFO, tích **FEFO Override** trên dòng và nhập **lý do**. Việc này yêu cầu vai trò Manager; hệ thống ghi người duyệt, thời điểm và lưu một bình luận kiểm toán trên phiếu.
OL	Nhấn **Lưu** rồi **Nộp**. Khi nộp, Sổ kho (Stock Ledger) ghi giảm tồn theo từng lô đã chọn.
IMG	Bảng dòng vật tư trên phiếu xuất với lô được gợi ý theo FEFO và cột mức cảnh báo màu.
NOTE	FEFO chỉ ép buộc khi **cấp phát** (Material Issue). Với **chuyển kho** nội bộ (Material Transfer), hàng chưa rời hệ thống nên không kiểm tra thứ tự FEFO, nhưng vẫn chặn lô hết hạn và lô bị block.
H4	3.5.3.5	Cấu hình FEFO Picker Rule
OL	Mở thẻ **FEFO Picker Rule** trong M5, nhấn **Tạo mới**. Mã quy tắc tự sinh dạng **SC-FEFO-#####**.
OL	Nhập **Tiêu đề rule**, bật **Đang sử dụng**, đặt **Priority (cao thắng)** — khi nhiều quy tắc khớp, quy tắc có priority cao nhất được áp dụng (mặc định 100).
OL	Đặt **Phạm vi áp dụng**: chọn **Kho** (để trống = áp dụng mọi kho) và **Nhóm vật tư** (để trống = mọi nhóm).
OL	Đặt **Quy tắc**: tích **Strict mode (block FEFO violation)** để chặn cứng khi vi phạm FEFO (báo lỗi SC-E001); bỏ tích để chỉ cảnh báo cam, không chặn.
OL	Đặt **Hạn dùng tối thiểu khi nhập (ngày)** (mặc định 30), **Cảnh báo Yellow (ngày)** (mặc định 90) và **Cảnh báo Red (ngày)** (mặc định 30) rồi **Lưu**.
IMG	Form FEFO Picker Rule với mục Phạm vi áp dụng và Quy tắc.
H4	3.5.3.6	Xử lý cảnh báo lô sắp hết hạn
OL	Mỗi ngày hệ thống tự quét tồn kho và tạo **Cảnh báo hết hạn (Batch Expiry Alert)** cho từng cặp (lô, kho) còn tồn, phân mức theo số ngày còn lại.
OL	Xem cảnh báo ở trang **Cảnh báo** (/alerts) hoặc **Danh sách** Batch Expiry Alert; lọc theo **Kho** và **Mức độ**.
OL	Mở một cảnh báo và chọn hành động ở mục **Xử lý**: **Priority Issue** (ưu tiên cấp phát đợt tới — FEFO vốn đã xếp lô gần hết hạn lên trước), **Return to Supplier** (trả NCC), **Write Off** (hủy), hoặc **No Action**.
OL	Khi chọn hủy, hệ thống tạo Phiếu xuất kho **Material Issue** mục đích "Expired Disposal", ghi giảm tồn lô và đặt lô về trạng thái Disabled; cảnh báo được đánh dấu **Đã xử lý** kèm người và thời điểm xử lý.
IMG	Trang Cảnh báo liệt kê các lô sắp hết hạn theo mức Critical / Warning / Info.
H3	3.5.4	Trạng thái & phê duyệt
BODY	**Trạng thái QC của lô** (do Kiểm soát Chất lượng đặt qua M3):
TABLE	Trạng thái QC|Ý nghĩa|FEFO có gợi ý?
ROW	Pending|Chờ kiểm tra (mặc định khi mới tạo)|Có (nếu chưa gắn QC)
ROW	Accepted|Đạt, dùng được|Có
ROW	Conditional|Đạt có điều kiện|Có
ROW	Rejected|Không đạt|Không
BODY	**Mức cảnh báo hết hạn** (tính theo ngưỡng trong SupplyCore Settings, mặc định 90/30 ngày):
TABLE	Mức|Số ngày còn lại|Màu
ROW	Info|90–180 ngày|Xanh
ROW	Warning|30–90 ngày|Vàng
ROW	Critical|dưới 30 ngày|Đỏ
ROW	Expired|đã quá hạn|Đỏ (không xuất được)
BODY	**Phê duyệt:** nhập lô hạn ngắn (<6 tháng) cần Trưởng phòng Vật tư tích xác nhận; xuất trái FEFO (FEFO Override) cần vai trò Manager và ghi lý do, có lưu vết kiểm toán.
H3	3.5.5	Kết quả & truy vết
UL	Tạo bản ghi **SC Batch** với Batch ID dạng **[Mã VT]-YYYYMM-NNN** và barcode tra cứu được.
UL	Quy tắc FEFO lưu dưới mã **SC-FEFO-#####**; cảnh báo hết hạn lưu dưới mã **SC-EXP-YYYY-#####**.
UL	Mỗi lần xuất theo lô ghi vào **Sổ kho (Stock Ledger)** theo từng lô; xuất trái FEFO để lại bình luận kiểm toán trên phiếu kèm người duyệt và thời điểm.
UL	Mọi thay đổi trên lô được theo dõi (track changes): người và thời điểm khóa lô, người và thời điểm xác nhận lô hạn ngắn, người và thời điểm xử lý cảnh báo.
UL	Truy xuất nguồn gốc lô qua màn hình **Truy xuất lô** (/batch-trace); theo dõi lô sắp hết hạn qua trang **Cảnh báo** (/alerts) và dashboard cảnh báo theo kho.
H3	3.5.6	Lỗi thường gặp & mẹo
UL	**SC-E008 BATCH_RECALLED — Lô bị block:** lô đang bị khóa do thu hồi/cách ly nên không xuất được bằng phiếu thường; xử lý qua quy trình thu hồi (M10) hoặc bỏ block kèm lý do nếu đã được phép.
UL	**SC-E003 EXPIRY_TOO_CLOSE — Lô đã hết hạn:** không thể xuất lô quá hạn; chọn lô khác còn hạn hoặc hủy lô qua cảnh báo hết hạn.
UL	**SC-E001 FEFO_OVERRIDE — Còn lô gần hết hạn hơn:** đang xuất sai thứ tự FEFO; chọn đúng lô gợi ý, hoặc (nếu được phép) tích **FEFO Override** và ghi lý do — cần vai trò Manager.
UL	**SC-E-FEFO-MANAGER-REQUIRED:** chỉ vai trò SupplyCore Manager / System Manager mới nộp được phiếu có FEFO Override; nhờ Trưởng phòng Vật tư duyệt.
UL	**SC-E-BATCH-SHORT-EXPIRY:** lô hạn còn dưới 6 tháng chưa được xác nhận; nhờ Manager tích **Xác nhận nhập lô hạn ngắn** trước khi lưu.
UL	**SC-E020 BATCH_ID_INVALID_CHAR:** Batch ID chứa ký tự đặc biệt (/, \\, ?, #, %); chỉ dùng chữ, số và các dấu '-', '_', '.'.
UL	**Phải ghi lý do khi block batch:** không bỏ trống **Lý do block** khi tích Block.
UL	**Mẹo —** muốn một lô sắp hết hạn được cấp trước, vào cảnh báo của lô và chọn **Priority Issue**; FEFO vốn đã xếp lô gần hết hạn lên đầu.
UL	**Mẹo —** dùng **Strict mode** của FEFO Picker Rule cho nhóm vật tư quan trọng để chặn cứng việc xuất sai thứ tự; tắt strict cho nhóm ít rủi ro để chỉ cảnh báo.
UL	**Mẹo —** đặt **Hạn dùng tối thiểu khi nhập** trong FEFO Picker Rule để từ chối nhập hàng quá cận hạn.
H3	3.5.7	Liên quan
UL	Xem 3.3 — Tiếp nhận & Kiểm tra chất lượng (nơi lô được tạo tự động và đặt trạng thái QC).
UL	Xem 3.4 — Quản lý kho & tồn (Sổ kho, putaway, bản đồ kho).
UL	Xem 3.6 — Chuyển kho (Material Transfer áp dụng kiểm tra lô).
UL	Xem 3.7 — Cấp phát & BHYT (cấp phát cho khoa theo FEFO).
UL	Xem chương M10 — Thu hồi vật tư (khóa lô và xử lý thu hồi).
