H2	3.7	M7 · Cấp phát & BHYT
H3	3.7.1	Mục đích & khi nào dùng
FIRST	Module M7 quản lý toàn bộ chuỗi cấp phát vật tư từ kho ra khoa phòng và xuống tới từng bệnh nhân, kèm tính chi phí Bảo hiểm Y tế (BHYT). Bạn dùng module này khi: khoa cần lĩnh vật tư cho hoạt động thường ngày, ca cấp cứu, hoặc cho một bệnh nhân cụ thể; khi Thủ kho xuất hàng theo nguyên tắc cận hạn xuất trước (FEFO); và khi cần ghi nhận vật tư đã dùng cho bệnh nhân để hệ thống tự chia phần BHYT chi trả và phần bệnh nhân tự trả.
BODY	Module gồm ba loại phiếu nối tiếp nhau. **Yêu cầu cấp phát (SC Dispensing Request, mã SC-DR-…)** do khoa lập để xin vật tư. **Cấp phát cho bệnh nhân (SC Patient Dispensing, mã SC-PD-…)** ghi nhận vật tư thực dùng cho từng người bệnh và tính BHYT. **Cấu hình Mã BHYT (SC BHYT Code Config, mã SC-BHYT-…)** là danh mục tham số do Kế toán/BHYT khai báo để hệ thống biết tỷ lệ chi trả và giá trần cho mỗi vật tư.
H3	3.7.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Điều dưỡng / NV Khoa (SupplyCore Ward Staff) tạo Yêu cầu cấp phát và ghi nhận sử dụng cho bệnh nhân; Thủ kho (SupplyCore Storekeeper) xử lý phiếu, chọn lô theo FEFO và xuất kho; Trưởng phòng Vật tư (SupplyCore Manager) xác nhận khi vượt hạn mức tháng; Kế toán / BHYT Officer / Quản trị Hệ thống cấu hình Mã BHYT. Dược/QC (Pharmacy Officer) cũng được tạo và nộp phiếu.
BODY	**Cần có trước:** Vật tư (SC Item), Kho (SC Warehouse), Khoa (SC Department) và — nếu cấp theo bệnh nhân — hồ sơ Bệnh nhân (SC Patient) đã khai báo. Vật tư cần có tồn kho khả dụng tại kho cấp. Mã BHYT của vật tư phải được cấu hình trước thì phiếu cấp phát cho bệnh nhân mới chia được phần BHYT. Khoa có thể đặt **Hạn mức cấp phát tháng (monthly_dispensing_quota)** để kiểm soát giá trị xuất.
NOTE	Đơn vị kép (BR-BH-03): mỗi vật tư có thể khai **Đơn vị mua (buy_uom)** khác **Đơn vị sử dụng/BHYT (use_uom)** kèm **Hệ số quy đổi mua → dùng**. Ví dụ mua theo hộp nhưng cấp phát và tính BHYT theo viên. Hãy chọn đúng đơn vị trên dòng phiếu để số lượng và chi phí khớp với cách BHYT thanh toán.
H3	3.7.3	Các bước thực hiện
H4	3.7.3.1	Tạo Yêu cầu cấp phát (Điều dưỡng / NV Khoa)
OL	Từ Trang chủ, mở **M7 · Cấp phát & BHYT**, bấm thẻ **Yêu cầu cấp phát** rồi nhấn **Tạo mới**.
OL	Chọn **Ngày yêu cầu** (mặc định hôm nay), **Mục đích** (Routine = thường quy, Urgent = cấp cứu, Patient-Specific = theo bệnh nhân) và **Khoa yêu cầu** (bắt buộc). Trường **Người yêu cầu** tự điền theo tài khoản đăng nhập.
OL	Nếu Mục đích là **Patient-Specific**, ô **Bệnh nhân** sẽ hiện ra và bắt buộc chọn; nếu là Routine/Urgent thì cấp cho khoa, không gắn bệnh nhân.
OL	Chọn **Kho cấp** rồi thêm các dòng vật tư trong bảng **Vật tư**: **Mã VT**, **SL yêu cầu**, **UOM**. Có thể nhập **Lý do yêu cầu** và **Ngày cần**.
OL	Nhấn **Lưu**. Hệ thống tính **Tổng SL** và **Tổng ước tính (VND)** theo giá mua gần nhất của vật tư.
OL	Nhấn **Nộp** để gửi duyệt. Khi nộp, hệ thống kiểm tra hạn mức tháng của khoa và kiểm tra tồn khả dụng tại kho cấp; nếu hợp lệ, trạng thái chuyển sang **Approved** và Thủ kho nhận phiếu.
IMG	Màn hình tạo Yêu cầu cấp phát với phần Mục đích, Khoa, Kho cấp và bảng dòng vật tư.
NOTE	Khi tổng giá trị cấp phát trong tháng của khoa vượt **Hạn mức cấp phát tháng**, hệ thống chặn nộp (lỗi SC-E-DR-QUOTA-EXCEEDED). Trưởng phòng Vật tư phải tích ô **Xác nhận vượt hạn mức (Manager)** rồi nộp lại.
H4	3.7.3.2	Thủ kho cấp phát theo FEFO
OL	Mở **Danh sách** Yêu cầu cấp phát, lọc theo trạng thái **Approved** để xem các phiếu chờ xuất, rồi mở phiếu cần xử lý.
OL	Dùng chức năng **Auto FEFO** (auto_pick_fefo_for_dr) để hệ thống tự chọn **Lô** cận hạn xuất trước và điền **SL duyệt** cho từng dòng. Nếu tồn không đủ, hệ thống tự ghi **Ghi chú thiếu hàng** và hạ SL duyệt xuống mức cấp được.
OL	Kiểm tra lại **SL duyệt** và **Lô** từng dòng. Nếu cấp thiếu so với yêu cầu (partial), ghi rõ lý do vào **Ghi chú thiếu hàng**.
OL	Bấm tạo Stock Entry (make_stock_entry). Hệ thống đối chiếu tồn hệ thống với tồn thực; nếu khớp sẽ sinh một **SC Stock Entry** loại **Material Issue** từ Kho cấp, ghi sổ kho và chuyển phiếu sang **Issued**. Trưởng khoa nhận email báo vật tư đã sẵn sàng.
OL	Dùng dữ liệu phiếu cấp phát có mã vạch (get_dispensing_slip_data) để in phiếu giao cho khoa khi cần.
IMG	Phiếu cấp phát ở trạng thái Approved với nút Auto FEFO và các dòng đã điền lô và SL duyệt.
WARN	Nếu tồn kho hệ thống không khớp tồn thực (thiếu hụt), hệ thống chặn bước tạo Stock Entry với lỗi SC-E-DR-STOCK-MISMATCH. Phải tạo **SC Stock Reconciliation** để chỉnh tồn trước khi cấp phát.
H4	3.7.3.3	Ghi nhận sử dụng cho bệnh nhân & tính BHYT
OL	Mở thẻ **Cấp phát cho bệnh nhân** rồi **Tạo mới**; hoặc với phiếu DR Patient-Specific đã có Stock Entry, dùng chức năng make_patient_dispensing để sinh sẵn phiếu PD.
OL	Chọn **Mã BN** (có thể tra theo số thẻ qua lookup_patient_by_bhyt). Hệ thống tự lấy **Họ tên**, **Số thẻ BHYT**, **Loại BHYT** và **Tỷ lệ BHYT BN** từ hồ sơ bệnh nhân. Chọn **Khoa** và **Ngày cấp phát**.
OL	Thêm các dòng **Vật tư sử dụng** (có thể lấy từ phiếu đã cấp cho khoa qua get_dispensed_items_for_dr): nhập **SL dùng**, **Đơn giá**, **Lô** và **Kho cấp**.
OL	Nhấn **Lưu**. Hệ thống tự tra Mã BHYT của từng vật tư theo ngày cấp và tính: **BHYT chi trả**, **BN tự trả**, **Phần vượt giá trần** cho từng dòng và tổng phiếu.
OL	Nhấn **Nộp**. Hệ thống ghi sổ kho (xuất âm tồn theo lô) và đồng bộ phiếu DR liên kết sang trạng thái **Dispensed**.
IMG	Phiếu Cấp phát cho bệnh nhân với cột BHYT chi trả, BN tự trả và Phần vượt giá trần.
NOTE	Quy tắc tính BHYT mỗi dòng: nếu bệnh nhân không có thẻ BHYT, hoặc vật tư không có cấu hình BHYT → bệnh nhân tự trả 100%. Tỷ lệ áp dụng lấy theo cấu hình, nhưng nếu Tỷ lệ BHYT của bệnh nhân thấp hơn thì lấy tỷ lệ thấp hơn. Nếu đơn giá vượt **Giá trần**, phần vượt do bệnh nhân tự trả (Phần vượt giá trần).
H4	3.7.3.4	Cấu hình Mã BHYT (Kế toán / BHYT Officer / Admin)
OL	Mở thẻ **Cấu hình Mã BHYT** (SC BHYT Code Config) rồi **Tạo mới**.
OL	Nhập **Mã BHYT**, **Tên BHYT**, chọn **Nhóm BHYT** (N01–N09, mặc định N05) và **Tỷ lệ thanh toán BHYT (%)** (mặc định 80). Nhập **Giá trần BHYT/đơn vị** nếu có (để trống = không áp giá trần).
OL	Khai **Phạm vi áp dụng**: chọn **Vật tư cụ thể** cho cấu hình riêng một vật tư, hoặc để trống và chọn **Nhóm vật tư** để áp cho cả nhóm. Cần ít nhất một trong hai.
OL	Đặt **Hiệu lực từ** và **Hết hiệu lực** (để trống = chưa kết thúc), ghi **Căn cứ pháp lý** (ví dụ TT 04/2024/TT-BYT) rồi **Lưu**.
OL	Khi quy định thay đổi: đóng bản cũ bằng cách đặt **Hết hiệu lực**, sau đó tạo bản mới có **Hiệu lực từ** kế tiếp. Có thể nhập hàng loạt bằng Frappe Data Import (System Manager).
IMG	Màn hình Cấu hình Mã BHYT với Nhóm, Tỷ lệ, Giá trần, Phạm vi và Hiệu lực.
NOTE	Thứ tự ưu tiên khi tra BHYT cho một vật tư: (1) cấu hình theo Vật tư cụ thể, (2) cấu hình theo Nhóm vật tư, (3) thông tin BHYT khai sẵn trên thẻ vật tư (has_bhyt). Hệ thống luôn lấy bản đang hiệu lực tại ngày cấp.
H3	3.7.4	Trạng thái & phê duyệt
BODY	Yêu cầu cấp phát (SC-DR-…) đi theo vòng đời sau; trạng thái do hệ thống tự đặt theo thao tác, người dùng không sửa tay.
TABLE	Trạng thái|Ý nghĩa|Ai chuyển
ROW	Draft (Nháp)|Đang soạn, chưa nộp|Điều dưỡng / NV Khoa
ROW	Pending (Chờ duyệt)|Đã nộp, chờ xử lý (trạng thái trung gian)|Hệ thống
ROW	Approved (Đã duyệt)|Đã nộp hợp lệ, sẵn sàng để Thủ kho xuất|Hệ thống khi Nộp
ROW	Issued (Đã xuất)|Đã tạo Stock Entry Material Issue, ghi sổ kho|Thủ kho khi tạo Stock Entry
ROW	Dispensed (Đã cấp cho BN)|Đã ghi nhận sử dụng cho bệnh nhân|Hệ thống khi nộp Cấp phát cho bệnh nhân
ROW	Cancelled (Đã hủy)|Phiếu bị hủy|Người có quyền Hủy
BODY	**Phê duyệt vượt hạn mức:** nếu giá trị cấp phát trong tháng của khoa vượt **Hạn mức cấp phát tháng**, chỉ Trưởng phòng Vật tư tích **Xác nhận vượt hạn mức (Manager)** mới nộp được phiếu. Phiếu Cấp phát cho bệnh nhân (SC-PD-…) là phiếu nộp/hủy: khi nộp thì ghi sổ kho và đẩy DR sang Dispensed; khi hủy thì đảo bút toán sổ kho.
H3	3.7.5	Kết quả & truy vết
UL	Yêu cầu cấp phát tạo bản ghi mã **SC-DR-{YYYY}-{#####}** với Tổng SL và Tổng ước tính (VND).
UL	Khi Thủ kho xuất kho: sinh **SC Stock Entry** loại **Material Issue**, ghi vào Sổ kho (SC Stock Ledger Entry) làm giảm tồn theo từng lô; phiếu liên kết qua trường **Stock Entry**.
UL	Cấp phát cho bệnh nhân tạo bản ghi mã **SC-PD-{YYYY}-{#####}** với **Tổng chi phí**, **BHYT chi trả**, **BN tự trả**, **Phần vượt giá trần**; mỗi dòng lưu Mã BHYT, Nhóm, Tỷ lệ %, Giá trần áp dụng.
UL	Cấu hình BHYT tạo bản ghi mã **SC-BHYT-{#####}**, lưu lịch sử thay đổi (track_changes) và căn cứ pháp lý phục vụ kiểm toán.
UL	Lịch sử chi phí của bệnh nhân tổng hợp được qua get_patient_dispense_history; lịch sử cấu hình BHYT của một vật tư xem qua list_bhyt_configs_for_item / get_bhyt_history.
UL	Trưởng khoa nhận email thông báo khi phiếu chuyển sang Issued (vật tư sẵn sàng).
H3	3.7.6	Lỗi thường gặp & mẹo
UL	**SC-E-DR-QUOTA-EXCEEDED — Vượt hạn mức cấp phát tháng:** Trưởng phòng Vật tư tích **Xác nhận vượt hạn mức (Manager)** rồi nộp lại.
UL	**SC-E010 NEGATIVE_STOCK — Không đủ tồn khả dụng:** giảm SL duyệt hoặc tạo Stock Reconciliation; tồn khả dụng đã loại trừ lô đang QC Pending/Rejected hoặc bị khóa.
UL	**SC-E-DR-STOCK-MISMATCH — Tồn hệ thống lệch tồn thực:** tạo SC Stock Reconciliation trước rồi mới tạo Stock Entry.
UL	**SC-E-RCL-BATCH-RECALLED — Lô đang bị thu hồi/khóa:** không thể cấp phát; chọn lô khác.
UL	**SC-E-BHYT-RATE — Tỷ lệ thanh toán ngoài [0..100]:** nhập lại tỷ lệ trong khoảng 0 đến 100.
UL	**SC-E-BHYT-OVERLAP — Cấu hình trùng phạm vi và thời hạn:** đóng bản cũ (đặt Hết hiệu lực) trước khi tạo bản mới.
UL	**Mẹo —** nếu cảnh báo "Mã BHYT có thay đổi quy định" hiện lên khi lưu phiếu bệnh nhân, hãy kiểm tra lại cấu hình BHYT của vật tư đó trước khi nộp (cờ bhyt_config_changed).
UL	**Mẹo —** bệnh nhân không có thẻ BHYT hoặc vật tư chưa cấu hình BHYT thì cột BN tự trả sẽ bằng toàn bộ chi phí; muốn BHYT chi trả, cần khai số thẻ cho bệnh nhân và cấu hình Mã BHYT cho vật tư.
UL	**Mẹo —** dùng **Auto FEFO** thay vì chọn lô thủ công để luôn xuất đúng lô cận hạn trước và tránh tồn hết hạn.
H3	3.7.7	Liên quan
UL	Xem 3.5 — M5 Tồn kho & FEFO (cơ chế gợi ý lô cận hạn xuất trước).
UL	Xem 3.4 — M4 Xuất kho / Stock Entry (phiếu Material Issue sinh ra khi cấp phát).
UL	Xem 3.3 — M3 Tiếp nhận & Kiểm tra chất lượng (tồn khả dụng loại trừ lô QC Pending/Rejected).
UL	Xem 3.9 — M9 Thu hồi (lô bị khóa không được cấp phát).
UL	Xem chương Dữ liệu nền — khai báo SC Item (đơn vị kép, BHYT), SC Patient, SC Department (hạn mức cấp phát tháng).
