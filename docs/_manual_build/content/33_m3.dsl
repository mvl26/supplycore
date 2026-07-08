H2	3.3	M3 · Tiếp nhận & Kiểm tra chất lượng
H3	3.3.1	Mục đích & khi nào dùng
FIRST	Module M3 (thẻ **Tiếp nhận** trên thanh bên) dùng để ghi nhận hàng vật tư – hóa chất – thuốc do nhà cung cấp giao đến kho, lập **Phiếu nhập** (mã SC-PR-…) và kiểm tra chất lượng từng lô trước khi cho phép sử dụng. Bạn vào đây khi xe hàng của nhà cung cấp tới cổng kho: thủ kho đối chiếu thực nhận với đơn đặt hàng, nhập số lô – ngày sản xuất – hạn dùng, rồi nộp phiếu để hệ thống tự sinh lô, ghi tăng tồn kho và tạo phiếu kiểm tra QC.
BODY	M3 bao trùm ba việc gắn liền nhau: tiếp nhận hàng theo đơn (PO), kiểm tra chất lượng (QC) từng lô, và xử lý hàng trả lại nhà cung cấp khi hàng không đạt hoặc giao thừa/thiếu. Đây là cửa kiểm soát đầu vào: hàng chưa qua QC thì chưa được xuất dùng theo nguyên tắc FEFO.
H3	3.3.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Thủ kho (SupplyCore Storekeeper / Warehouse Officer) lập và nộp Phiếu nhập, nhập lô và hạn dùng. Kiểm soát Chất lượng (QC Officer) thực hiện kiểm tra QC từng lô và quyết định Đạt/Không đạt. Trưởng phòng Vật tư (SupplyCore Manager) xác nhận khi hàng nhận vượt số lượng PO. Kế toán (SupplyCore Accountant) tạo Debit Note / Credit Note khi trả hàng.
BODY	**Cần có trước:** Đơn đặt hàng (PO) đã duyệt và gửi nhà cung cấp (xem 3.2 — Mua sắm). Vật tư, Nhà cung cấp, Kho và UOM đã khai báo trong Dữ liệu nền. Nên có sẵn **Mẫu checklist** (QC Checklist Template, mã SC-QCT-…) cho nhóm vật tư để hệ thống tự nạp tiêu chí kiểm tra; nếu chưa có, hệ thống dùng mẫu mặc định toàn cục.
BODY	**Cần chuẩn bị tại quầy nhận:** phiếu giao hàng của nhà cung cấp (để đối chiếu và đính kèm bản scan), thông tin số lô NCC, ngày sản xuất và hạn dùng in trên bao bì từng mặt hàng.
H3	3.3.3	Các bước thực hiện
H4	3.3.3.1	Tạo Phiếu nhập từ đơn đặt hàng
OL	Từ Trang chủ, mở module **M3 · Tiếp nhận**, bấm thẻ **Phiếu nhập** rồi nhấn **Tạo mới**; hoặc mở đúng đơn **PO** liên quan và tạo Phiếu nhập từ đó để hệ thống nạp sẵn danh sách vật tư cùng **SL PO** cho từng dòng.
OL	Kiểm tra **NCC** và **PO tham chiếu** đã đúng; chọn **Ngày nhập** (mặc định hôm nay) và **Kho nhập** nơi hàng sẽ vào.
OL	Nếu hàng về **không có PO** (mua khẩn cấp, hàng tài trợ, mẫu thử), để trống **PO tham chiếu** và bắt buộc nhập **Lý do không có PO**; nếu thiếu, hệ thống chặn khi nộp (SC-E-NO-PO-REASON).
IMG	Màn hình tạo Phiếu nhập: phần NCC / PO tham chiếu / Ngày nhập / Kho nhập và bảng dòng vật tư.
H4	3.3.3.2	Nhập số lượng thực nhận, lô và hạn dùng
OL	Với từng dòng vật tư, nhập **SL nhận** thực tế. Hệ thống tự tính **SL vượt PO** = max(0, SL nhận − SL PO) và **Thành tiền** theo **Đơn giá**.
OL	Nhập **Ngày SX**, **Hạn dùng** và **Số lô NCC** cho từng dòng. Mỗi dòng vật tư sẽ sinh **một lô** riêng khi nộp phiếu (đơn N mặt hàng → N lô). Nếu vật tư có quản lý lô, **Số lô NCC** là bắt buộc để truy xuất nguồn gốc (Thông tư 22/2011/TT-BYT). Có thể nhập thêm **Nhà sản xuất** và **Xuất xứ**.
OL	Nếu hàng đã có sẵn lô trong hệ thống, chọn lô tại **Lô (đã có)** thay vì để hệ thống sinh lô mới.
OL	Tùy chọn: chọn **Target Bin** (vị trí kệ) cho dòng để phục vụ quản lý WMS, và đính kèm bản scan phiếu giao hàng tại **Phiếu giao hàng NCC (scan)**.
OL	Nếu **SL nhận** vượt **SL PO**, hệ thống bật cảnh báo cam và đặt cờ **Có item nhận vượt PO**; cần Trưởng phòng Vật tư tick **Xác nhận over-receipt (Manager)** trước khi nộp.
WARN	Mỗi dòng phải có **Hạn dùng** để hệ thống sinh lô; nếu thiếu sẽ bị chặn khi nộp (SC-E-PR-MISSING-EXPIRY). Hàng đã hết hạn (hạn dùng đã qua) bị từ chối ngay với mã SC-E003 EXPIRY_TOO_CLOSE. Hàng còn hạn nhưng dưới ngưỡng tồn kho tối thiểu (mặc định 30 ngày, cấu hình tại SupplyCore Settings) chỉ cảnh báo, vẫn cho nhập sau khi xác nhận.
H4	3.3.3.3	Nộp Phiếu nhập
OL	Bấm **Lưu** rồi **Nộp** phiếu. Khi nộp, hệ thống tự động: sinh **SC Batch** cho mỗi dòng có hạn dùng (mã lô dạng [mã VT]-[YYYYMM]-[số thứ tự]), ghi **Sổ kho (Stock Ledger)** tăng tồn tại Kho nhập, và tạo **Kiểm tra QC** cho từng dòng nếu **Yêu cầu QC** đang bật.
OL	Sau khi nộp, **QC Status** của phiếu là **Pending** (Chờ QC). Hàng chưa được FEFO/cấp phát chọn cho tới khi QC đạt.
IMG	Phiếu nhập sau khi nộp: cờ QC Status = Pending và danh sách lô vừa sinh.
H4	3.3.3.4	Kiểm tra chất lượng (QC)
OL	Mở thẻ **Kiểm tra QC** trong M3 (mã SC-QI-…). Mỗi phiếu QI gắn với một dòng vật tư của Phiếu nhập, mang sẵn **NCC**, **Lô**, **SL nhận** và **Mẫu checklist** tương ứng nhóm vật tư.
OL	Trong bảng **Tiêu chí kiểm tra**, đặt **Kết quả** cho từng tiêu chí là **Accepted** (đạt) hoặc **Rejected** (không đạt); nhập **Giá trị đo** và **Ghi chú** nếu cần. Tiêu chí mặc định gồm: bao bì nguyên vẹn, nhãn mác đúng, hạn dùng ≥6 tháng, số lô khớp chứng từ, quy cách đúng hợp đồng.
OL	Nếu tất cả tiêu chí Accepted, hệ thống tự đặt **Kết quả tổng** = **Accepted**. Bấm **Lưu** rồi **Nộp**.
OL	Thiếu thiết bị đo: tick **Thiếu thiết bị kiểm tra** và nhập **Ghi chú thiết bị**; phiếu chuyển **Kết quả tổng** = **On Hold** và không cập nhật trạng thái QC của Phiếu nhập cho tới khi kiểm lại.
IMG	Màn hình Kiểm tra QC với bảng tiêu chí và ô Kết quả tổng / Hành động.
BODY	**Khi QC đạt:** lô được đặt qc_status = Accepted, Phiếu nhập chuyển **QC Status** = Pass và ghi mốc **Đã nhập kho chính thức lúc** (officially_received_at). Từ thời điểm này lô mới được FEFO/cấp phát chọn.
H4	3.3.3.5	Xử lý hàng không đạt & trả nhà cung cấp
OL	Khi có tiêu chí Rejected, đặt **Hành động** phù hợp: **Return to Supplier** (trả NCC), **Request Replacement** (yêu cầu đổi hàng) hoặc **Conditional Accept** (chấp nhận có điều kiện). Nhập **Lý do không đạt**, rồi **Nộp** phiếu QI.
OL	Với **Return to Supplier**: hệ thống chặn lô (blocked) và tự tạo một **Phiếu nhập trả hàng** ở dạng nháp (is_return = 1) để Kế toán rà soát. Với **Request Replacement**: lô bị chặn và ghi lý do. Với **Conditional Accept**: lô đặt qc_status = Conditional và vẫn được phép xuất dùng.
OL	Trên Phiếu nhập trả hàng (nháp): mở phần **Trả hàng / Backorder**, kiểm tra danh sách vật tư, nhập **Lý do trả hàng** (bắt buộc), rồi **Nộp**. Khi nộp, hệ thống ghi Sổ kho giảm tồn, gửi email thông báo NCC, đặt **Trạng thái Return** = Pending Supplier Response và tự tạo **Debit Note**.
OL	Theo dõi phản hồi NCC: Kế toán dùng **Tạo Credit Note** khi NCC hoàn tiền (đặt Trạng thái Return = Refunded); khi NCC giao hàng đổi, tạo Phiếu nhập mới rồi dùng **Link Replacement** để gắn **PR đổi hàng** (đặt Trạng thái Return = Replaced).
WARN	Nếu NCC không phản hồi sau 7 ngày, hệ thống tự gửi email nhắc (escalate) cho Trưởng phòng Vật tư và đánh dấu mốc đã nhắc để không gửi trùng.
H4	3.3.3.6	Tạo Backorder cho phần nhận thiếu
OL	Khi nhận thiếu so với PO, mở Phiếu nhập đã nộp và dùng chức năng **Tạo Backorder**; hệ thống tạo một Phiếu nhập nháp mới cho phần còn thiếu, gắn **Backorder của PR** và cùng PO tham chiếu.
OL	Tiếp nhận phần hàng còn lại theo Backorder như một Phiếu nhập bình thường (quay lại 3.3.3.2).
NOTE	Khi nhận đủ 100% theo PO, hệ thống tự cập nhật trạng thái PO sang **Đã nhận**; nhận một phần thì PO ở **Nhận một phần**.
H3	3.3.4	Trạng thái & phê duyệt
BODY	**QC Status của Phiếu nhập** (tự cập nhật theo kết quả các phiếu QI, không sửa tay):
TABLE	Trạng thái|Ý nghĩa
ROW	Pending|Chờ QC — chưa kiểm xong mọi dòng; hàng chưa được FEFO/cấp phát chọn
ROW	Pass|Tất cả dòng QC đạt — ghi mốc Đã nhập kho chính thức, hàng được dùng
ROW	Partial Pass|Một số dòng đạt, một số không đạt
ROW	Fail|Tất cả dòng không đạt
BODY	**Kết quả tổng của phiếu Kiểm tra QC** (overall_status):
TABLE	Trạng thái|Ý nghĩa|Ai quyết định
ROW	Pending|Chờ kiểm — phiếu vừa tạo tự động|Kiểm soát Chất lượng
ROW	Accepted|Đạt toàn bộ tiêu chí|Kiểm soát Chất lượng
ROW	Rejected|Có tiêu chí không đạt|Kiểm soát Chất lượng
ROW	Conditional|Chấp nhận có điều kiện (vẫn xuất dùng)|Kiểm soát Chất lượng
ROW	On Hold|Tạm giữ do thiếu thiết bị kiểm tra|Kiểm soát Chất lượng
BODY	**Hành động xử lý sau QC** (action_taken): Pending, Accept, Conditional Accept, Return to Supplier, Request Replacement.
BODY	**Trạng thái Return của phiếu trả hàng** (return_status):
TABLE	Trạng thái|Ý nghĩa|Ai xử lý
ROW	Pending Supplier Response|Đã gửi NCC, chờ phản hồi|Kế toán theo dõi
ROW	Replaced|NCC đã giao hàng đổi (đã gắn PR đổi hàng)|Kế toán
ROW	Refunded|NCC hoàn tiền (đã tạo Credit Note)|Kế toán
ROW	Closed|Đã đóng hồ sơ trả hàng|Kế toán / Manager
BODY	**Xác nhận vượt PO:** khi hàng nhận vượt số lượng PO, phải có Trưởng phòng Vật tư tick **Xác nhận over-receipt (Manager)** thì mới nộp được Phiếu nhập.
H3	3.3.5	Kết quả & truy vết
UL	Tạo **Phiếu nhập** mã **SC-PR-YYYY-#####**; phiếu trả hàng cũng là SC-PR với cờ **Phiếu trả NCC**.
UL	Mỗi dòng vật tư sinh một **Lô (SC Batch)** mã [mã VT]-[YYYYMM]-[số thứ tự], mang ngày SX, hạn dùng, số lô NCC, nhà sản xuất, xuất xứ.
UL	Ghi **Sổ kho (Stock Ledger Entry)** tăng tồn tại Kho nhập khi nộp; phiếu trả hàng ghi giảm tồn.
UL	Tạo **Kiểm tra QC** mã **SC-QI-YYYY-#####** cho từng dòng (khi Yêu cầu QC bật); kết quả cập nhật qc_status của lô (Accepted/Conditional/Rejected) và QC Status của Phiếu nhập.
UL	QC đạt ghi mốc **Đã nhập kho chính thức lúc** trên Phiếu nhập — điều kiện để lô được FEFO/cấp phát chọn.
UL	Trả hàng tạo **Debit Note** (và **Credit Note** khi hoàn tiền) là SC Purchase Invoice; cập nhật **received_qty** và trạng thái của PO liên quan.
UL	Mẫu checklist dùng **QC Checklist Template** mã **SC-QCT-#####** (theo nhóm vật tư hoặc mặc định toàn cục).
H3	3.3.6	Lỗi thường gặp & mẹo
UL	**SC-E003 EXPIRY_TOO_CLOSE —** hạn dùng đã qua: hàng hết hạn không nhập được, đổi lô khác hoặc trả NCC.
UL	**SC-E014 SUPPLIER_BATCH_REQUIRED —** thiếu Số lô NCC cho vật tư có quản lý lô: nhập Số lô NCC để truy xuất nguồn gốc.
UL	**SC-E-PR-MISSING-EXPIRY —** dòng vật tư chưa nhập Hạn dùng: bổ sung hạn dùng để hệ thống sinh lô.
UL	**SC-E-OVER-RECEIPT —** nhận vượt SL PO mà chưa xác nhận: nhờ Trưởng phòng Vật tư tick Xác nhận over-receipt rồi nộp lại.
UL	**SC-E-NO-PO-REASON —** Phiếu nhập không có PO mà chưa nêu lý do: nhập Lý do không có PO.
UL	**SC-E-QI-READINGS —** nộp QC khi chưa đặt kết quả tiêu chí nào: đặt Kết quả cho ít nhất một tiêu chí.
UL	**SC-E-QI-ONHOLD —** tick Thiếu thiết bị kiểm tra mà chưa ghi chú: nhập Ghi chú thiết bị.
UL	**SC-E-RETURN-REASON —** nộp phiếu trả hàng chưa có lý do: nhập Lý do trả hàng.
UL	**SC-E-RETURN-DN-EXISTS / SC-E-RETURN-CN-EXISTS —** đã có Debit/Credit Note: không tạo lại; mở chứng từ đã có.
UL	**SC-E-RETURN-REPLACE-INVALID —** gắn nhầm PR đổi hàng là phiếu trả: chọn một Phiếu nhập thường (không phải phiếu trả).
UL	**SC-E-BACKORDER-NOTHING —** bấm Tạo Backorder khi không có dòng nào nhận thiếu: chỉ tạo backorder khi SL nhận < SL PO.
UL	**Mẹo —** đối chiếu kỹ Số lô NCC, ngày SX và hạn dùng với bao bì thực tế trước khi nộp, vì lô sinh tự động khi nộp và là gốc truy xuất sau này.
UL	**Mẹo —** chuẩn bị sẵn Mẫu checklist (SC-QCT) cho từng nhóm vật tư để phiếu QC tự nạp đúng tiêu chí, kiểm nhanh hơn.
H3	3.3.7	Liên quan
UL	Xem 3.2 — Mua sắm (PO làm tiền đề cho Phiếu nhập).
UL	Xem 3.4 — Kho & FEFO (lô qua QC mới được FEFO chọn; xếp hàng lên kệ theo Target Bin).
UL	Xem chương Truy xuất lô để lần theo nguồn gốc lô từ NCC đến điểm sử dụng.
UL	Xem 3.8 — Kế toán (Debit Note / Credit Note khi trả hàng và đối chiếu công nợ NCC).
