# SupplyCore — Hướng dẫn viết nội dung (cho người soạn từng chương)

Bạn đang soạn **một mục module** trong Chương 3 "Tác vụ nghiệp vụ" của tài liệu Hướng dẫn sử dụng SupplyCore.
Văn bản đầu ra phải là **DSL** (xem cuối file) ghi vào đúng file được giao. Toàn bộ nội dung bằng **tiếng Việt**, giọng văn hướng người dùng cuối (thủ kho, nhân viên bán hàng, kế toán… ở doanh nghiệp phân phối), rõ ràng, ngắn gọn, đúng thực tế phần mềm.

## Nguyên tắc tối quan trọng
- **Tuyệt đối chính xác với phần mềm thật.** Chỉ mô tả những gì có trong code bạn đọc (doctype JSON/PY, trang Vue) và trong tài liệu BA `docs/ba-miyano/SupplyCore_MVL_BA.html`. KHÔNG bịa nút, màn hình, hay tính năng không tồn tại.
- Trích **nhãn tiếng Việt đúng nguyên văn** khi có (tên nút, trạng thái, menu). Bọc nhãn/nút trong `**...**` để in đậm.
- Nếu một bước không chắc có UI riêng, mô tả theo **mô hình điều hướng chung** bên dưới (đa số DocType dùng màn hình Danh sách + Chi tiết dùng chung).

## Mô hình điều hướng SupplyCore (SPA Vue, KHÔNG phải Frappe Desk)
- Sau đăng nhập → **Trang chủ / Tổng quan (Dashboard)**. Thanh bên trái (Sidebar) hiển thị nhóm chức năng theo **vai trò (persona)**.
- Mỗi module mở qua **Trang module (ModuleHub)**: hiển thị các **thẻ DocType** (mỗi thẻ có biểu tượng, tên, số bản ghi). Bấm thẻ → xem 10 bản ghi gần nhất, nút **Tạo mới**, link **Danh sách**.
- **Danh sách** (`/list/<doctype>`): bảng có tìm kiếm, lọc, sắp xếp, phân trang, nút **Tạo mới**, **Nhập** (CSV/Excel), **Xuất**.
- **Chi tiết** (`/doc/<doctype>/<tên>`): xem/sửa bản ghi. Bản nháp có nút **Sửa**, **Lưu**, **Nộp** (Submit nếu doctype submittable), **Hủy**, **Xóa**; có panel bản ghi liên quan; một số doctype có panel chuyên biệt (FEFO, tồn kho, QC…).
- Các màn hình chuyên biệt có route riêng: Tồn kho `/stock-balance`, Xếp hàng lên kệ `/putaway`, Bản đồ kho `/warehouse-map`, Thiết kế bản đồ `/map-editor`, Truy xuất lô `/batch-trace`, Báo cáo tài chính `/financial-reports`, Cảnh báo `/alerts`, Người dùng `/users`. Cổng khách hàng là trang riêng `/portal` (khách dùng, không phải nhân viên).
- Quy ước: "Không có phận sự thì không thấy" — nếu thiếu quyền, menu ẩn / route chặn (trang **Không có quyền** /403) / nút biến mất.

## Vai trò — gọi tên đúng khi nói "Ai làm được"
- **Quản trị Hệ thống** (System Manager) — toàn quyền cấu hình.
- **Trưởng phòng** (SupplyCore Manager) — duyệt PO/Thanh toán/Hợp đồng, duyệt hàng loạt HĐ khung, kết luận QC.
- **Lãnh đạo** (SupplyCore Executive) — phê duyệt cấp cao giá trị lớn, duyệt phát hành thu hồi.
- **NV Mua & Bán hàng** (SupplyCore Purchaser) — đơn mua, NCC; khách hàng, HĐ khung bán, đơn hàng.
- **Thủ kho** (SupplyCore Storekeeper) — nhập–xuất–tồn, FEFO, soạn hàng giao khách, kiểm kê.
- **NV Kho vận hành** (Warehouse Officer) — vị trí kệ, xếp hàng, hỗ trợ nhập/chuyển kho.
- **Kế toán** (SupplyCore Accountant) — hóa đơn mua và bán, đối chiếu 3 bên, thanh toán, thu tiền.
- **Kiểm định** (QC Officer) — kết luận QC lô, khóa lô/cách ly, truy xuất, thu hồi.
- **Kiểm toán** (SupplyCore Auditor) — chỉ đọc toàn bộ dữ liệu.
- **Khách hàng** (SC Customer Portal) — chỉ dùng Cổng khách hàng `/portal`, không vào giao diện nội bộ.

