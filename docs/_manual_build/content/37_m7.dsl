# Mục 3.7 — M7 · Bán hàng & Bàn giao (Order-to-Cash). Soạn theo AUTHOR_GUIDE; nhãn lấy đúng từ code.
H2	3.7	M7 · Bán hàng & Bàn giao
H3	3.7.1	Mục đích & khi nào dùng
FIRST	Module M7 quản lý toàn bộ vòng đời bán hàng cho khách: từ hợp đồng khung bán, đơn hàng của khách, soạn hàng và giao hàng, biên bản nghiệm thu, đến hóa đơn bán và thu tiền. Bạn dùng module này khi: ký hợp đồng khung với một khách hàng để chốt danh mục và giá; nhận đơn đặt hàng (khách gọi điện, gửi email, hoặc tự đặt trên Cổng khách hàng); thủ kho soạn hàng và giao cho khách; và khi kế toán xuất hóa đơn, theo dõi công nợ phải thu.
BODY	Chuỗi chứng từ nối tiếp nhau theo thứ tự cố định. **Khách hàng (SC Customer)** là hồ sơ khách. **Hợp đồng khung bán (SC Sales Framework Contract)** khóa danh mục vật tư, đơn giá và số lượng trần cho một kỳ. **Đơn hàng bán (SC Sales Order)** là đơn khách đặt. **Phiếu giao hàng (SC Delivery Note)** ghi nhận hàng thực xuất kho theo lô. **Biên bản nghiệm thu (SC Acceptance Record)** xác nhận khách đã nhận đủ. **Hóa đơn bán (SC Sales Invoice)** ghi doanh thu và công nợ. **Phiếu thu (SC Sales Receipt)** tất toán công nợ.
NOTE	Nguyên tắc xuyên suốt: **giá luôn lấy từ hợp đồng khung**, người dùng và kế toán không sửa được; và **phải có nghiệm thu mới xuất được hóa đơn**. Hai chốt này bảo vệ doanh thu khỏi sai giá và khỏi xuất hóa đơn cho hàng khách chưa nhận.
H3	3.7.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** NV Mua & Bán hàng (SupplyCore Purchaser) tạo Khách hàng, Hợp đồng khung bán, Đơn hàng và duyệt đơn. Thủ kho (SupplyCore Storekeeper) soạn hàng, quét xác nhận và nộp Phiếu giao hàng, lập Biên bản nghiệm thu. Kế toán (SupplyCore Accountant) lập Hóa đơn bán và Phiếu thu, theo dõi công nợ phải thu. Trưởng phòng (SupplyCore Manager) có toàn quyền và giám sát toàn chuỗi. Khách hàng tự đặt hàng và tự nghiệm thu qua Cổng khách hàng (xem 3.12).
BODY	**Cần có trước:** Vật tư (SC Item), Kho (SC Warehouse) và Đơn vị tính đã khai trong Dữ liệu nền. Khách hàng đã tạo hồ sơ, có **Hạn mức tín dụng** nếu muốn kiểm soát công nợ. Hợp đồng khung bán còn hiệu lực nếu bán theo hợp đồng. Kho xuất còn đủ **tồn khả dụng** (không tính lô đang chờ QC, bị từ chối hoặc bị khóa do thu hồi).
NOTE	Đơn vị kép: một vật tư có thể mua theo thùng/hộp nhưng bán và xuất theo cái. Khai bảng **Quy đổi đơn vị kép** trên thẻ vật tư (1 đơn vị này = bao nhiêu đơn vị tồn kho). Sổ kho luôn ghi theo **đơn vị tồn kho**; quy đổi chỉ phục vụ nhập liệu và hiển thị.
H3	3.7.3	Các bước thực hiện
H4	3.7.3.1	Tạo hồ sơ Khách hàng
OL	Từ Trang chủ, mở khối **BÁN HÀNG**, bấm thẻ **Khách hàng** rồi nhấn **Tạo mới**.
OL	Điền **Tên khách hàng**, **Mã số thuế**, **Địa chỉ**, **Điện thoại**, **Người liên hệ**.
OL	Đặt **Hạn mức tín dụng** nếu muốn hệ thống tự chặn đơn khi khách nợ quá mức. Để trống thì dùng hạn mức mặc định trong Cấu hình hệ thống.
OL	Nếu khách sẽ tự đặt hàng qua Cổng khách hàng, điền **Tài khoản Portal** (email tài khoản đăng nhập của khách). Mỗi tài khoản Portal chỉ được gắn đúng một khách hàng.
OL	Nhấn **Lưu**.
IMG	Màn hình chi tiết Khách hàng với hạn mức tín dụng và tài khoản Portal.
WARN	**Tài khoản Portal là trục cô lập dữ liệu.** Gán nhầm tài khoản sang khách khác sẽ khiến khách đó nhìn thấy đơn hàng, hóa đơn và công nợ của khách kia. Kiểm tra kỹ trước khi lưu.
H4	3.7.3.2	Lập Hợp đồng khung bán
OL	Bấm thẻ **HĐ khung bán** rồi **Tạo mới**. Chọn **Khách hàng**, đặt **Hiệu lực từ** và **Hiệu lực đến**.
OL	Trong bảng danh mục, thêm từng dòng vật tư: **Mã VT**, **Đơn vị**, **Đơn giá** (giá chốt theo hợp đồng) và **SL hợp đồng** (số lượng trần khách được đặt trong kỳ).
OL	Nhấn **Lưu** rồi **Nộp** để hợp đồng có hiệu lực.
OL	Trong quá trình sử dụng, cột **SL đã bán** và **SL còn lại** tự cập nhật theo các đơn hàng đã đặt — không sửa tay.
IMG	Hợp đồng khung bán với bảng danh mục, đơn giá và cột SL còn lại.
NOTE	Hệ thống kiểm tra hiệu lực **theo ngày**, không tin vào trạng thái hiển thị. Hợp đồng hết ngày hiệu lực sẽ bị chặn đặt đơn ngay cả khi trạng thái chưa kịp cập nhật.
H4	3.7.3.3	Tạo & duyệt Đơn hàng bán
OL	Bấm thẻ **Đơn hàng bán** rồi **Tạo mới**. Chọn **Khách hàng** và **Ngày đặt hàng**.
OL	Chọn **HĐ khung bán**. Ô chọn hợp đồng chỉ hiện hợp đồng của đúng khách đã chọn; khi chọn xong, hệ thống **tự nạp danh mục vật tư** kèm đơn giá hợp đồng và SL còn lại.
OL	Nhập **SL đặt** cho từng dòng. Ô chọn vật tư chỉ cho chọn trong danh mục hợp đồng. Có thể xóa các dòng khách không đặt.
OL	Nhấn **Lưu**. Hệ thống ghi đè lại đơn giá theo hợp đồng, tính tổng tiền, và kiểm tra: số lượng không vượt SL trần hợp đồng, tồn kho khả dụng đủ, và công nợ khách không vượt hạn mức tín dụng.
OL	Nhấn **Duyệt** để chuyển đơn sang trạng thái **Đã duyệt** — từ đây thủ kho mới lập được Phiếu giao hàng.
IMG	Đơn hàng bán với hợp đồng khung đã chọn và bảng chi tiết tự nạp.
WARN	Nếu khách vượt hạn mức tín dụng, đơn bị đặt cờ **Giữ do công nợ (credit hold)** và không duyệt được. Phải thu bớt công nợ hoặc nâng hạn mức trên hồ sơ khách trước.
H4	3.7.3.4	Soạn hàng & quét xác nhận (Thủ kho)
FIRST	Đây là bước bảo đảm hàng giao đúng lô, đúng số lượng. Từ đơn đã duyệt, hệ thống tạo một Phiếu giao hàng **nháp** với lô do FEFO gợi ý; thủ kho ra kho lấy hàng thật rồi quét xác nhận từng dòng. Chỉ khi quét đủ mọi dòng mới nộp được phiếu và trừ tồn kho.
OL	Mở Đơn hàng bán ở trạng thái **Đã duyệt**, bấm **Tạo phiếu giao (soạn hàng)**. Hệ thống tạo Phiếu giao hàng nháp và chuyển đơn sang **Đang xử lý** (nút Tạo phiếu giao (soạn hàng) ẩn đi để tránh tạo trùng).
OL	Trên phiếu giao nháp, xem bảng **Hướng dẫn lấy hàng**: mỗi dòng hiển thị lô nên lấy (hạn dùng gần nhất), vị trí và số lượng.
OL	Ra kho lấy hàng. Với từng dòng, quét **mã vạch lô** trên thùng/hộp; quét thêm **mã vị trí (bin)** nếu kho có khai vị trí; nhập **SL thực lấy** nếu khác số gợi ý.
OL	Hệ thống kiểm tra ngay tại máy chủ: lô đúng vật tư, còn hạn, đã đạt QC, không bị khóa, đủ tồn tại kho xuất, và vị trí thuộc đúng kho. Đạt thì dòng được đánh dấu **Đã quét xác nhận** và hiện số dòng còn lại.
OL	Khi mọi dòng đã quét, nhấn **Nộp**. Hệ thống trừ tồn kho theo đúng lô đã quét, ghi vào Sổ kho, và chuyển đơn hàng sang **Đã bàn giao**.
IMG	Màn hình soạn hàng với ô quét lô, ô quét vị trí và tiến độ số dòng đã xác nhận.
NOTE	**Được phép lấy lô khác lô gợi ý.** Thực tế kho không phải lúc nào cũng khớp gợi ý FEFO (hàng nằm sâu, thùng vỡ, lô lẻ). Cứ quét lô thực lấy — hệ thống kiểm tra và ghi nhận đúng lô đó, nên truy xuất nguồn gốc sau này vẫn chính xác.
NOTE	Máy quét cầm tay (PDA) hoạt động như bàn phím: quét xong nó gõ mã vào ô đang chọn rồi Enter. Vì vậy dùng được ngay trên trình duyệt của máy PDA, không cần cài ứng dụng riêng.
WARN	Nếu bỏ phiếu giao nháp: **Xóa** phiếu để đơn hàng tự quay lại **Đã duyệt** và hiện lại nút Tạo phiếu giao (soạn hàng). Đừng để phiếu nháp treo — đơn sẽ kẹt ở Đang xử lý.
H4	3.7.3.5	Lập Biên bản nghiệm thu
OL	Sau khi giao hàng, mở Phiếu giao hàng đã nộp và bấm tạo **Biên bản nghiệm thu**; hoặc để khách tự xác nhận trên Cổng khách hàng (xem 3.12).
OL	Điền **Ngày nghiệm thu**, **Người nghiệm thu** (đại diện bên khách) và ghi chú nếu có.
OL	Nhấn **Lưu** rồi **Nộp**. Phiếu giao chuyển sang **Đã nghiệm thu** — mở khóa bước lập hóa đơn.
IMG	Biên bản nghiệm thu gắn với phiếu giao hàng.
H4	3.7.3.6	Xuất Hóa đơn bán & Thu tiền (Kế toán)
OL	Mở Phiếu giao hàng đã nghiệm thu, bấm tạo **Hóa đơn bán**. Hệ thống chép nguyên vật tư và số lượng từ phiếu giao — không sửa được cho khác.
OL	Kiểm tra **Thuế suất**, **Tiền thuế** và **Tổng tiền**, rồi **Nộp**. Hệ thống ghi bút toán: Nợ 131 Phải thu / Có 511 Doanh thu và Có 3331 Thuế; đồng thời ghi giá vốn Nợ 632 / Có 156.
OL	In hóa đơn theo mẫu TT99 (có số tiền bằng chữ và thông tin bên bán lấy từ Cấu hình hệ thống).
OL	Khi khách trả tiền, mở hóa đơn và bấm **Thu tiền**: nhập **Số tiền** và **Hình thức** (Tiền mặt / Chuyển khoản), rồi nộp. Hệ thống ghi Nợ tiền / Có 131 và cập nhật **Còn phải thu** trên hóa đơn.
IMG	Hóa đơn bán với khối thuế, tổng tiền và số còn phải thu.
WARN	Không thu tiền được trên hóa đơn **chưa nộp** — làm vậy sẽ tạo công nợ phải thu âm. Nộp hóa đơn trước rồi mới thu.
H3	3.7.4	Trạng thái & phê duyệt
FIRST	Mỗi loại chứng từ có vòng đời riêng; trạng thái do hệ thống đặt theo thao tác, người dùng không sửa tay.
TABLE	Chứng từ|Vòng đời trạng thái|Chốt quan trọng
ROW	HĐ khung bán|Nháp - Chờ duyệt - Hiệu lực - Hết hạn / Thanh lý|Hết hiệu lực theo NGÀY thì chặn đặt đơn
ROW	Đơn hàng bán|Chờ duyệt - Đã duyệt - Đang xử lý - Đã bàn giao - Hoàn tất / Từ chối|Đang xử lý = đang có phiếu giao nháp
ROW	Phiếu giao hàng|Nháp (soạn hàng) - Đã giao - Đã nghiệm thu - Đã xuất HĐ|Chỉ nộp được khi quét đủ mọi dòng
ROW	Biên bản nghiệm thu|Nháp - Đã nghiệm thu|Mở khóa lập hóa đơn
ROW	Hóa đơn bán|Nháp - Đã phát hành - Thu một phần - Thu đủ - Hủy|Phải khớp đúng phiếu giao
ROW	Phiếu thu|Nháp - Đã nộp|Cập nhật Còn phải thu trên hóa đơn
BODY	**Bốn cột mốc khách nhìn thấy** trên Cổng khách hàng: (1) Đã đặt hàng, (2) Đã bàn giao và nghiệm thu, (3) Đã cấp hóa đơn, (4) Đã thu tiền. Mốc (2) và (3) kèm liên kết tải chứng từ. Đơn bị Từ chối thì chuỗi mốc dừng lại.
H3	3.7.5	Kết quả & truy vết
UL	Đơn hàng bán tạo bản ghi mã **SC-SO-…**; phiếu giao **SC-DN-…**; nghiệm thu **SC-AR-…**; hóa đơn **SC-SI-…**; phiếu thu **SC-SR-…**.
UL	Khi nộp Phiếu giao hàng: ghi vào **Sổ kho (Stock Ledger)** làm giảm tồn theo đúng từng lô đã quét, kèm kho và vị trí.
UL	Khi nộp Hóa đơn bán và Phiếu thu: ghi vào **Sổ cái (GL Entry)** — công nợ phải thu, doanh thu, thuế và giá vốn.
UL	Mỗi phiếu có khối **Chứng từ liên quan** cho xem cả chuỗi hai chiều: Khách hàng, HĐ khung, Đơn hàng, Phiếu giao (kèm **các lô đã giao** và số lô nhà cung cấp), Nghiệm thu, Hóa đơn, Phiếu thu.
UL	Truy xuất lô (mục 3.10) dựng lại được lô này đã bán cho **khách nào**, phục vụ thu hồi khi cần.
UL	Hạn mức hợp đồng khung tự trừ theo từng đơn; Dashboard có nhóm chỉ số **công nợ phải thu**.
H3	3.7.6	Lỗi thường gặp & mẹo
UL	**BRU-SFC-001 — Hợp đồng khung hết hiệu lực:** gia hạn hợp đồng hoặc lập hợp đồng kỳ mới trước khi nhận đơn.
UL	**BRU-SFC-002 — Không sửa được đơn giá:** giá khóa theo hợp đồng khung; muốn đổi giá phải sửa hợp đồng, không sửa trên đơn hay hóa đơn.
UL	**BRU-SO-001 — Vượt SL trần hợp đồng:** giảm số lượng đặt, hoặc bổ sung SL vào hợp đồng khung. Hệ thống cộng dồn mọi đơn đã đặt nên số còn lại có thể ít hơn bạn tưởng.
UL	**BRU-INV-002 — Tồn khả dụng không đủ:** nhập thêm hàng, hoặc giảm số lượng. Tồn khả dụng đã trừ các lô đang chờ QC, bị từ chối và lô bị khóa.
UL	**BRU-AR-001 — Vượt hạn mức tín dụng:** thu bớt công nợ hoặc nâng hạn mức trên hồ sơ khách rồi duyệt lại.
UL	**BRU-SO-002 — Đơn chưa được duyệt:** duyệt đơn trước khi tạo phiếu giao.
UL	**SC-E-DN-NOT-SCANNED — Còn dòng chưa quét:** thông báo nêu rõ còn bao nhiêu dòng và vật tư nào; quét nốt rồi nộp lại.
UL	**SC-E-PICK-ITEM — Lô quét thuộc vật tư khác:** bạn đang cầm nhầm hàng; kiểm tra lại thùng.
UL	**SC-E-PICK-EXPIRED / SC-E-PICK-QC / SC-E-PICK-BLOCKED — Lô hết hạn, chưa đạt QC, hoặc bị khóa:** không lấy lô này; chọn lô khác theo hướng dẫn lấy hàng.
UL	**SC-E-PICK-STOCK — Lô không đủ tồn:** lấy thêm từ lô khác cho đủ số, hoặc báo lại để điều chỉnh đơn.
UL	**SC-E-PICK-BIN-WH — Vị trí thuộc kho khác:** bạn đang quét ở sai kho; kiểm tra lại kho xuất trên phiếu.
UL	**SC-E-DN-CANCEL-REASON — Thiếu lý do hủy:** hủy phiếu giao bắt buộc ghi lý do; lý do được lưu vào phiếu để đối chiếu về sau.
UL	**BRU-DEL-001 — Chưa nghiệm thu:** lập Biên bản nghiệm thu trước, rồi mới xuất hóa đơn.
UL	**BRU-INVC-001 — Hóa đơn lệch phiếu giao:** vật tư, số lượng và khách trên hóa đơn phải khớp chính xác phiếu giao; đừng thêm hoặc bớt dòng.
UL	**Mẹo —** khi khách gọi đặt hàng, chọn hợp đồng khung trước rồi mới nhập số lượng: danh mục và giá tự nạp, đỡ gõ và không sai giá.
UL	**Mẹo —** hủy phiếu giao đã nộp sẽ hoàn tồn kho về đúng lô cũ; không cần nhập kho tay.
H3	3.7.7	Liên quan
UL	Xem 3.5 — M5 Lô vật tư & FEFO (cách hệ thống gợi ý lô cận hạn xuất trước).
UL	Xem 3.3 — M3 Tiếp nhận & Kiểm tra chất lượng (lô chưa đạt QC không được giao cho khách).
UL	Xem 3.8 — M8 Kế toán (bút toán doanh thu, giá vốn, công nợ phải thu).
UL	Xem 3.10 — M10 Truy xuất & Thu hồi (truy lô đã bán tới từng khách).
UL	Xem 3.12 — M12 Cổng khách hàng (khách tự đặt hàng và tự nghiệm thu).
UL	Xem Chương 2 — khai báo Khách hàng, Vật tư (đơn vị kép, giá bán), Kho.
