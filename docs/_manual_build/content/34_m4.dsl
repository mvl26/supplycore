H2	3.4	M4 · Quản lý kho
H3	3.4.1	Mục đích & khi nào dùng
FIRST	Module M4 (WMS — Quản lý kho) giúp Thủ kho biết chính xác hàng nào, lô nào, còn bao nhiêu và đang nằm ở đâu trong kho — theo thời gian thực. Bạn dùng module này hằng ngày để: tra cứu tồn kho và giá trị tồn, xem nhanh tổng quan các kho, khai báo vị trí lưu trữ (bin), xếp hàng vừa nhận lên kệ, và xem bản đồ chỉ đường tới đúng kho / đúng vị trí lấy hàng.
BODY	Khác với module nhập–xuất (tạo phiếu làm thay đổi tồn), M4 chủ yếu là lớp "tổ chức không gian kho": nó không tự cộng/trừ tồn, mà gắn mỗi lượng tồn vào một vị trí cụ thể (bin) và trình bày dữ liệu tồn cho dễ tra cứu. Số liệu tồn được tính trực tiếp từ Sổ kho (Stock Ledger) nên luôn khớp với phiếu nhập–xuất–chuyển.
BODY	Bạn vào M4 khi: cần kiểm tra còn bao nhiêu một vật tư trước khi cấp phát; vừa nhận hàng từ phiếu nhập (PR) và cần xếp lên kệ; muốn thiết lập sơ đồ kho lần đầu; hoặc cần chỉ đường cho nhân viên mới tới đúng kho/đúng kệ.
H3	3.4.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Thủ kho (SupplyCore Storekeeper / Warehouse Officer) là người dùng chính — xem tồn, khai báo bin, đặt quy tắc xếp hàng, xếp hàng lên kệ. Trưởng phòng Vật tư và Quản trị Hệ thống có toàn quyền. Điều dưỡng/NV Khoa và Kiểm soát Chất lượng chỉ xem (read-only) tồn kho và vị trí. Riêng màn hình **Thiết kế bản đồ** (`/map-editor`) chỉ Quản trị Hệ thống hoặc Trưởng phòng Vật tư mới lưu được.
BODY	**Cần có trước:** Kho (SC Warehouse) đã khai báo theo cây 3 cấp (kho tổng → kho con → kho khoa phòng) trong Dữ liệu nền; Vật tư (SC Item) và Lô (SC Batch) đã tồn tại; đã có phát sinh nhập kho (Sổ kho có dòng) thì tồn kho mới hiển thị. Để xếp hàng lên kệ cần có ít nhất một Vị trí lưu trữ (Bin Location) thuộc kho đó.
NOTE	Tồn kho trong M4 đọc từ Sổ kho (SC Stock Ledger Entry). Nếu một kho chưa có phát sinh nào thì sẽ hiện "Không có tồn kho khớp với bộ lọc" — đó là bình thường, không phải lỗi.
H3	3.4.3	Các bước thực hiện
H4	3.4.3.1	Xem tồn kho thời gian thực (Tồn kho — /stock-balance)
FIRST	Màn hình **Tồn kho hiện tại** (`/stock-balance`) là nơi tra cứu nhanh nhất: ai còn quyền xem đều mở được từ thanh bên trái.
OL	Mở **Tồn kho** từ Sidebar (hoặc vào thẳng `/stock-balance`).
OL	Dùng bộ lọc phía trên: **Vật tư** (chọn từ danh sách), **Kho** (chọn từ danh sách), **Lô** (gõ mã lô rồi nhấn Enter). Để trống = xem tất cả.
OL	Đọc 4 thẻ tổng hợp (KPI) ở đầu trang: **Tổng số lượng tồn**, **Tổng giá trị** (VND), **Số vật tư**, **Số lô** — các thẻ này tính theo kết quả đang lọc.
OL	Xem bảng chi tiết: **Mã VT**, **Tên**, **Kho**, **Lô**, **KCS**, **HD** (hạn dùng), **SL tồn**, **Giá trị (VND)**. Bấm tiêu đề cột để sắp xếp tăng/giảm.
OL	Bấm vào **Mã VT** để mở chi tiết vật tư, hoặc bấm **Lô** để mở chi tiết lô (truy vết).
OL	Bấm **Tải lại** để cập nhật lại số liệu mới nhất.
IMG	Màn hình Tồn kho hiện tại với 4 thẻ KPI và bảng tồn theo vật tư/kho/lô.
BODY	**Tô màu cảnh báo:** dòng có lô **đã hết hạn** được tô nền đỏ; dòng có lô **sắp hết hạn** (còn dưới 30 ngày) được tô nền vàng và ngày HD in màu cam. Cột **KCS** hiển thị trạng thái kiểm tra chất lượng của lô: **Đạt** (xanh), **Không đạt** (đỏ), **Có điều kiện** (vàng); lô bị khoá có thêm nhãn **Khoá**.
NOTE	Mẹo: Từ màn hình Danh sách kho, bấm **Chi tiết** ở mỗi dòng sẽ mở thẳng Tồn kho đã lọc sẵn theo kho đó (`/stock-balance?warehouse=...`).
H4	3.4.3.2	Xem danh sách kho (Kho — /warehouses)
FIRST	Màn hình **Kho — Tồn kho hiện tại** (`/warehouses`) cho cái nhìn tổng quan từng kho: tổng số lượng, số loại vật tư và tổng giá trị tồn.
OL	Mở **Kho** từ Sidebar (`/warehouses`).
OL	Dùng ô tìm theo tên kho, bộ lọc **loại kho**, và menu sắp xếp (Tên kho / SL tồn / Số items / Giá trị).
OL	Đọc bảng: **Tên kho**, **Loại**, **Tổng SL tồn**, **Số items**, **Giá trị tồn (VND)**; dòng **Tổng cộng** ở chân bảng cộng toàn bộ.
OL	Bấm **tên kho** để mở chi tiết kho; bấm **Chi tiết** để xem tồn kho của kho đó.
OL	Cần tạo kho mới, bấm **+ Tạo kho** (mở biểu mẫu SC Warehouse).
IMG	Danh sách kho với cột tổng số lượng, số items và giá trị tồn, dòng Tổng cộng.
H4	3.4.3.3	Khai báo vị trí lưu trữ (Vị trí lưu trữ — Bin Location)
FIRST	Vị trí lưu trữ (DocType **Bin Location**, mã tự sinh **SC-BIN-#####**) là ô/kệ vật lý trong một kho để gắn hàng vào đó. Khai báo bin giúp xếp hàng lên kệ và lấy hàng theo đúng vị trí.
OL	Từ Trang chủ mở **M4**, bấm thẻ **Bin Location** rồi **Tạo mới** (hoặc vào Danh sách `/list/Bin Location`).
OL	Nhập **Kho** (bắt buộc) và **Mã bin** (bắt buộc, duy nhất — ví dụ A-01-03 theo Zone-Aisle-Shelf), thêm **Mô tả ngắn** nếu cần.
OL	Khai vị trí vật lý ở mục "Vị trí vật lý": **Zone (khu)**, **Aisle (lối)**, **Rack (giá)**, **Shelf (kệ)**, **Level (tầng)**. Hai trường **Toạ độ hàng/cột (map)** dùng để vẽ vị trí trên sơ đồ kho.
OL	Khai **Sức chứa tối đa** và **Đơn vị sức chứa** (để trống hoặc 0 = không giới hạn). Nếu là kho lạnh, bật **Kiểm soát nhiệt độ** rồi nhập **Nhiệt độ min/max (°C)**.
OL	Bật/tắt **Đang sử dụng**; bật **Bin cách ly (QC Hold)** nếu đây là vị trí giữ hàng chờ QC (chưa được xuất).
OL	**Lưu**. Hệ thống tự sinh **Barcode bin** bằng mã bin (có thể đè bằng mã GS1 riêng); bạn có thể in nhãn barcode để dán lên kệ.
IMG	Biểu mẫu Bin Location với mã bin, vị trí vật lý, sức chứa và trạng thái.
BODY	**Tồn hiện tại**, **Tỷ lệ chiếm dụng (%)** và **Trạng thái** (Empty/In Use/Full) là các trường chỉ-đọc, hệ thống tự tính lại từ Sổ kho (nút tính lại / đồng bộ trên bin). Không sửa tay được các trường này.
WARN	Không xóa được bin đang còn hàng. Nếu cố xóa, hệ thống báo **SC-E-BIN-NOT-EMPTY** — phải chuyển hết hàng sang bin khác (qua phiếu chuyển/xuất) rồi mới xóa.
H4	3.4.3.4	Đặt quy tắc xếp hàng (Putaway Rule)
FIRST	Quy tắc xếp hàng (DocType **Putaway Rule**, mã tự sinh **PWR-#####**) giúp hệ thống gợi ý sẵn bin đích cho một vật tư hoặc một nhóm vật tư — đỡ phải chọn tay mỗi lần.
OL	Mở **M4** → thẻ **Putaway Rule** → **Tạo mới**.
OL	Chọn **Bin đích** (bắt buộc) — vị trí muốn xếp hàng vào.
OL	Khai tiêu chí khớp: nhập **Vật tư cụ thể** HOẶC **Nhóm vật tư** (phải có ít nhất một trong hai). Rule theo vật tư cụ thể ưu tiên hơn rule theo nhóm.
OL	Chọn **Kho áp dụng** (để trống = áp dụng mọi kho), đặt **Priority** (số càng cao chạy trước), bật **Đang sử dụng**.
OL	**Lưu**. Khi nhận hàng/xếp hàng, hệ thống dò rule theo thứ tự: rule vật tư+kho → bin mặc định của vật tư → rule nhóm+kho → rule nhóm toàn cục, và chỉ chọn bin còn đủ sức chứa.
WARN	Nếu lưu mà chưa nhập cả Vật tư lẫn Nhóm vật tư, hệ thống báo **SC-E-PUTAWAY-RULE** — phải nhập một trong hai.
H4	3.4.3.5	Xếp hàng lên kệ (Phiếu xếp hàng lên kệ — /putaway)
FIRST	Màn hình **Phiếu xếp hàng lên kệ** (`/putaway`) liệt kê các dòng hàng vừa nhận (từ phiếu nhập PR hoặc phiếu nhập kho SE) nhưng **chưa được gán vị trí**, để Thủ kho chọn bin và lưu hàng loạt.
OL	Mở **Phiếu xếp hàng** từ Sidebar (`/putaway`).
OL	(Tùy chọn) Lọc **theo kho** ở ô "Lọc theo kho", hoặc gõ vào "Tìm trong DS" theo mã chứng từ / mã VT / lô.
OL	Với mỗi dòng (Chứng từ, Ngày, Mã VT, Tên SP, Kho, Lô, HD, KCS, SL), ở cột **Chọn vị trí** chọn một bin thuộc đúng kho của dòng đó.
OL	Sau khi chọn xong các dòng, bấm **Lưu N dòng** (N = số dòng đã chọn). Hệ thống báo "Đã xếp N dòng lên kệ" và làm mới danh sách.
OL	Bấm **Tải lại** để lấy danh sách hàng chờ xếp mới nhất.
IMG	Phiếu xếp hàng lên kệ với danh sách hàng chờ xếp và dropdown Chọn vị trí từng dòng.
BODY	Thao tác này gán **vị trí lưu trữ** vào từng dòng Sổ kho đã có — không tạo phiếu nhập mới và không làm thay đổi số lượng tồn. Hệ thống kiểm tra bin được chọn phải cùng kho với dòng hàng.
NOTE	Nếu một dòng hiện "Kho chưa khai vị trí", nghĩa là kho đó chưa có Bin Location nào — hãy khai bin trước (mục 3.4.3.3). Khi không còn hàng chờ xếp, màn hình hiện "Không có hàng chờ xếp lên kệ".
H4	3.4.3.6	Xem bản đồ kho (Bản đồ kho — /warehouse-map)
FIRST	Màn hình **Bản đồ kho** (`/warehouse-map`) có 2 tab giúp định hướng trực quan: chỉ đường tới kho và tìm đúng vị trí lưu trữ bên trong kho.
OL	Mở **Bản đồ kho** từ Sidebar (`/warehouse-map`).
OL	Tab **Bản đồ khuôn viên**: xem sơ đồ khuôn viên bệnh viện với vị trí các kho. Chọn "Chỉ đường tới kho" để hệ thống vẽ tuyến từ cổng chính tới kho đó.
OL	Bấm vào một kho trên bản đồ khuôn viên để chuyển sang tab **Sơ đồ trong kho** của đúng kho đó.
OL	Tab **Sơ đồ trong kho**: chọn kho ở ô "Chọn kho" để xem lưới các vị trí lưu trữ (bin) bên trong; hệ thống có thể vẽ lối đi tới một bin đích.
OL	Bấm vào một ô bin để mở **chi tiết Vị trí lưu trữ** (Bin Location) tương ứng.
IMG	Bản đồ kho — tab Bản đồ khuôn viên với tuyến chỉ đường từ cổng tới kho.
NOTE	Chỉ những kho đã được đặt toạ độ trên bản đồ (qua màn hình Thiết kế bản đồ) mới hiển thị. Kho chưa gán toạ độ sẽ không xuất hiện trên sơ đồ.
H4	3.4.3.7	Thiết kế bản đồ kho (Thiết kế bản đồ — /map-editor)
FIRST	Màn hình **Thiết kế bản đồ** (`/map-editor`) dành cho quản trị: tùy chỉnh sơ đồ khuôn viên theo từng bệnh viện — đặt cổng, sắp xếp các kho lên lưới và lưu cấu hình. Đây là việc làm một lần khi triển khai, hoặc khi kho thay đổi bố trí.
OL	Mở **Thiết kế bản đồ** (`/map-editor`).
OL	Ở mục "Thông tin bệnh viện", nhập **Tên bệnh viện**, **Địa chỉ**, **Nhãn cổng**, và số **Hàng** × **Cột** của lưới bản đồ.
OL	Bấm **Đặt vị trí cổng** rồi click một ô trên lưới để đặt cổng chính.
OL	Click ô trống trên lưới → chọn một kho từ danh sách "Kho chưa đặt" để đưa vào ô; click ô đã có kho để đổi loại kho (Kho tổng / Kho con / Kho khoa / Cách ly / Trung chuyển) hoặc **Gỡ khỏi bản đồ**.
OL	Bấm **Lưu cấu hình** để ghi lại. Hệ thống báo số kho đã cập nhật (và số lỗi nếu trùng ô / thiếu toạ độ).
IMG	Màn hình Thiết kế bản đồ với lưới ô, danh sách Kho chưa đặt và nút Lưu cấu hình.
WARN	Chỉ Quản trị Hệ thống hoặc Trưởng phòng Vật tư mới lưu được bản đồ; người khác mở vào sẽ bị chặn quyền. Mỗi ô chỉ đặt được một kho — đặt trùng ô sẽ bị bỏ qua và báo lỗi khi lưu.
H4	3.4.3.8	Quét mã vạch / PDA khi xếp hàng (barcode)
FIRST	Hệ thống có sẵn các điểm kết nối (API) cho thiết bị quét mã vạch / ứng dụng PDA để hỗ trợ xếp hàng và tra cứu nhanh, dùng khi bệnh viện trang bị máy quét.
UL	**Quét mã** nhận dạng mã vạch thành Vật tư, Lô, hoặc Vị trí lưu trữ (theo barcode hoặc mã bin); nếu mã không nhận dạng được sẽ báo lỗi để quét lại.
UL	**Gợi ý bin** theo vật tư + kho (bin mặc định → quy tắc xếp hàng → bin trống đầu tiên), và **xác nhận xếp hàng** tạo phiếu nhập kho nháp gắn đúng bin/lô.
UL	Mỗi vị trí lưu trữ có **Barcode bin** (tự sinh từ mã bin) để in nhãn dán lên kệ, quét là ra ngay vị trí.
NOTE	Bệnh viện hiện tại chủ yếu thao tác trên web (nhập/chọn tay) như mục 3.4.3.5; phần quét mã vạch là tùy chọn, sẵn sàng khi có thiết bị PDA.
H3	3.4.4	Trạng thái & phê duyệt
FIRST	M4 không có quy trình nộp/phê duyệt như phiếu nghiệp vụ. "Trạng thái" ở đây là trạng thái chiếm dụng của từng Vị trí lưu trữ, được hệ thống tự tính từ Sổ kho.
TABLE	Trạng thái bin|Ý nghĩa
ROW	Empty (Trống)|Bin không còn hàng (tồn ≈ 0)
ROW	In Use (Đang dùng)|Bin có hàng, chưa đầy (dưới 95% sức chứa)
ROW	Full (Đầy)|Tỷ lệ chiếm dụng ≥ 95% sức chứa — nên xếp sang bin khác
BODY	Trạng thái, **Tồn hiện tại** và **Tỷ lệ chiếm dụng (%)** là chỉ-đọc, được tính lại khi chạy đồng bộ/tính lại (recompute / reconcile). Bin còn bật cờ **Bin cách ly (QC Hold)** để đánh dấu hàng chờ QC chưa được xuất.
H3	3.4.5	Kết quả & truy vết
UL	Khai báo bin tạo bản ghi **Bin Location** mã **SC-BIN-#####**; quy tắc xếp hàng tạo **Putaway Rule** mã **PWR-#####**.
UL	Xếp hàng lên kệ ghi **vị trí lưu trữ (bin_location)** vào các dòng Sổ kho (SC Stock Ledger Entry) tương ứng — không thay đổi số lượng tồn.
UL	Tồn kho và giá trị trên màn hình Tồn kho / Danh sách kho luôn lấy trực tiếp từ Sổ kho, nên khớp tuyệt đối với phiếu nhập–xuất–chuyển.
UL	Mỗi bin lưu lịch sử nhập–xuất tại vị trí đó (truy được "ai để gì, lúc nào, vào ô nào"); cảnh báo hết hạn / sắp hết hạn hiển thị ngay trên dòng tồn.
H3	3.4.6	Lỗi thường gặp & mẹo
UL	**SC-E-BIN-NOT-EMPTY — Bin còn hàng không xóa được:** chuyển hết hàng sang bin khác rồi mới xóa.
UL	**SC-E-PUTAWAY-RULE — Quy tắc thiếu tiêu chí:** phải nhập Vật tư cụ thể HOẶC Nhóm vật tư.
UL	**SC-E-BIN-CAPACITY — Bin vượt sức chứa:** chọn bin còn chỗ, hoặc tăng sức chứa, hoặc để 0 (không giới hạn).
UL	**"Kho chưa khai vị trí" ở màn xếp hàng:** kho chưa có Bin Location nào — khai bin trước (3.4.3.3).
UL	**Kho không hiện trên bản đồ:** kho chưa được đặt toạ độ — vào Thiết kế bản đồ để đặt vị trí.
UL	**Mẹo —** đặt **Bin đích** mặc định qua Putaway Rule cho các nhóm hàng hay nhập để khỏi chọn tay mỗi lần.
UL	**Mẹo —** in nhãn **Barcode bin** dán lên kệ để tra vị trí và (khi có PDA) quét xếp hàng nhanh.
UL	**Mẹo —** nếu số liệu chiếm dụng bin nghi sai lệch, chạy đồng bộ/tính lại (reconcile) để cập nhật lại từ Sổ kho.
H3	3.4.7	Liên quan
UL	Xem 3.3 — Tiếp nhận & Kiểm tra chất lượng (hàng nhận từ PR là nguồn của danh sách xếp hàng lên kệ).
UL	Xem 3.5 — Quản lý FEFO & hạn dùng (lấy hàng theo lô hết hạn trước, cảnh báo hạn dùng).
UL	Xem 3.6 — Chuyển kho (di chuyển hàng giữa các kho/bin; bản đồ chỉ đường tuyến chuyển).
UL	Xem 3.7 — Cấp phát & BHYT (xuất hàng từ tồn kho cho khoa/bệnh nhân).
