# Mục 3.10 — M10 Truy xuất & Thu hồi. Nguồn: m10_traceability (UC-29/30/31), BatchTrace.vue, các DocType SC Recall Notice / SC Investigation Report.
H2	3.10	M10 · Truy xuất & Thu hồi
H3	3.10.1	Mục đích & khi nào dùng
FIRST	Module M10 trả lời câu hỏi "lô vật tư này từ đâu ra, đã đi những đâu và hiện còn ở chỗ nào", đồng thời cho phép thu hồi một lô có vấn đề và điều tra khi tồn kho bị thất thoát. Bạn vào đây khi nhà cung cấp gửi thông báo thu hồi, khi phát hiện lô lỗi/không đạt chất lượng, khi cần dựng lại toàn bộ lịch sử một lô để báo cáo, hoặc khi kiểm kê phát hiện chênh lệch tồn cần truy nguyên.
BODY	Module gồm ba việc chính: **Truy xuất lô** (tra cứu vòng đời một lô — màn hình riêng `/batch-trace`), **Thông báo Thu hồi** (SC Recall Notice — khóa lô, nạp danh sách nơi bị ảnh hưởng, thu hồi/trả/hủy) và **Báo cáo Điều tra** (SC Investigation Report — so sánh tồn lý thuyết với thực tế và phát hiện giao dịch bất thường).
H3	3.10.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** **Kiểm định** (QC Officer) tra cứu lô và theo dõi tiến độ thu hồi; **Trưởng phòng** (SupplyCore Manager) tạo, nộp và xử lý Thông báo Thu hồi cũng như mở Báo cáo Điều tra; **Thủ kho** tra cứu lô, ghi nhận số đã thu hồi và đã hủy. Quản trị Hệ thống có toàn quyền.
BODY	**Cần có trước:** Lô (SC Batch) và Sổ kho (Stock Ledger) đã có dữ liệu di chuyển; để thu hồi cần lô đang hoạt động có gắn Nhà cung cấp; để trả Nhà cung cấp thì lô phải có **NCC**; để điều tra cần biết Vật tư/Kho/Lô và khoảng thời gian nghi vấn.
H3	3.10.3	Các bước thực hiện
H4	3.10.3.1	Truy xuất lô (màn hình /batch-trace)
OL	Từ Trang chủ mở **M10**, vào **Truy xuất lô**, hoặc gõ thẳng đường dẫn `/batch-trace`.
OL	Gõ mã lô vào ô **Mã lô (Batch No)** rồi bấm **Tra cứu** (hoặc Enter). Nếu chưa nhớ mã lô, dùng ô **Hoặc tìm theo VT**: nhập mã/tên vật tư, bấm **Tìm**, hệ thống liệt kê các lô khớp kèm hạn dùng và trạng thái KCS — bấm vào một lô để mở.
OL	Đọc khối đầu trang: mã lô, **Vật tư**, **Nhà sản xuất**, **NCC** (kèm **Lô NCC**), **Xuất xứ**, **Ngày SX**, **Hạn dùng**. Cạnh hạn dùng có nhãn màu cảnh báo: đỏ "ĐÃ HẾT HẠN" hoặc "Còn N ngày" khi dưới 30 ngày, vàng khi dưới 90 ngày, xanh khi còn xa. Nếu lô đã khóa sẽ có phù hiệu đỏ **ĐÃ KHOÁ** kèm lý do.
OL	Khối **Nguồn gốc (PR → PO → QI)** cho biết lô sinh ra từ Phiếu nhập nào, gắn với Đơn mua nào và Phiếu KCS kết luận ra sao; bấm vào từng mã để mở chứng từ gốc.
OL	Khối **Tồn kho hiện tại** cho tổng tồn còn lại và chi tiết theo từng kho. Khối **Sổ cái tồn kho** liệt kê mọi bút toán nhập/xuất của lô (xuôi thời gian), tổng Nhập và tổng Xuất; dòng đã hủy bị gạch ngang. Khối **Đã bán cho khách** cho biết lô đã giao cho khách hàng nào, qua phiếu giao nào, số lượng bao nhiêu — kèm **số lô của nhà cung cấp** để đối chiếu với bao bì thực tế.
IMG	Màn hình Truy xuất lô: khối đầu trang, Nguồn gốc, Tồn kho hiện tại và bảng Sổ cái tồn kho.
NOTE	Nếu lô thiếu thông tin truy xuất (chưa khai NCC, số lô NCC, nhà sản xuất, ngày SX, không liên kết được Phiếu nhập gốc, hoặc KCS chưa kết luận), đầu trang hiện khung vàng "Dữ liệu chưa đầy đủ" và liệt kê trường còn thiếu. Đây chỉ là cảnh báo, không chặn xem.
NOTE	Lô đã xuất hết vẫn tra cứu được — Sổ cái và phần đã bán cho khách vẫn hiện đầy đủ, chỉ Tồn kho hiện tại bằng 0.
H4	3.10.3.2	Tạo Thông báo Thu hồi & nạp nơi bị ảnh hưởng
OL	Mở **M10**, bấm thẻ **SC Recall Notice** rồi **Tạo mới** (chỉ Trưởng phòng Vật tư / Quản trị tạo được).
OL	Điền **Ngày thu hồi**, **Loại thu hồi** (Voluntary — tự nguyện / Mandatory — bắt buộc / Precautionary — phòng ngừa), **Mức độ** (Class I (Critical) / Class II (High) / Class III (Low)), chọn **Vật tư** và **Lô bị thu hồi**; **NCC** tự lấy theo lô.
OL	Nhập **Lý do** thu hồi (bắt buộc) và **Tham chiếu pháp lý** nếu có (ví dụ công văn/thông tư của Bộ Y tế).
OL	**Lưu** bản nháp, sau đó chạy chức năng **Nạp items bị ảnh hưởng** (populate). Hệ thống dò Sổ kho và các phiếu giao hàng để tự điền bảng **Items bị ảnh hưởng**: các dòng còn tồn trong kho (Loại vị trí = Warehouse), các dòng đã chuyển sang kho khác (Loại vị trí = Department) và các dòng **đã bán cho khách** (Loại vị trí = Customer), kèm số lượng tương ứng.
OL	Xem bảng tổng hợp tự tính: **Tổng SL ảnh hưởng**, **SL đã thu hồi**, **SL đã hủy**, **SL chưa thu hồi** và **Tỷ lệ giải quyết**.
IMG	Phiếu Thông báo Thu hồi ở trạng thái Nháp với bảng Items bị ảnh hưởng vừa được nạp.
WARN	Vật tư phải khớp với vật tư của lô; nếu chọn lệch hệ thống sẽ báo lỗi và không cho lưu.
H4	3.10.3.3	Nộp phiếu — khóa lô & thông báo
OL	Kiểm tra lại danh sách, sau đó **Nộp** (Submit) phiếu. Khi nộp, hệ thống khóa lô (đặt cờ chặn trên SC Batch kèm lý do "Recall …"): từ đây mọi phiếu giao hàng và xuất kho dùng lô này đều bị chặn, ghi nhận **Người duyệt** và **Thời điểm duyệt**, trạng thái chuyển sang **Issued**.
OL	Nếu có dòng bị ảnh hưởng là khách hàng, chạy chức năng thông báo để gửi thư thu hồi — **mỗi khách hàng một thư riêng**, nêu đúng lô và số lượng khách đó đã nhận. Các dòng được đánh dấu đã thông báo kèm thời điểm gửi.
OL	Để gửi thông báo cho các kho nội bộ đang giữ lô, dùng chức năng gửi theo phòng ban — hệ thống gom các dòng theo **Phòng ban** để in hoặc gửi thư.
NOTE	Nếu nghi còn nơi nhận chưa được liệt kê, dùng chức năng rà soát theo khoảng ngày (mặc định 90 ngày gần nhất) để xem toàn bộ lần xuất của vật tư rồi bổ sung thủ công.
H4	3.10.3.4	Theo dõi thu hồi & xử lý (trả NCC / hủy)
OL	Khi các nơi trả vật tư về, cập nhật từng dòng: nhập **SL thu hồi**, **SL hủy**, đổi **Trạng thái** dòng (Notified / In Progress / Recovered / Destroyed / Used (No Recovery)); hệ thống tự tính lại **Còn chưa thu** và **Tỷ lệ giải quyết**.
OL	Nếu có **SL hủy** lớn hơn 0, bắt buộc điền đủ **Lý do hủy**, **Người chứng kiến hủy** và **Ngày tiêu hủy** trên dòng đó — đây là yêu cầu audit chống gian lận khi tiêu hủy thuốc/vật tư.
OL	Để trả lô về Nhà cung cấp, chạy **Tạo phiếu trả NCC** (create return): hệ thống lập một SC Purchase Receipt dạng trả hàng cho phần **SL thu hồi** từ kho, gắn vào **Phiếu trả NCC** và đặt **Phương án xử lý** = Return to Supplier.
OL	Để tiêu hủy, chạy **Tạo phiếu hủy** (write off): hệ thống lập một SC Stock Entry loại Material Issue mục đích "Write Off — Recall …" cho phần **SL hủy** từ kho, tự nộp, gắn vào **Phiếu hủy (Write Off)** và đặt **Phương án xử lý** = Destroy.
IMG	Phiếu Thu hồi đang xử lý: cập nhật SL thu hồi/hủy, audit hủy và các liên kết Phiếu trả NCC / Phiếu hủy.
NOTE	Phiếu hủy chỉ làm được cho một kho mỗi lần; nếu hàng hủy nằm ở nhiều kho, phải tạo phiếu hủy riêng cho từng kho.
H4	3.10.3.5	Điều tra thất thoát (Báo cáo Điều tra)
OL	Mở **M10**, bấm thẻ **SC Investigation Report** rồi **Tạo mới** (Trưởng phòng Vật tư / Quản trị).
OL	Khai phạm vi điều tra: ít nhất một trong **Vật tư** / **Kho** / **Batch**, cùng **Từ ngày** – **Đến ngày**, và **Filter user** nếu nghi một người dùng cụ thể; mô tả ngắn ở **Mô tả phát hiện ban đầu**.
OL	Chạy **Run Audit Trail** để xem toàn bộ giao dịch trong phạm vi (kèm người tạo, thời gian, thay đổi). Chạy **Compare** để hệ thống tính **Tồn lý thuyết** từ Sổ kho; nhập **Tồn thực tế (manual count)** đã kiểm đếm để ra **Δ qty** và **Δ giá trị**.
OL	Chạy **Detect Anomalies** để hệ thống dò các bất thường (lượng thay đổi lớn, giao dịch ngoài giờ, hủy không lý do, sửa sau khi nộp, một người lặp nhiều giao dịch âm, lệch số dư, ghi lùi ngày) và đổ vào bảng **Findings** kèm **Mức độ** (Low/Medium/High/Critical).
OL	Nếu phát hiện gian lận, dùng **Lock User** kèm lý do để khóa tài khoản nghi vấn (không khóa được Administrator/Guest hay tài khoản có quyền System Manager); thao tác được ghi vào **Log khóa user**. Nếu chỉ là lỗi hệ thống, dùng **Create Adjustment SR** để lập phiếu SC Stock Reconciliation điều chỉnh chênh lệch.
OL	Viết **Biện pháp khắc phục đề xuất** và **Kết luận điều tra**, dùng **Generate Minutes** để xuất biên bản có chỗ ký, rồi **Nộp** — trạng thái chuyển **Resolved**, ghi **Người duyệt** / **Thời điểm duyệt**.
IMG	Báo cáo Điều tra: so sánh tồn lý thuyết – thực tế và bảng Findings.
H3	3.10.4	Trạng thái & phê duyệt
BODY	**Thông báo Thu hồi (SC Recall Notice)** chạy theo vòng đời sau; trạng thái tự đổi theo thao tác nộp và theo số lượng đã thu hồi/hủy.
TABLE	Trạng thái|Ý nghĩa|Ai chuyển
ROW	Draft (Nháp)|Đang soạn, đã/đang nạp items bị ảnh hưởng, chưa khóa lô|Trưởng phòng Vật tư
ROW	Issued (Đã ban hành)|Đã nộp — lô bị khóa, ghi người/thời điểm duyệt|Trưởng phòng Vật tư (nộp)
ROW	In Progress (Đang xử lý)|Đã thu hồi/hủy được một phần, vẫn còn SL chưa thu|Hệ thống tự đặt
ROW	Completed (Hoàn tất)|Số chưa thu về 0 — thu hồi xong|Hệ thống tự đặt
ROW	Cancelled (Đã hủy)|Hủy phiếu — lô được mở khóa trở lại|Trưởng phòng Vật tư
BODY	**Báo cáo Điều tra (SC Investigation Report)** có vòng đời: **Draft** (chưa có phát hiện) → **Investigating** (đã có dòng Findings) → **Resolved** (sau khi Nộp) → **Closed**. Hủy phiếu đưa về Draft. Các dòng trong bảng Items bị ảnh hưởng cũng có trạng thái riêng: Notified, In Progress, Recovered, Destroyed, Used (No Recovery).
H3	3.10.5	Kết quả & truy vết
UL	Thu hồi tạo bản ghi **SC-RCL-YYYY-#####**; khi nộp sẽ khóa lô (cờ chặn trên SC Batch) để dừng mọi việc xuất kho và giao hàng.
UL	Trả Nhà cung cấp tạo một **SC Purchase Receipt** dạng trả hàng (liên kết ở **Phiếu trả NCC**); tiêu hủy tạo một **SC Stock Entry** Material Issue "Write Off — Recall …" đã nộp (liên kết ở **Phiếu hủy (Write Off)**), cả hai đều ghi âm vào Sổ kho cho lô.
UL	Điều tra tạo bản ghi **SC-INV-YYYY-#####**; nếu điều chỉnh do lỗi hệ thống sẽ sinh một **SC Stock Reconciliation** (liên kết ở **Phiếu điều chỉnh (System Error)**); việc khóa user và biên bản đều lưu vết.
UL	Truy xuất lô không tạo bản ghi mới — chỉ đọc Sổ kho, Phiếu nhập/Đơn mua/Phiếu KCS và Phiếu giao hàng để dựng lại lịch sử lô (xuôi và ngược).
UL	Phiếu thu hồi và điều tra đều bật theo dõi thay đổi (track changes), nên mọi chỉnh sửa đều có nhật ký.
H3	3.10.6	Lỗi thường gặp & mẹo
UL	**SC-E016 DESTRUCTION_AUDIT —** có dòng SL hủy lớn hơn 0 nhưng thiếu Lý do hủy / Người chứng kiến / Ngày hủy: bổ sung đủ ba thông tin này rồi lưu lại.
UL	**Vật tư không khớp lô —** chọn lại đúng vật tư của lô bị thu hồi.
UL	**SC-E-RCL-NO-SUPPLIER —** lô không có NCC nên không tạo được phiếu trả: chỉ có thể chuyển sang phương án hủy (Write Off) hoặc khai bổ sung NCC cho lô.
UL	**SC-E-RCL-NO-AFFECTED —** không có số lượng thu hồi/hủy từ kho: nhập SL thu hồi/SL hủy cho các dòng kho trước khi tạo phiếu xử lý.
UL	**SC-E-RCL-MULTI-WH —** hàng hủy ở nhiều kho: tạo phiếu hủy riêng cho từng kho.
UL	**SC-E-RCL-NOT-ISSUED —** chỉ thông báo/cập nhật/tạo phiếu xử lý được sau khi phiếu đã Nộp (Issued); hãy nộp phiếu trước.
UL	**SC-E-INV-NO-SCOPE —** thiếu phạm vi điều tra: phải có ít nhất một trong Vật tư / Kho / Batch (và Vật tư + Kho khi tạo phiếu điều chỉnh).
UL	**SC-E-INV-USER-IS-ADMIN —** không khóa được tài khoản hệ thống hoặc tài khoản có quyền System Manager qua điều tra.
UL	**Mẹo —** từ Sổ cái trong Truy xuất lô, bấm mã chứng từ để nhảy thẳng tới phiếu gốc khi cần đối chiếu.
UL	**Mẹo —** nếu lô báo "Dữ liệu chưa đầy đủ", quay về Dữ liệu nền bổ sung NCC/số lô NCC/nhà sản xuất để các lần truy xuất sau đầy đủ hơn.
UL	**Mẹo —** trước khi nộp Thu hồi, chạy lại Nạp items để chắc chắn đã gồm mọi nơi lô từng đến (các kho và các khách hàng).
H3	3.10.7	Liên quan
UL	Xem 3.3 — Tiếp nhận & Kiểm tra chất lượng (Phiếu nhập, Phiếu KCS — nguồn gốc của lô).
UL	Xem 3.7 — Bán hàng & Bàn giao (Phiếu giao hàng — nơi lô rời kho tới tay khách).
UL	Xem 3.5 — Lô vật tư & FEFO (Sổ kho; lô bị khóa không được chọn khi soạn hàng).
UL	Xem mục Kiểm kê & Điều chỉnh (SC Stock Reconciliation — phiếu điều chỉnh khi điều tra kết luận lỗi hệ thống).
