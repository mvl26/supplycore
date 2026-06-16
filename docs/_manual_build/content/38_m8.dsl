# SupplyCore — Hướng dẫn sử dụng | Mục 3.8 — M8 Kế toán
# DSL (mỗi block 1 dòng, phân tách bằng TAB). Sinh từ code thật M8 Accounting.
H2	3.8	M8 · Kế toán
H3	3.8.1	Mục đích & khi nào dùng
FIRST	Module Kế toán (M8) là nơi xử lý phần tiền của chuỗi mua sắm: ghi nhận **Hóa đơn mua** (Purchase Invoice) do nhà cung cấp xuất, đối chiếu 3 bên giữa Đơn mua (PO) — Phiếu nhập (PR) — Hóa đơn (PI), lập **Phiếu thanh toán** (Payment Entry) chi tiền cho nhà cung cấp, và tự động sinh **Bút toán sổ cái** (GL Entry). Module cũng cung cấp màn hình **Báo cáo tài chính** với 4 báo cáo: giá trị tồn kho, công nợ nhà cung cấp, chi phí vật tư theo kỳ và quyết toán BHYT.
BODY	Bạn dùng M8 khi: đã có hàng về kho (đã nộp Phiếu nhập ở M3) và nhận được hóa đơn giấy của nhà cung cấp; khi đến hạn trả tiền cho nhà cung cấp; hoặc khi cần xem số liệu công nợ, chi phí, giá trị tồn để báo cáo và quyết toán.
H3	3.8.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Kế toán (SupplyCore Accountant) tạo và nộp Hóa đơn mua, lập Phiếu thanh toán, xem báo cáo. Trưởng phòng Vật tư (SupplyCore Manager) duyệt hóa đơn/thanh toán dưới ngưỡng; Lãnh đạo (SupplyCore Executive) duyệt khi giá trị từ 50 triệu trở lên hoặc khi đối chiếu 3 bên lệch. Thủ kho và Kiểm toán chỉ được xem (read/report).
BODY	**Cần có trước:** Phiếu nhập (PR) đã nộp và không bị QC từ chối (xem 3.3); Đơn mua (PO) đã nộp nếu muốn đối chiếu 3 bên (xem 3.2); Nhà cung cấp đã khai báo trong Dữ liệu nền; hóa đơn giấy của nhà cung cấp (số hóa đơn, ngày, tổng tiền). Để bút toán ghi được sổ cái cần khai báo trước các Tài khoản kế toán (SC GL Account): 152, 1331, 331, 1121, 1111.
H3	3.8.3	Các bước thực hiện
H4	3.8.3.1	Tạo Hóa đơn mua từ Phiếu nhập
BODY	Cách nhanh nhất là tạo hóa đơn từ một Phiếu nhập (PR) đã nộp: hệ thống tự sao chép nhà cung cấp, đơn mua, các dòng vật tư (mã, số lượng, đơn vị, đơn giá, kho nhập, lô) sang hóa đơn nháp.
OL	Mở Phiếu nhập (PR) đã nộp và không bị QC từ chối, chọn chức năng tạo Hóa đơn mua. Hệ thống tạo một **SC Purchase Invoice** ở trạng thái nháp, mã dạng **SC-PI-2026-00001**.
OL	Mở hóa đơn nháp vừa tạo. Sửa lại **Số HĐ NCC** đúng theo hóa đơn giấy (mặc định hệ thống điền tạm dạng AUTO-…), kiểm tra **Ngày HĐ** và **Ngày đến hạn** (mặc định +30 ngày).
OL	Đối chiếu các dòng trong bảng **Items**: mã vật tư, số lượng, đơn giá. Sửa đơn giá nếu hóa đơn khác với phiếu nhập. **Thành tiền**, **Tổng trước thuế**, **Tiền VAT** (mặc định **VAT (%)** = 10) và **Tổng cộng** được tính tự động.
OL	Nhấn **Lưu**. Khi lưu, hệ thống tự chạy đối chiếu 3 bên và tính lại **Còn phải trả** = Tổng cộng − Đã thanh toán.
OL	Khi số liệu đã đúng, nhấn **Nộp** để ghi sổ. Hóa đơn chuyển sang trạng thái đã duyệt (Approved) và sinh bút toán sổ cái.
IMG	Màn hình Hóa đơn mua nháp với bảng Items, khối Tổng và khối 3-Way Match.
NOTE	Bạn cũng có thể tạo hóa đơn thủ công từ Trang module **M8** → thẻ **SC Purchase Invoice** → **Tạo mới**, rồi chọn nhà cung cấp và thêm dòng vật tư bằng tay. Khi đó nên chọn **Purchase Order** và **Purchase Receipt** để hệ thống đối chiếu được 3 bên.
H4	3.8.3.2	Đối chiếu 3 bên (3-way match)
BODY	Khi hóa đơn có liên kết **Purchase Order**, hệ thống tự so sánh **Tổng trước thuế** của hóa đơn với Tổng của Đơn mua (PO) và tổng giá trị các Phiếu nhập (PR) đã nộp của đơn đó. Sai số cho phép là ±1%.
OL	Mở hóa đơn và nhìn khối **3-Way Match**. Trường **Trạng thái 3-way** cho biết kết quả, **Sai lệch (VND)** cho biết chênh lệch lớn nhất so với PO hoặc PR.
OL	Nếu chênh lệch trong ±1% → trạng thái **Match** (khớp): không cần giải trình, có thể nộp ngay.
OL	Nếu chênh lệch vượt ±1% → trạng thái **Mismatch** (lệch): hệ thống hiện cảnh báo, tự bật **Tạm hold thanh toán** và yêu cầu nhập **Giải trình chênh lệch** trước khi nộp (xem 3.8.3.3).
OL	Nếu hóa đơn không gắn Đơn mua → trạng thái **Not Applicable** (không áp dụng), bỏ qua đối chiếu.
WARN	Có một ngưỡng chặn cứng: nếu **Tổng trước thuế** của hóa đơn vượt Đơn mua quá 5%, hệ thống chặn ngay khi lưu/nộp với lỗi **SC-E009 THREE_WAY_MISMATCH**. Phải sửa lại đơn giá/số lượng hoặc điều chỉnh Đơn mua trước.
H4	3.8.3.3	Xử lý chênh lệch & giải trình
BODY	Khi đối chiếu cho kết quả **Mismatch**, hóa đơn bị giữ thanh toán cho tới khi được giải trình và duyệt ở cấp phù hợp. Trường **Cấp duyệt yêu cầu** sẽ tự đặt thành **Executive** (Lãnh đạo) khi lệch, hoặc khi Tổng cộng từ 50 triệu trở lên.
OL	Trong khối 3-Way Match, nhập rõ lý do chênh lệch vào ô **Giải trình chênh lệch** (ví dụ: nhận thiếu, đơn giá điều chỉnh, phụ phí vận chuyển…).
OL	Trình hóa đơn lên Lãnh đạo (Executive) duyệt theo **Cấp duyệt yêu cầu**. Người có vai trò phù hợp nhấn **Nộp** để ghi sổ.
OL	Sau khi nộp, trường **Người duyệt** và **Thời điểm duyệt** được ghi tự động.
WARN	Nếu nhấn **Nộp** mà chưa nhập **Giải trình chênh lệch** khi trạng thái là Mismatch/Force Approved, hệ thống chặn với lỗi **SC-E-PI-MISMATCH-EXPLANATION**.
NOTE	Cờ **Tạm hold thanh toán** chỉ tự gỡ khi đối chiếu trở về Match. Trong khi cờ này còn bật, hóa đơn sẽ không xuất hiện trong danh sách hóa đơn cần trả khi lập Phiếu thanh toán (xem 3.8.3.5).
H4	3.8.3.4	Debit Note / Credit Note (hàng trả nhà cung cấp)
BODY	Khi trả hàng cho nhà cung cấp (từ Phiếu nhập trả ở M3), dùng cờ trên hóa đơn để giảm hoặc hoàn công nợ.
OL	Tạo hóa đơn và đánh dấu **Debit Note (UC-11)** để giảm công nợ phải trả, hoặc **Credit Note (UC-11 refund)** khi nhà cung cấp hoàn tiền.
OL	Chọn **Return PR (UC-11)** trỏ tới Phiếu nhập trả tương ứng (ô này chỉ hiện khi đã tích Debit/Credit Note).
OL	Nhập các dòng và nộp như hóa đơn thường.
NOTE	Quy tắc Tổng cộng phải lớn hơn 0 (lỗi **SC-E015**) được nới cho phiếu trả: nếu là phiếu trả/Credit Note thì không bị chặn bởi quy tắc này.
H4	3.8.3.5	Tạo Phiếu thanh toán (Payment Entry)
BODY	Phiếu thanh toán (SC Payment Entry, mã **SC-PE-2026-00001**) dùng để chi tiền cho nhà cung cấp và phân bổ số tiền vào từng hóa đơn còn nợ.
OL	Từ Trang module **M8** → thẻ **SC Payment Entry** → **Tạo mới**. Chọn **NCC** (nhà cung cấp).
OL	Hệ thống có thể tự nạp các hóa đơn còn nợ của nhà cung cấp (sắp theo ngày đến hạn, tự loại các hóa đơn đang bị hold). Trong bảng **Invoices**, mỗi dòng gồm **PI**, **Tổng HĐ**, **Còn trước TT**, ô **Phân bổ** và **Còn sau TT**.
OL	Nhập số tiền cần trả cho từng hóa đơn vào ô **Phân bổ**. **Tổng phân bổ** phải bằng **Số tiền** của phiếu.
OL	Điền **Ngày thanh toán**, **Phương thức** (Bank Transfer / Cash / Check / Credit Card / Other), **Tài khoản ngân hàng** (khi chuyển khoản), **Số chứng từ NH** và **Ngày chứng từ**.
OL	Nếu chỉ trả một phần hóa đơn, ghi rõ lý do vào **Lý do thanh toán partial**.
OL	Nhấn **Lưu** rồi **Nộp**. Hệ thống ghi bút toán chi tiền và cập nhật lại công nợ các hóa đơn liên quan.
IMG	Màn hình Phiếu thanh toán với bảng Invoices phân bổ theo từng hóa đơn.
BODY	**Cấp duyệt** được tính tự động theo **Số tiền**: dưới 50 triệu cần vai trò Manager; từ 50 triệu trở lên cần vai trò Executive. Hệ thống kiểm tra vai trò người nộp ngay tại bước **Nộp**.
WARN	Không thể phân bổ vào hóa đơn đang bị **Tạm hold thanh toán** (lỗi **SC-E-PE-PAYMENT-HOLD**), cũng không thể phân bổ vượt quá số còn phải trả của hóa đơn. Nếu số dư tài khoản ngân hàng thấp hơn số tiền chi, hệ thống chỉ cảnh báo (màu cam) chứ không chặn nộp.
H4	3.8.3.6	Xem Báo cáo tài chính
BODY	Mở màn hình **Báo cáo tài chính M8** tại đường dẫn **/financial-reports**. Màn hình có 4 thẻ (tab). Với mỗi thẻ: chọn bộ lọc → nhấn **Chạy báo cáo** → xem kết quả → nhấn **Xuất CSV** để tải dữ liệu.
OL	Thẻ **Tồn kho — giá trị**: lọc theo **Kho**, **Nhóm vật tư**, **Tại ngày**. Kết quả gồm thẻ tổng (Số dòng, Tổng SL, Giá trị tồn) và bảng chi tiết theo từng vật tư/kho/lô; bấm vào dòng để mở vật tư.
OL	Thẻ **Công nợ NCC (Aging)**: lọc theo **Nhà cung cấp**, **Tại ngày**. Công nợ được chia nhóm tuổi nợ: Chưa đến hạn, 0–30, 31–60, 61–90, > 90 ngày. Bấm mã PI trong bảng để xem nhanh chi tiết chứng từ.
OL	Thẻ **Chi phí vật tư kỳ**: bắt buộc nhập **Từ ngày** và **Đến ngày**; lọc thêm theo **Nhóm vật tư**, **Kho**. Kết quả là tổng chi phí trong kỳ và phân tích theo nhóm vật tư.
OL	Thẻ **Quyết toán BHYT**: bắt buộc nhập **Từ ngày** và **Đến ngày**; lọc thêm **Khoa phòng**, **Nhóm BHYT (N01-N09)**. Kết quả gồm các thẻ tổng (Tổng chi phí, BHYT chi trả, BN tự trả, Vượt trần) và bảng theo nhóm BHYT × khoa.
IMG	Màn hình Báo cáo tài chính với 4 thẻ và bộ lọc theo kỳ.
NOTE	Nếu trong kỳ vẫn còn chứng từ ở trạng thái nháp (hóa đơn, thanh toán, cấp phát), báo cáo hiển thị dải vàng **Kỳ chưa khóa sổ** kèm số lượng chứng từ nháp còn lại — số liệu lúc này là tạm thời và có thể thay đổi.
H3	3.8.4	Trạng thái & phê duyệt
BODY	Hóa đơn mua (SC Purchase Invoice) đi qua các trạng thái sau:
TABLE	Trạng thái|Ý nghĩa|Ai duyệt
ROW	Draft (Nháp)|Đang soạn, chưa ghi sổ|Kế toán
ROW	Pending Approval (Chờ duyệt)|Đã trình, chờ phê duyệt|Manager / Executive
ROW	Approved (Đã duyệt)|Đã nộp, đã ghi sổ cái + công nợ|Tự động khi nộp
ROW	Partly Paid (Trả một phần)|Đã thanh toán một phần|—
ROW	Paid (Đã trả)|Đã thanh toán đủ|—
ROW	Overdue (Quá hạn)|Quá ngày đến hạn mà chưa trả đủ|—
ROW	Cancelled (Đã hủy)|Đã hủy, bút toán bị đảo|Kế toán / Manager
BODY	Phiếu thanh toán (SC Payment Entry) có các trạng thái: **Draft** (nháp), **Pending Approval** (chờ duyệt), **Approved** (đã duyệt/đã chi), **Cleared** (đã đối soát NH), **Cancelled** (đã hủy).
BODY	**Cấp duyệt yêu cầu / Cấp duyệt:** Auto khi đối chiếu khớp và dưới ngưỡng (kế toán tự nộp); Manager khi dưới 50 triệu; Executive khi từ 50 triệu trở lên hoặc khi đối chiếu 3 bên lệch.
H3	3.8.5	Kết quả & truy vết
UL	Hóa đơn mua: tạo bản ghi mã **SC-PI-YYYY-#####**, cập nhật **Còn phải trả** và làm tăng công nợ phải trả nhà cung cấp.
UL	Khi nộp hóa đơn: sinh **Bút toán sổ cái** (SC GL Entry, mã **SC-GL-YYYY-########**) theo định khoản Nợ 152 (hàng tồn kho) + Nợ 1331 (thuế GTGT được khấu trừ, nếu có VAT) / Có 331 (phải trả nhà cung cấp).
UL	Phiếu thanh toán: tạo bản ghi mã **SC-PE-YYYY-#####**, sinh bút toán Nợ 331 / Có 1121 (chuyển khoản) hoặc 1111 (tiền mặt), và cập nhật hóa đơn về **Partly Paid** hoặc **Paid**.
UL	Bút toán sổ cái là **chỉ đọc**, sinh tự động từ hóa đơn/thanh toán; khi hủy chứng từ gốc, bút toán bị đánh dấu Cancelled (đảo sổ) chứ không xóa.
UL	Các báo cáo ở /financial-reports tổng hợp số liệu từ Sổ kho (SLE), Hóa đơn, Thanh toán và Phiếu cấp phát BHYT; có cờ "Kỳ chưa khóa sổ" để cảnh báo số liệu tạm thời.
H3	3.8.6	Lỗi thường gặp & mẹo
UL	**SC-E-PI-DUPLICATE — Trùng số hóa đơn NCC:** một nhà cung cấp không được có 2 hóa đơn cùng **Số HĐ NCC**. Kiểm tra lại số hóa đơn giấy hoặc tìm hóa đơn đã nhập trước đó.
UL	**SC-E007 PI_DUPLICATE — Đã có hóa đơn cho phiếu nhập này:** mỗi Phiếu nhập chỉ tạo được một hóa đơn; mở hóa đơn đã có thay vì tạo mới.
UL	**SC-E015 ZERO_INVOICE_TOTAL — Tổng cộng phải lớn hơn 0:** kiểm tra lại các dòng vật tư và đơn giá; nếu là Credit Note thì đánh dấu phiếu trả.
UL	**SC-E009 THREE_WAY_MISMATCH — Vượt Đơn mua quá 5%:** sửa đơn giá/số lượng hoặc điều chỉnh Đơn mua; ngưỡng này chặn cứng, không nộp được.
UL	**SC-E-PI-MISMATCH-EXPLANATION — Thiếu giải trình:** nhập **Giải trình chênh lệch** trước khi nộp hóa đơn lệch.
UL	**SC-E-PE-PAYMENT-HOLD — Hóa đơn đang bị hold:** giải trình và đưa đối chiếu về Match để gỡ hold trước khi thanh toán.
UL	**SC-E-PE-EXECUTIVE-REQUIRED / SC-E-PE-MANAGER-REQUIRED — Sai cấp duyệt:** phiếu từ 50 triệu cần Lãnh đạo nộp, dưới 50 triệu cần Trưởng phòng; nhờ đúng người có vai trò nộp.
UL	**Mẹo —** tạo hóa đơn từ Phiếu nhập để tự sao chép dòng vật tư, kho và lô, giảm nhập tay và sai sót đối chiếu.
UL	**Mẹo —** khi đối chiếu lệch nhẹ, xem **Sai lệch (VND)** để biết chênh đúng bao nhiêu trước khi quyết định giải trình hay sửa đơn giá.
UL	**Mẹo —** dùng thẻ **Công nợ NCC (Aging)** đầu kỳ để biết hóa đơn nào sắp/đã quá hạn, ưu tiên lập Phiếu thanh toán cho nhóm > 90 ngày.
H3	3.8.7	Liên quan
UL	Xem 3.2 — Mua sắm (Đơn mua / PO làm cơ sở đối chiếu 3 bên).
UL	Xem 3.3 — Tiếp nhận & Kiểm tra chất lượng (Phiếu nhập / PR là nguồn tạo hóa đơn).
UL	Xem 3.7 — Cấp phát & BHYT (số liệu cho báo cáo Quyết toán BHYT).
