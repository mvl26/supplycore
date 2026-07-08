H2	3.1	M1 · Hợp đồng khung & Nhà cung cấp
H3	3.1.1	Mục đích & khi nào dùng
FIRST	Module M1 là nền móng cho mọi giao dịch mua hàng trong SupplyCore. Tại đây bạn khai báo và theo dõi Nhà cung cấp (SC Supplier), ký và quản lý Hợp đồng khung (Framework Contract — mã SC-FC-…) với từng NCC, rồi phát Lệnh gọi hàng (Release Order — mã SC-RO-…) để rút vật tư theo hợp đồng và chuyển thành Đơn đặt hàng (PO).
BODY	Bạn vào M1 khi: cần thêm/sửa thông tin một NCC; lập hợp đồng khung mới và đưa qua quy trình duyệt nhiều cấp; gọi hàng theo hợp đồng đã có; gia hạn hoặc thanh lý hợp đồng; hoặc tra cứu hạn mức còn lại, điểm đánh giá và giấy tờ pháp lý của NCC trước khi đặt hàng.
BODY	**Vì sao quan trọng:** hợp đồng khung giữ sẵn đơn giá và số lượng cam kết, đồng thời tự theo dõi giá trị Đã sử dụng / Đang gọi / Còn lại khả dụng. Nhờ đó mọi PO sinh ra đều bám đúng giá hợp đồng và không vượt hạn mức.
H3	3.1.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** NV Mua sắm và Trưởng phòng Vật tư (cùng Kế toán) tạo và sửa Nhà cung cấp. Hợp đồng khung do Kế toán hoặc Trưởng phòng Vật tư soạn; NV Mua sắm chỉ xem. Phê duyệt hợp đồng theo 3 cấp: người soạn **Gửi duyệt** → **Trưởng phòng Vật tư** (SupplyCore Manager) duyệt → **Lãnh đạo** (SupplyCore Executive) duyệt nếu giá trị vượt ngưỡng. Lệnh gọi hàng do NV Mua sắm soạn, Trưởng phòng Vật tư nộp (Submit).
BODY	**Cần có trước:** Nhà cung cấp đã khai báo (kèm Mã số thuế hợp lệ); các Vật tư (SC Item), Đơn vị tính (SC UOM) và Nhóm vật tư (SC Item Group) đã có trong Dữ liệu nền; với hợp đồng khung phải biết đơn giá và số lượng cam kết cho từng vật tư; với lệnh gọi hàng phải có một hợp đồng khung đang **Hiệu lực**.
NOTE	Ngưỡng duyệt Lãnh đạo lấy từ trường **fc_executive_threshold** trong SupplyCore Settings, mặc định 100.000.000 VND. Hợp đồng có Tổng giá trị từ ngưỡng trở lên bắt buộc qua thêm cấp Lãnh đạo; dưới ngưỡng thì Trưởng phòng duyệt là đủ.
H3	3.1.3	Các bước thực hiện
H4	3.1.3.1	Quản lý Nhà cung cấp (tạo, blacklist, chứng chỉ, đánh giá)
OL	Từ Trang chủ, mở **Dữ liệu nền (M0)** và bấm thẻ **Nhà cung cấp**, rồi nhấn **Tạo mới** (hoặc mở một NCC sẵn có để sửa).
OL	Nhập **Tên NCC**, **Mã số thuế** (10 hoặc 13 chữ số theo Thông tư 105/2020/TT-BTC), **Loại NCC**, cùng các trường liên hệ bắt buộc: **Email**, **Điện thoại**, **Địa chỉ**. **Mã NCC** (SC-SUP-#####) tự sinh, không cần nhập.
OL	Khai phần **Thanh toán** (Điều khoản thanh toán, Hạn mức tín dụng, thông tin ngân hàng) và bảng **Danh mục vật tư cung ứng** để liệt kê các nhóm vật tư NCC cung cấp.
OL	Mở mục **Giấy tờ pháp lý** để ghi **Số GPKD** và đính kèm file, **Số GPP/GDP** kèm **Hết hạn GPP**, **Số ISO** kèm file ISO.
OL	Nhấn **Lưu**. Khi cần ngừng hợp tác có rủi ro, tích ô **Blacklist** (đưa NCC vào danh sách đen — chặn tạo PO mới); tích **Disabled** nếu chỉ muốn ẩn NCC khỏi lựa chọn.
IMG	Màn hình chi tiết Nhà cung cấp với các mục Liên hệ, Thanh toán, Giấy tờ pháp lý và Đánh giá NCC.
BODY	**Đánh giá NCC:** trường **Điểm trung bình (0-5)** và **Số lần đánh giá** là chỉ là số đọc (read-only) do hệ thống tính, không nhập tay. SupplyCore tổng hợp scorecard 12 tháng gần nhất của NCC: số hợp đồng đang hiệu lực và hạn mức còn lại, số PO và giá trị mua, tỷ lệ giao đúng hạn, tỷ lệ đạt QC, công nợ phải trả và số cảnh báo còn mở — dùng để xem nhanh năng lực NCC trước khi ký hợp đồng.
H4	3.1.3.2	Tạo Hợp đồng khung & gửi duyệt
OL	Từ Trang chủ mở **M1 · Hợp đồng**, bấm thẻ **Hợp đồng khung** rồi nhấn **Tạo mới**.
OL	Chọn **Nhà cung cấp**, nhập **Số hợp đồng** (không trùng), **Ngày ký**, **Hiệu lực từ** và **Hết hạn**. Ngày hết hạn phải sau ngày hiệu lực và ngày ký không được sau ngày hiệu lực.
OL	Tại bảng **Danh mục vật tư trong hợp đồng**, thêm từng dòng: **Mã VT**, **Đơn vị**, **SL hợp đồng** và **Đơn giá**. **Thành tiền** mỗi dòng và **Tổng giá trị (VND)** của hợp đồng được tính tự động (read-only).
OL	Khai thêm **Điều khoản thanh toán**, **Điều khoản giao hàng**, đính kèm **File hợp đồng (PDF)** nếu có, rồi nhấn **Lưu**. Hợp đồng ở trạng thái **Nháp** và giai đoạn phê duyệt **Draft**.
OL	Nhấn **Gửi duyệt** để khởi động quy trình. Hợp đồng chuyển sang giai đoạn **Manager Review** và chờ Trưởng phòng Vật tư.
IMG	Màn hình Hợp đồng khung với bảng danh mục vật tư và khối giá trị Đã sử dụng / Đang gọi / Còn lại.
WARN	Nếu NCC đang trong **Blacklist**, khi còn ở Nháp hệ thống chỉ cảnh báo; nhưng để duyệt và nộp được thì Lãnh đạo phải tích ô **Lãnh đạo xác nhận override blacklist**, nếu không sẽ bị chặn (SC-E-FC-BLACKLIST).
H4	3.1.3.3	Duyệt hợp đồng (Trưởng phòng → Lãnh đạo)
OL	Trưởng phòng Vật tư mở hợp đồng đang ở **Manager Review**, nhấn **Duyệt (Quản lý)** và nhập **Ghi chú Quản lý** (bắt buộc tối thiểu 10 ký tự để phục vụ audit).
OL	Hệ thống so Tổng giá trị với ngưỡng: nếu nhỏ hơn ngưỡng, hợp đồng chuyển thẳng sang **Approved**; nếu bằng hoặc lớn hơn ngưỡng, chuyển sang **Executive Review** chờ Lãnh đạo.
OL	Lãnh đạo mở hợp đồng ở **Executive Review**, nhấn **Duyệt (Lãnh đạo)** và nhập ghi chú (tối thiểu 10 ký tự); hợp đồng chuyển sang **Approved**.
OL	Người soạn (hoặc người có quyền) nhấn **Nộp (Submit)** để kích hoạt. Hợp đồng chuyển docstatus = đã nộp và trạng thái thành **Hiệu lực** (Active).
OL	Khi cần từ chối: ở bước Manager hoặc Executive, người duyệt nhấn **Từ chối** và bắt buộc nhập **Lý do từ chối**; giai đoạn chuyển **Rejected**. Người soạn sửa lại rồi **Gửi duyệt** lần nữa để chạy lại quy trình.
WARN	Sau khi đã **Approved** nhưng chưa Nộp, hợp đồng bị khóa sửa nội dung (SC-E-FC-LOCKED). Khi đó chỉ còn hai lựa chọn: **Nộp** để kích hoạt, hoặc **Từ chối** để gửi lại từ đầu.
H4	3.1.3.4	Gia hạn hợp đồng
OL	Mở hợp đồng đã Nộp (Hiệu lực), dùng chức năng **Gia hạn**: nhập **Hết hạn mới** và **Lý do gia hạn**.
OL	Một dòng mới được thêm vào bảng **Lịch sử gia hạn** với trạng thái **Pending** (Chờ duyệt).
OL	Trưởng phòng Vật tư duyệt yêu cầu (Lãnh đạo duyệt nếu hợp đồng từ ngưỡng trở lên). Khi **Approved**, trường **Hết hạn** của hợp đồng được cập nhật và trạng thái tính lại.
OL	Nếu không phù hợp, người duyệt **Từ chối** dòng gia hạn (trạng thái dòng chuyển **Rejected**), hợp đồng giữ nguyên ngày hết hạn cũ.
WARN	Ngày hết hạn mới phải SAU ngày hết hạn hiện tại. Không thể gia hạn nếu hợp đồng đã quá hạn hơn 90 ngày (SC-E-FC-EXPIRED-90D) — khi đó phải tạo hợp đồng mới.
H4	3.1.3.5	Thanh lý / kết thúc hợp đồng
OL	Trưởng phòng Vật tư mở hợp đồng đã Nộp, dùng chức năng **Thanh lý**, nhập **Lý do thanh lý** và đính kèm **Biên bản thanh lý (PDF)** nếu có.
OL	Trạng thái hợp đồng chuyển **Kết thúc** (Terminated) và ghi **Ngày thanh lý**.
OL	Mọi Lệnh gọi hàng còn ở Nháp tham chiếu hợp đồng này tự động bị chuyển **Đã huỷ** (Cancelled), tránh gọi hàng trên hợp đồng đã chấm dứt.
NOTE	Hủy (Cancel) một hợp đồng đã Nộp cũng đưa trạng thái về **Kết thúc** và chặn các RO Nháp tương tự như thanh lý.
H4	3.1.3.6	Tạo Lệnh gọi hàng (Release Order) & chuyển thành PO
OL	Mở danh sách **Lệnh gọi hàng** (Release Order) và nhấn **Tạo mới**.
OL	Chọn **Hợp đồng khung** (phải đang Hiệu lực). **Nhà cung cấp** và **Tên NCC** tự điền theo hợp đồng. Khi để trống bảng vật tư, hệ thống tự nạp các dòng còn số lượng từ hợp đồng với SL = 0.
OL	Nhập **Ngày lệnh**, **Ngày cần giao** (không trước ngày lệnh) và điền **SL** cần gọi cho từng vật tư. Đơn giá lấy theo hợp đồng, **Tổng giá trị (VND)** tự tính.
OL	Nhấn **Lưu** rồi **Nộp (Submit)**. Lệnh chuyển trạng thái **Đã duyệt** (Approved); hệ thống chụp lại hạn mức còn lại của hợp đồng tại thời điểm tạo và tăng giá trị **Đang gọi** của hợp đồng.
OL	Khi sẵn sàng đặt hàng, dùng chức năng **Tạo Purchase Order** trên lệnh đã Approved. Hệ thống sinh một **SC Purchase Order** (Nháp) gắn link hợp đồng + lệnh gọi hàng; lệnh chuyển trạng thái **Converted** và lưu link PO.
IMG	Màn hình Lệnh gọi hàng sau khi nạp vật tư từ hợp đồng, với cột SL còn lại khả dụng.
WARN	Số lượng gọi mỗi vật tư không được vượt **SL còn lại** trong hợp đồng và tổng giá trị lệnh không được vượt **Còn lại khả dụng** của hợp đồng, nếu không sẽ báo lỗi SC-E002 FC_EXCEEDED.
H3	3.1.4	Trạng thái & phê duyệt
BODY	**Hợp đồng khung** có hai trục song song: Giai đoạn phê duyệt (approval_stage) và Trạng thái vòng đời (status).
TABLE	Giai đoạn phê duyệt|Ý nghĩa|Ai xử lý
ROW	Draft (Nháp)|Đang soạn, chưa gửi duyệt|Người soạn (Kế toán/Trưởng phòng)
ROW	Manager Review|Đã Gửi duyệt, chờ Trưởng phòng|Trưởng phòng Vật tư
ROW	Executive Review|Giá trị ≥ ngưỡng, chờ Lãnh đạo|Lãnh đạo
ROW	Approved (Đã duyệt)|Đã duyệt đủ cấp, chờ Nộp kích hoạt|Người soạn nhấn Nộp
ROW	Rejected (Từ chối)|Bị từ chối, cần sửa và gửi lại|Người soạn
TABLE	Trạng thái HĐ|Ý nghĩa
ROW	Nháp (Draft)|Chưa Nộp
ROW	Hiệu lực (Active)|Đã Nộp, còn hạn và còn hạn mức — gọi hàng được
ROW	Hết hạn (Expired)|Đã quá ngày Hết hạn
ROW	Hết hạn mức (Exhausted)|Còn lại khả dụng ≤ 0 — không tạo PO mới dù còn hạn
ROW	Kết thúc (Terminated)|Đã thanh lý hoặc bị hủy
BODY	**Lệnh gọi hàng** có 4 trạng thái: **Nháp** (Draft) đang soạn; **Đã duyệt** (Approved) đã Nộp, đã chiếm hạn mức Đang gọi; **Converted** đã sinh PO; **Đã huỷ** (Cancelled) bị hủy hoặc bị chặn do hợp đồng thanh lý.
H3	3.1.5	Kết quả & truy vết
UL	Nhà cung cấp tạo ra bản ghi mã **SC-SUP-#####**, kèm scorecard 12 tháng và các giấy tờ pháp lý đính kèm.
UL	Hợp đồng khung tạo bản ghi mã **SC-FC-YYYY-#####**; tự cập nhật **Đã sử dụng** (Σ grand_total các PO đã nộp), **Đang gọi** (Σ các RO Approved chưa convert) và **Còn lại khả dụng**.
UL	Lệnh gọi hàng tạo bản ghi mã **SC-RO-YYYY-#####**; khi chuyển đổi sẽ sinh **SC Purchase Order** và lưu link hai chiều để truy vết.
UL	Lịch sử gia hạn và thông tin thanh lý (ngày, lý do, biên bản) lưu ngay trên hợp đồng phục vụ kiểm toán.
UL	Tác vụ nền chạy hằng ngày cảnh báo hợp đồng sắp hết hạn ở mốc **30 / 15 / 7 ngày** (gửi email và bật cờ **Sắp hết hạn (≤30 ngày)** trên hợp đồng), liên thông cảnh báo ở M11.
H3	3.1.6	Lỗi thường gặp & mẹo
UL	**SC-E021 INVALID_TAX_ID — Mã số thuế sai định dạng:** nhập đúng 10 chữ số (vd 0301110116) hoặc 13 chữ số cho đơn vị phụ thuộc.
UL	**SC-E-DUPLICATE-TAX-ID — MST đã tồn tại ở NCC khác:** tra lại NCC cũ thay vì tạo trùng.
UL	**SC-E026 APPROVAL_COMMENT_TOO_SHORT — Ghi chú duyệt quá ngắn:** ghi chú khi duyệt phải tối thiểu 10 ký tự, nêu rõ cơ sở duyệt.
UL	**SC-E-FC-NOT-APPROVED — Chưa duyệt đủ 3 cấp:** không thể Nộp khi giai đoạn chưa phải Approved; bấm **Gửi duyệt** để bắt đầu quy trình.
UL	**SC-E-FC-LOCKED — Đã duyệt nên khóa sửa:** chỉ còn lựa chọn Nộp hoặc Từ chối; muốn sửa nội dung phải Từ chối rồi soạn lại.
UL	**SC-E-FC-BLACKLIST — NCC trong danh sách đen:** cần Lãnh đạo tích ô override blacklist mới tiếp tục được.
UL	**SC-E-FC-EXPIRED-90D — Hết hạn quá 90 ngày:** không gia hạn lùi được, hãy tạo hợp đồng mới.
UL	**SC-E002 FC_INACTIVE / FC_EXPIRED — Hợp đồng không Hiệu lực hoặc đã hết hạn:** chỉ tạo lệnh gọi hàng trên hợp đồng đang Hiệu lực và còn hạn.
UL	**SC-E002 FC_EXCEEDED / FC_ITEM_NOT_FOUND — Vượt hạn mức hoặc vật tư ngoài hợp đồng:** giảm số lượng/giá trị, hoặc chỉ gọi vật tư có trong hợp đồng.
UL	**Mẹo —** xem khối **Còn lại khả dụng** trên hợp đồng trước khi lập lệnh gọi hàng để tránh bị chặn vượt hạn mức.
UL	**Mẹo —** dùng nút **Xuất** ở màn hình Danh sách để tải hợp đồng/NCC ra Excel cho báo cáo, và tích **Blacklist** thay vì xóa khi muốn chặn NCC.
H3	3.1.7	Liên quan
UL	Xem 3.2 — Lập kế hoạch & Đặt hàng (M2): tạo PO từ hợp đồng/lệnh gọi hàng, đơn giá lấy theo hợp đồng khung.
UL	Xem 3.3 — Tiếp nhận & Kiểm tra chất lượng (M3): nhận hàng theo PO làm tăng giá trị Đã sử dụng của hợp đồng.
UL	Xem mục Dữ liệu nền (M0): khai báo Vật tư, Đơn vị tính, Nhóm vật tư và Nhà cung cấp trước khi lập hợp đồng.
UL	Xem 3.11 — Dashboard & Cảnh báo (M11): theo dõi cảnh báo hợp đồng sắp hết hạn và điểm đánh giá NCC.
