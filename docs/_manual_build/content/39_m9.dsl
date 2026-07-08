H2	3.9	M9 · Kiểm kê & Đối chiếu
H3	3.9.1	Mục đích & khi nào dùng
FIRST	Module M9 dùng để kiểm kê tồn kho thực tế và đối soát với số liệu trên hệ thống. Bạn dùng module này khi tổ chức kiểm kê định kỳ (cuối tháng, cuối quý, cuối năm), kiểm kê đột xuất một kho/một nhóm vật tư/một khu vực kệ, hoặc khi phát hiện sai lệch giữa sổ sách và hàng thực tế. Quy trình gồm hai bước: lập **Phiếu kiểm kê** (SC Inventory Count Sheet — đếm thực tế và so với số hệ thống) rồi tạo **Phiếu đối soát** (SC Stock Reconciliation — ghi điều chỉnh tồn kho và hạch toán chênh lệch).
BODY	**Đếm xoay vòng (cycle count):** thay vì kiểm kê toàn kho một lần, bạn lập nhiều phiếu kiểm kê nhỏ theo phạm vi **Theo nhóm vật tư** hoặc **Theo khu vực (Zone)** và lặp lại định kỳ để mỗi vật tư đều được đếm trong kỳ. M9 hỗ trợ chọn phạm vi đếm; lịch xoay vòng do người dùng tự sắp xếp.
H3	3.9.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Thủ kho lập phiếu kiểm kê, đếm và nhập số liệu; Trưởng phòng Vật tư (SupplyCore Manager) lập kế hoạch, chứng kiến khi phải đếm lần 3 và phê duyệt chênh lệch lớn; Kế toán (SupplyCore Accountant) lập/nộp phiếu đối soát và soát ảnh hưởng hạch toán. Quản trị Hệ thống có toàn quyền. Lưu ý: phiếu đối soát chỉ người có vai trò Trưởng phòng Vật tư / Kế toán / Quản trị Hệ thống mới được nộp (Submit).
BODY	**Cần có trước:** Kho (SC Warehouse) đã khai báo; vật tư đã có phát sinh tồn trên Sổ kho (SC Stock Ledger Entry) để hệ thống lấy được số lượng và đơn giá tham chiếu; với chênh lệch lớn cần có ngưỡng điều tra trong **SupplyCore Settings** (large_variance_threshold, mặc định 10.000.000 đ); để hạch toán đầy đủ cần khai báo tài khoản kế toán 152 (Hàng tồn kho) và 642 (Chi phí QLDN) trong SC GL Account.
H3	3.9.3	Các bước thực hiện
H4	3.9.3.1	Lập phiếu kiểm kê & nạp danh sách vật tư
OL	Từ Trang chủ, mở **M9**, bấm thẻ **SC Inventory Count Sheet** rồi nhấn **Tạo mới**.
OL	Chọn **Ngày kiểm kê**, **Kho** và **Phạm vi**: **All Items** (toàn kho), **By Item Group** (chọn thêm **Nhóm vật tư**), hoặc **By Zone** (nhập **Zone bin**). Có thể chọn **Người lập kế hoạch** và **Thủ kho đếm**.
OL	Bấm chức năng nạp tự động (**auto_load_items**) để hệ thống đưa vào danh sách mọi vật tư đang còn tồn lớn hơn 0 ở kho theo phạm vi đã chọn; mỗi dòng tự lấy **SL hệ thống** và **Đơn giá tham chiếu** từ Sổ kho. Chỉ nạp được khi phiếu còn ở trạng thái Nháp.
OL	Kiểm tra **Ngưỡng đếm lại (%)** (mặc định 5%) — nếu chênh lệch một dòng vượt ngưỡng này, hệ thống sẽ gắn cờ **Cần đếm lại**. Nhấn **Lưu**.
IMG	Màn hình tạo phiếu kiểm kê: chọn kho, phạm vi và danh sách vật tư vừa nạp.
NOTE	Bạn cũng có thể tự thêm từng dòng vật tư thủ công nếu chỉ kiểm kê một số mặt hàng, không cần nạp toàn bộ.
H4	3.9.3.2	In phiếu đếm (ẩn số lượng hệ thống)
OL	Để tránh người đếm bị ảnh hưởng bởi số trên hệ thống, giữ tùy chọn **Ẩn system_qty khi in** đang bật (mặc định bật).
OL	Lấy dữ liệu in phiếu kiểm kê (**get_count_sheet_print_data**) — khi ẩn, phiếu in ra chỉ có mã vật tư, tên, đơn vị, lô và vị trí (bin), không hiển thị **SL hệ thống**.
OL	Bấm **Start counting** để chuyển phiếu sang trạng thái **In Progress**, báo hiệu đang đếm dở; thủ kho cầm phiếu giấy đi đếm thực tế.
IMG	Phiếu kiểm kê in ra không có cột số lượng hệ thống.
WARN	Chỉ Trưởng phòng Vật tư mới nên xem **SL hệ thống** trong lúc đếm. Bật ẩn cột này khi in để bảo đảm số đếm khách quan.
H4	3.9.3.3	Nhập số đếm, đếm lại & đếm lần 3
OL	Mở lại phiếu, nhập **SL thực tế** cho từng dòng. Nhấn **Lưu** — hệ thống tự tính **Chênh lệch** (= thực tế − hệ thống), **% chênh lệch** và **Δ giá trị** cho từng dòng, đồng thời cập nhật **Tổng items**, **Items chênh lệch**, **Tổng Δ qty**, **Tổng Δ giá trị**.
OL	Với dòng bị gắn **Cần đếm lại** (chênh lệch vượt ngưỡng), đếm lại lần 2 và nhập vào **SL đếm lại**; hệ thống ưu tiên số đếm lại khi tính chênh lệch.
OL	Nếu sau khi đếm lại vẫn còn chênh vượt ngưỡng, nhập **SL đếm lần 3** và bắt buộc chọn **Manager chứng kiến (đếm lần 3)**. Hệ thống ưu tiên số đếm lần 3 cao nhất khi tính chênh lệch.
OL	Khi đếm xong, nhấn **Nộp** (Submit). Phiếu chuyển trạng thái **Counted**.
OL	Nếu có dòng chênh lệch, bấm chức năng **Tạo Stock Reconciliation** (**make_stock_reconciliation**) để sinh phiếu đối soát từ các dòng có chênh lệch.
IMG	Bảng dòng vật tư với SL thực tế, SL đếm lại, SL đếm lần 3 và chênh lệch.
NOTE	Hệ thống tự đặt **Đã đếm** cho dòng đã nhập số, giúp phân biệt giữa "đếm ra 0" và "chưa đếm".
H4	3.9.3.4	Tạo & nộp phiếu đối soát (SR)
OL	Phiếu đối soát có thể được tạo tự động từ phiếu kiểm kê (bước trên) hoặc tạo thủ công: mở thẻ **SC Stock Reconciliation**, **Tạo mới**, chọn **Kho** và **Ngày đối soát**.
OL	Nếu tạo từ phiếu kiểm kê, đặt **Phiếu kiểm kê nguồn** rồi dùng **load_from_count_sheet** để chép các dòng sang. Hệ thống tự điền **SL hệ thống** từ Sổ kho và tính **Δ qty**, **Δ giá trị** từng dòng.
OL	Mỗi dòng có chênh lệch phải chọn **Lý do** (Theft / Damage / System Error / Counting Error / Expired/Discarded / Receiving Error / Other) và có thể ghi **Ghi chú**.
OL	Tùy chọn chọn **TK chi phí điều chỉnh** (để trống sẽ dùng tài khoản 642 mặc định). Nhấn **Lưu**.
OL	Người có vai trò Trưởng phòng Vật tư / Kế toán nhấn **Nộp**. Khi nộp, hệ thống ghi bút toán điều chỉnh vào Sổ kho và sinh bút toán hạch toán (GL); trạng thái phiếu chuyển **Approved** và phiếu kiểm kê nguồn (nếu có) chuyển **Reconciled**.
OL	Để in **Biên bản đối soát** kèm ô ký của Thủ kho / Kế toán / Quản lý, dùng **get_reconciliation_minutes_data**.
IMG	Phiếu đối soát với danh sách dòng điều chỉnh, lý do và tổng chênh lệch.
H4	3.9.3.5	Xử lý chênh lệch lớn (yêu cầu điều tra)
OL	Khi **|Tổng Δ giá trị|** vượt ngưỡng **large_variance_threshold** (mặc định 10.000.000 đ), hệ thống tự bật **Yêu cầu điều tra** và hiện cảnh báo.
OL	Trước khi nộp, phải nhập **Ghi chú điều tra** (investigation_notes). Hệ thống tự ghi **Người điều tra** và **Thời điểm điều tra**.
OL	Trưởng phòng Vật tư xem xét nguyên nhân; nếu chưa thỏa đáng có thể từ chối phiếu (**reject** kèm lý do) — phiếu chuyển trạng thái **Rejected**, lưu **Lý do từ chối**; Thủ kho sửa và nộp lại.
WARN	Phiếu đối soát chỉ được từ chối khi còn ở trạng thái Nháp. Nộp khi đang **Yêu cầu điều tra** mà chưa có ghi chú điều tra sẽ bị chặn (SC-E-SR-INVESTIGATION-REQUIRED).
H4	3.9.3.6	Tạm dừng & tiếp tục kiểm kê
OL	Khi đếm chưa xong, cứ **Lưu** phiếu ở trạng thái Nháp / In Progress; số đã nhập được giữ nguyên.
OL	Quay lại bất kỳ lúc nào, nhập tiếp các dòng còn lại rồi mới **Nộp**.
H3	3.9.4	Trạng thái & phê duyệt
BODY	**Phiếu kiểm kê (SC Inventory Count Sheet):**
TABLE	Trạng thái|Ý nghĩa|Ai chuyển
ROW	Draft (Nháp)|Đang lập, đã nạp/nhập danh sách, chưa đếm xong|Thủ kho
ROW	In Progress (Đang đếm)|Đã bấm Start counting, đang đếm dở|Thủ kho
ROW	Counted (Đã đếm)|Đã nộp phiếu, chờ tạo đối soát|Thủ kho (nộp)
ROW	Reconciled (Đã đối soát)|Đã có phiếu đối soát nộp thành công|Hệ thống tự đặt
ROW	Cancelled (Đã hủy)|Phiếu bị hủy|Người có quyền hủy
BODY	**Phiếu đối soát (SC Stock Reconciliation):**
TABLE	Trạng thái|Ý nghĩa|Ai duyệt
ROW	Draft (Nháp)|Đang lập, chờ nộp|Thủ kho / Kế toán lập
ROW	Approved (Đã duyệt)|Đã nộp; đã ghi Sổ kho + bút toán GL|Trưởng phòng Vật tư / Kế toán nộp
ROW	Rejected (Từ chối)|Bị từ chối kèm lý do, cần sửa lại|Trưởng phòng Vật tư
ROW	Cancelled (Đã hủy)|Đã hủy; bút toán kho + GL được đảo|Người có quyền hủy
H3	3.9.5	Kết quả & truy vết
UL	Phiếu kiểm kê được tạo với mã **SC-ICS-YYYY-#####**, lưu **SL hệ thống** chốt tại thời điểm lập, số đếm các lần và bảng tổng hợp chênh lệch.
UL	Phiếu đối soát được tạo với mã **SC-SR-YYYY-#####**, lưu **Tổng Δ qty** và **Tổng Δ giá trị** (dương = thừa kho, âm = thiếu kho).
UL	Khi nộp phiếu đối soát: ghi bút toán điều chỉnh vào Sổ kho (SC Stock Ledger Entry) theo từng dòng có chênh lệch, cập nhật lại tồn kho thực tế.
UL	Sinh bút toán hạch toán (SC GL Entry): thừa kho ghi Nợ 152 / Có 642; thiếu kho ghi Nợ 642 / Có 152. Nếu chưa khai báo tài khoản 152/642, hệ thống bỏ qua bước GL và cảnh báo.
UL	Phiếu kiểm kê nguồn được liên kết qua trường **SR đã tạo** và tự chuyển sang **Reconciled** khi đối soát nộp thành công.
UL	Mọi thay đổi đều được lưu vết (track changes); nếu có ai cố ghi đè các ô tổng hợp đã khóa, hệ thống ghi nhật ký kiểm toán **SC-E025 ICS_SUMMARY_TAMPERING** và tính lại giá trị đúng.
H3	3.9.6	Lỗi thường gặp & mẹo
UL	**SC-E025 (ICS_SUMMARY_TAMPERING) —** các ô tổng hợp của phiếu kiểm kê luôn do hệ thống tính; mọi cố gắng sửa tay sẽ bị ghi đè và lưu nhật ký. Đừng chỉnh trực tiếp các số tổng.
UL	**SC-E-ICS-WITNESS-REQUIRED —** có dòng nhập SL đếm lần 3 nhưng chưa chọn Manager chứng kiến: chọn **Manager chứng kiến (đếm lần 3)** rồi nộp lại.
UL	**SC-E-SR-MANAGER-REQUIRED —** nộp phiếu đối soát mà không có vai trò Trưởng phòng Vật tư / Kế toán: nhờ đúng người có quyền nộp.
UL	**SC-E-SR-REASON-REQUIRED —** dòng có chênh lệch nhưng chưa chọn lý do: chọn **Lý do** cho mọi dòng có Δ khác 0.
UL	**SC-E-SR-INVESTIGATION-REQUIRED —** chênh lệch giá trị vượt ngưỡng nhưng chưa nhập ghi chú điều tra: điền **Ghi chú điều tra** trước khi nộp.
UL	**SC-E-SR-NEGATIVE —** số thực tế âm: SL thực tế không được nhỏ hơn 0.
UL	**SC-E-SR-REJECT-REASON —** từ chối phiếu mà không nhập lý do: nhập rõ lý do từ chối.
UL	**Mẹo —** luôn bật ẩn SL hệ thống khi in phiếu đếm để số liệu khách quan, tránh người đếm chép theo số trên sổ.
UL	**Mẹo —** dùng phạm vi **By Zone** / **By Item Group** để chia nhỏ thành nhiều đợt đếm xoay vòng thay vì khóa toàn kho một lần.
UL	**Mẹo —** trước khi nộp đối soát, in **Biên bản đối soát** cho các bên ký xác nhận để hồ sơ kiểm kê đầy đủ.
H3	3.9.7	Liên quan
UL	Xem 3.3 — Tiếp nhận & Kiểm tra chất lượng (nguồn nhập tồn kho).
UL	Xem 3.4 — Kho & Sắp xếp (Sổ kho, vị trí bin làm cơ sở đối soát).
UL	Xem 3.5 — FEFO & Hạn dùng (tồn kho theo lô).
UL	Xem 3.8 — Kế toán & Hạch toán (bút toán GL phát sinh khi đối soát).