## Cấu trúc BẮT BUỘC của mỗi mục module (giống AssetCore) — dùng đúng số mục được giao (ví dụ 3.7)
- `H2  3.x  <Tên module>` (ví dụ: `M7 · Bán hàng & Bàn giao`)
- `H3  3.x.1  Mục đích & khi nào dùng` → 1 đoạn FIRST mô tả module dùng để làm gì, khi nào dùng.
- `H3  3.x.2  Ai làm được & cần chuẩn bị gì` → dòng "Vai trò: …" (BODY, in đậm "Vai trò:") và "Cần có trước: …".
- `H3  3.x.3  Các bước thực hiện` → chia nhiều `H4 3.x.3.1 …` cho từng tác vụ con; mỗi tác vụ dùng danh sách **OL** (các bước đánh số) và **IMG** placeholder ở chỗ cần ảnh.
- `H3  3.x.4  Trạng thái & phê duyệt` → giải thích vòng đời trạng thái; nên có 1 **TABLE** Trạng thái | Ý nghĩa (| Ai duyệt nếu có).
- `H3  3.x.5  Kết quả & truy vết` → dùng UL: tạo ra bản ghi gì (mã/naming series), ghi vào sổ kho (Stock Ledger), KPI/cảnh báo liên quan.
- `H3  3.x.6  Lỗi thường gặp & mẹo` → mỗi lỗi/mẹo 1 dòng OL hoặc UL; nêu mã lỗi SC-Exxx khi có và cách xử lý; thêm vài "Mẹo —".
- `H3  3.x.7  Liên quan` → UL trỏ tới các mục liên quan (ví dụ "Xem 3.3 — Tiếp nhận & QC").

Độ dài mục tiêu mỗi module: tương đương 4–7 trang. Viết đủ chi tiết, thực dụng.

## DSL — cú pháp (mỗi block 1 dòng; phân tách bằng ký tự TAB)
```
H1 \t <số> \t <tiêu đề>
H2 \t <số> \t <tiêu đề>
H3 \t <số> \t <tiêu đề>
H4 \t <số> \t <tiêu đề>
FIRST \t <đoạn văn>            (đoạn đầu sau heading)
BODY  \t <đoạn văn>            (đoạn thường; dùng **...** để in đậm phần đầu dòng như "Vai trò:")
UL \t <mục bullet>
OL \t <bước>                  (nhiều dòng OL liên tiếp = 1 danh sách đánh số, tự khởi động lại từ 1)
NOTE \t <nội dung>            (khung xanh "Gợi ý:"; muốn nhãn khác: "Nhãn: nội dung")
WARN \t <nội dung>            (khung đỏ "Lưu ý:")
IMG \t <mô tả ảnh chụp màn hình cần chèn>
TABLE \t Cột1|Cột2|Cột3
ROW \t a|b|c
```
- Inline: `**đậm**`. Trong TABLE/ROW dùng `|` ngăn cột. Dòng trống và dòng bắt đầu bằng `#` bị bỏ qua.
- KHÔNG dùng emoji. KHÔNG markdown khác (không `##`, không `-`, không `1.`); chỉ dùng các từ khóa DSL ở trên.
- Mỗi block phải nằm trên **một dòng duy nhất** (không xuống dòng giữa đoạn). Dùng TAB thật giữa từ khóa và nội dung.

## Ví dụ ngắn (giọng văn & cách dùng DSL) — mô phỏng từ AssetCore
```
H2	3.99	M99 · Ví dụ minh họa
H3	3.99.1	Mục đích & khi nào dùng
FIRST	Module này dùng để … Bạn vào đây khi cần …
H3	3.99.2	Ai làm được & cần chuẩn bị gì
BODY	**Vai trò:** Thủ kho tạo phiếu; Trưởng phòng Vật tư phê duyệt.
BODY	**Cần có trước:** Vật tư, Kho, Nhà cung cấp đã khai báo trong Dữ liệu nền.
H3	3.99.3	Các bước thực hiện
H4	3.99.3.1	Tạo phiếu mới
OL	Từ Trang chủ, mở **M99**, bấm thẻ **<DocType>** rồi nhấn **Tạo mới**.
OL	Điền các trường bắt buộc, chọn **Kho nguồn** và thêm dòng vật tư.
OL	Nhấn **Lưu** rồi **Nộp** để gửi duyệt.
IMG	Màn hình tạo phiếu với danh sách dòng vật tư.
H3	3.99.4	Trạng thái & phê duyệt
TABLE	Trạng thái|Ý nghĩa
ROW	Nháp|Đang soạn, chưa gửi
ROW	Chờ duyệt|Đã nộp, chờ phê duyệt
H3	3.99.5	Kết quả & truy vết
UL	Tạo bản ghi mã **SC-XX-YYYY-#####**.
UL	Ghi nhận vào Sổ kho (Stock Ledger) khi nộp.
H3	3.99.6	Lỗi thường gặp & mẹo
UL	**SC-E024 — Kho nguồn trùng kho đích:** chọn lại kho khác nhau.
UL	**Mẹo —** dùng nút **Xuất** để tải danh sách ra Excel.
H3	3.99.7	Liên quan
UL	Xem 3.3 — Tiếp nhận & Kiểm tra chất lượng.
```
