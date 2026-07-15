**SupplyCore**  |  Proposed Process Flow – To-Be  |  v1.0

**SUPPLYCORE**

**Hệ Thống Quản Lý Chuỗi Cung Ứng Vật Tư Tiêu Hao Bệnh Viện**

|<p>**PROPOSED PROCESS FLOW – TO-BE**</p><p>*Quy Trình Mới Đề Xuất Sau Khi Triển Khai SupplyCore*</p>|
| :-: |

Phiên bản: 1.0  |  Ngày: 05/05/2026  |  Trạng thái: Bản chính thức


# **1. TỔNG QUAN QUY TRÌNH MỚI**
Tài liệu này mô tả quy trình To-Be – cách thức hoạt động mới sau khi triển khai SupplyCore trên nền tảng Frappe/ERPNext v15. Mỗi quy trình mới được đối chiếu trực tiếp với quy trình As-Is tương ứng để làm rõ sự cải tiến.

## **1.1 Nguyên Tắc Thiết Kế Quy Trình Mới**
- Tự động hóa tối đa: Hệ thống tự động thực hiện những việc có thể, con người chỉ quyết định khi cần phán xét
- Dữ liệu một nguồn: Nhập liệu một lần, dùng nhiều nơi. Kho và kế toán cùng một nguồn dữ liệu
- Workflow số hóa: Phê duyệt qua hệ thống, không qua giấy tờ
- Truy xuất đầy đủ: Mọi giao dịch đều có audit trail, có thể truy vết đến lô hàng
- Cảnh báo chủ động: Hệ thống chủ động thông báo, không chờ người dùng phát hiện

## **1.2 So Sánh Tổng Quan As-Is vs To-Be**

|**Khía cạnh**|**As-Is (Trước SupplyCore)**|**To-Be (Với SupplyCore)**|
| :- | :- | :- |
|Cảnh báo tồn kho|Thủ công, phát hiện muộn|Tự động 24/7, cảnh báo theo ngưỡng ROP|
|Thời gian tạo PO|1-3 ngày (giấy, chờ ký)|< 2 giờ (digital workflow)|
|Kiểm soát hạn dùng|Thủ công hàng tháng|Tự động, cảnh báo 30/60/90 ngày|
|Áp dụng FEFO|Không nhất quán|100% tự động, hệ thống gợi ý lô xuất|
|Cập nhật tồn kho|Trễ 1-2 ngày|Tức thì sau mỗi giao dịch|
|Đối chiếu 3 chiều|Thủ công 30-90 phút/hóa đơn|Tự động, cảnh báo chỉ khi có sai lệch|
|Quản lý BHYT|Tra tay, 3-8% sai mã|Tự động gán mã, < 0.1% sai sót|
|Truy vết lô hàng|Không có khả năng|Tức thì, đầy đủ từ NCC đến bệnh nhân|
|Báo cáo điều hành|Tổng hợp thủ công 2-3 ngày|Dashboard real-time, tự động|


# **2. QUY TRÌNH MUA HÀNG MỚI (TO-BE)**
## **2.1 Quy Trình Đặt Hàng Tự Động**
Thay vì phụ thuộc vào quan sát thủ công, SupplyCore theo dõi tồn kho liên tục và tự động khởi động quy trình đặt hàng khi cần thiết.

|**B.**|**Hệ thống / Người thực hiện**|**Hoạt động MỚI**|**Thời gian**|
| :-: | :- | :- | :- |
|1|SupplyCore (tự động)|Hệ thống theo dõi tồn kho liên tục. Khi tồn kho xuống dưới ROP, tự động tạo đề xuất mua sắm và gửi thông báo cho SC-PURCHASER|Tức thì|
|2|SC-PURCHASER|Nhận thông báo, xem xét đề xuất. Hệ thống gợi ý: NCC theo hợp đồng khung hiện hành, số lượng đặt hàng tối ưu (EOQ)|15-30 phút|
|3|SC-PURCHASER|Tạo Release Order từ hợp đồng khung: chọn vật tư, nhập số lượng. Hệ thống tự điền giá, điều khoản từ HĐ khung|5-10 phút|
|4|SupplyCore (tự động)|Kiểm tra ngưỡng phê duyệt: nếu giá trị ≤ hạn mức → tự động approve. Nếu > hạn mức → gửi thông báo cho SC-MANAGER phê duyệt trên di động|Tức thì|
|5|SC-MANAGER (nếu cần)|Phê duyệt trên mobile app SupplyCore, có thể từ bất kỳ đâu. Hệ thống ghi nhận chữ ký số và thời gian|5 phút|
|6|SupplyCore (tự động)|Sau khi approved: tự động tạo Purchase Order, gửi email PDF cho NCC, cập nhật trạng thái PO. Lưu toàn bộ lịch sử|Tức thì|

### **Cải Tiến So Với As-Is – Quy Trình Đặt Hàng**
- **✓ Thời gian tạo PO: từ 1-3 ngày giảm xuống < 2 giờ**
- **✓ Cảnh báo tự động thay thế phát hiện thủ công**
- **✓ Giá hợp đồng tự động điền: loại bỏ lỗi tra giá nhầm**
- **✓ Phê duyệt số hóa: phê duyệt được từ di động, không cần có mặt văn phòng**
- **✓ Toàn bộ PO được lưu tập trung, có thể tìm kiếm và theo dõi tức thì**

## **2.2 Quy Trình Tiếp Nhận Hàng & QC**

|**B.**|**Hệ thống / Người thực hiện**|**Hoạt động MỚI**|**Thời gian**|
| :-: | :- | :- | :- |
|1|SC-STOREKEEPER|Mở màn hình 'Tiếp nhận hàng' trên tablet/máy tính kho. Tìm PO bằng 1 click từ danh sách PO chờ nhận|1 phút|
|2|SC-STOREKEEPER + EXT-SCANNER|Scan barcode vật tư → hệ thống tự điền mã, tên, đơn vị. Nhập số lô + hạn dùng (hoặc scan nếu NCC hỗ trợ GS1)|1-2 phút/mặt hàng|
|3|SC-STOREKEEPER|Thực hiện QC theo checklist điện tử: tick từng tiêu chí. Hệ thống hiển thị ảnh mẫu để đối chiếu quy cách|3-5 phút/lô|
|4|SupplyCore (tự động)|Kiểm tra tự động: hạn dùng < 30 ngày → cảnh báo đỏ. Số lượng ≠ PO → ghi nhận partial receipt, tạo backorder|Tức thì|
|5|SC-STOREKEEPER|Xác nhận nhập kho. Hệ thống tạo Stock Entry, cập nhật tồn kho NGAY LẬP TỨC theo lô và hạn dùng|1 phút|
|6|SupplyCore (tự động)|Tạo Purchase Receipt liên kết với PO. Thông báo cho kế toán có thể xử lý hóa đơn. Tạo GL Entry tự động|Tức thì|

### **Cải Tiến So Với As-Is – Tiếp Nhận Hàng**
- **✓ Tìm PO: từ 10-15 phút giảm xuống 1 click**
- **✓ Tồn kho cập nhật tức thì (không còn trễ 1-2 ngày)**
- **✓ QC checklist chuẩn hóa: tất cả thủ kho làm theo cùng một quy trình**
- **✓ Hệ thống ghi nhận lô và hạn dùng cho 100% vật tư nhập kho**
- **✓ Kế toán nhận thông báo ngay, không cần NV mua hàng mang hóa đơn**


# **3. QUY TRÌNH QUẢN LÝ KHO MỚI (TO-BE)**
## **3.1 Quy Trình Cấp Phát Khoa Phòng**
Điều dưỡng đặt yêu cầu vật tư trực tiếp trên hệ thống. Xuất kho theo FEFO được thực thi tự động.

|**B.**|**Hệ thống / Người thực hiện**|**Hoạt động MỚI**|**Thời gian**|
| :-: | :- | :- | :- |
|1|SC-WARD-STAFF|Đăng nhập SupplyCore, tạo 'Yêu cầu vật tư' từ khoa: chọn vật tư từ danh mục, nhập số lượng|3-5 phút|
|2|SupplyCore (tự động)|Kiểm tra tồn kho khoa và kho tổng. Nếu khoa có đủ: duyệt tự động. Nếu thiếu: tạo yêu cầu chuyển kho từ kho tổng|Tức thì|
|3|SC-STOREKEEPER|Nhận thông báo yêu cầu cấp phát, xác nhận và chuẩn bị hàng. Hệ thống gợi ý lô xuất theo FEFO tự động|5-10 phút|
|4|SC-STOREKEEPER|Scan vật tư khi đóng gói để xác nhận đúng lô. Xác nhận cấp phát – hệ thống trừ tồn kho tức thì|2-3 phút|
|5|SC-WARD-STAFF|Nhận vật tư, ký xác nhận điện tử trên tablet. Lịch sử cấp phát được lưu đầy đủ|1 phút|

### **Cải Tiến So Với As-Is – Cấp Phát Khoa Phòng**
- **✓ FEFO 100% tự động: không còn rủi ro xuất sai hạn dùng**
- **✓ Lịch sử cấp phát đầy đủ: biết chính xác vật tư nào đã đến khoa nào, lô nào**
- **✓ Điều dưỡng đặt yêu cầu trực tuyến: không cần điện thoại/giấy tờ**
- **✓ Tồn kho cập nhật tức thì sau mỗi giao dịch cấp phát**

## **3.2 Quy Trình Cấp Phát Gắn Bệnh Nhân & BHYT**

|**B.**|**Hệ thống / Người thực hiện**|**Hoạt động MỚI**|**Thời gian**|
| :-: | :- | :- | :- |
|1|SC-WARD-STAFF|Tìm bệnh nhân bằng mã BN (hoặc scan QR thẻ BN nếu tích hợp HIS). Hệ thống tự hiển thị loại BHYT, mức hưởng|1 phút|
|2|SC-WARD-STAFF|Thêm vật tư sử dụng: chọn mã vật tư. Hệ thống TỰ ĐỘNG gán mã BHYT (N01-N09), hiển thị giá trần, tỷ lệ chi trả|1 phút/loại VT|
|3|SupplyCore (tự động)|Tính toán tự động: phần BHYT chi trả, phần bệnh nhân tự trả, phần vượt giá trần. Hiển thị chi tiết để điều dưỡng xác nhận|Tức thì|
|4|SC-WARD-STAFF|Xác nhận. Hệ thống tạo Stock Entry, trừ tồn kho theo FEFO, ghi nhận dữ liệu BHYT vào hồ sơ bệnh nhân|1 phút|
|5|SupplyCore (tự động, cuối kỳ)|Tổng hợp tự động dữ liệu BHYT theo bệnh nhân, khoa, mã BHYT. Tạo báo cáo quyết toán sẵn sàng nộp BHXH|Tự động|

### **Cải Tiến So Với As-Is – Quản Lý BHYT**
- **✓ Mã BHYT tự động: từ 3-8% sai mã giảm xuống < 0.1%**
- **✓ Tính toán tự động phần chi trả BHYT/bệnh nhân**
- **✓ Cảnh báo tức thì khi giá vật tư vượt giá trần BHYT**
- **✓ Quyết toán BHYT tự động: từ 2-3 ngày tổng hợp giảm xuống 1 click**


# **4. QUY TRÌNH KIỂM KÊ MỚI (TO-BE)**
## **4.1 Kiểm Kê Bằng PDA**

|**B.**|**Hệ thống / Người thực hiện**|**Hoạt động MỚI**|**Thời gian**|
| :-: | :- | :- | :- |
|1|SC-MANAGER|Tạo Phiếu Kiểm Kê trên SupplyCore: chọn kho/khu vực, ngày kiểm kê, phân công thủ kho. Danh sách vật tư tự động gửi đến PDA|15 phút|
|2|SC-STOREKEEPER|Dùng PDA đến từng vị trí kho: scan bin location → PDA hiển thị danh sách vật tư tại vị trí đó|Linh hoạt|
|3|SC-STOREKEEPER|Scan từng vật tư, nhập số lượng đếm được. PDA xác nhận và chuyển sang vật tư tiếp theo|1 phút/mặt hàng|
|4|SupplyCore (tự động)|So sánh tự động số liệu thực tế vs sổ sách theo thời gian thực. SC-MANAGER có thể theo dõi tiến độ trên máy tính|Tức thì|
|5|SC-MANAGER|Xem báo cáo chênh lệch. Phê duyệt điều chỉnh tồn kho (Stock Reconciliation). Hệ thống tạo GL Entry tự động|30 phút|

### **Cải Tiến So Với As-Is – Kiểm Kê**
- **✓ Thời gian kiểm kê: từ 1-2 ngày/quý giảm xuống 4-8 giờ**
- **✓ Không cần dừng hoạt động kho trong khi kiểm kê**
- **✓ Theo dõi tiến độ kiểm kê thời gian thực**
- **✓ Tự động đối chiếu và xử lý chênh lệch, không cần nhập lại Excel**


# **5. QUY TRÌNH KẾ TOÁN & THANH TOÁN MỚI (TO-BE)**

|**B.**|**Hệ thống / Người thực hiện**|**Hoạt động MỚI**|**Thời gian**|
| :-: | :- | :- | :- |
|1|SC-ACCOUNTANT|Nhận thông báo từ SupplyCore: hóa đơn NCC đã được scan/upload vào hệ thống (NV mua hàng upload trực tiếp)|Tức thì|
|2|SupplyCore (tự động)|Thực hiện 3-way matching tự động: PO ↔ Purchase Receipt ↔ Purchase Invoice. Chỉ flag những chênh lệch cần người xem xét|< 1 phút|
|3|SC-ACCOUNTANT|Xử lý các trường hợp chênh lệch (nếu có). Phê duyệt hóa đơn. Hệ thống tạo GL Entry tự động theo tài khoản đã cấu hình|5-15 phút|
|4|SC-ACCOUNTANT|Tạo lệnh thanh toán trong SupplyCore, hệ thống tự điền thông tin NCC, số tài khoản, số tiền. Trình SC-MANAGER ký duyệt online|5 phút|
|5|SupplyCore (tự động)|Cảnh báo thanh toán đến hạn trước 7/3/1 ngày. Theo dõi công nợ NCC thời gian thực. Báo cáo aging AP tự động|Liên tục|

### **Cải Tiến So Với As-Is – Kế Toán & Thanh Toán**
- **✓ 3-way matching tự động: từ 30-90 phút/hóa đơn xuống < 1 phút**
- **✓ Không nhập liệu 2 lần: kho và kế toán cùng nguồn dữ liệu**
- **✓ GL Entry tự động 100%: loại bỏ sai sót hạch toán thủ công**
- **✓ Cảnh báo thanh toán đến hạn: không còn tình trạng thanh toán muộn**


# **6. CHỈ SỐ KẾT QUẢ DỰ KIẾN (EXPECTED OUTCOMES)**
## **6.1 KPI So Sánh As-Is vs To-Be**

|**Chỉ số**|**As-Is (Hiện tại)**|**To-Be (Mục tiêu)**|**Cải thiện**|
| :- | :- | :- | :- |
|Thời gian tạo PO|1-3 ngày|< 2 giờ|~90%↓|
|Cập nhật tồn kho|1-2 ngày trễ|Tức thì|100%|
|Thời gian kiểm kê|1-2 ngày/quý|4-8 giờ/quý|~80%↓|
|Tồn kho hết hạn|1-3% giá trị/năm|< 0.5%|~75%↓|
|Sai mã BHYT|3-8% giao dịch|< 0.1%|~98%↓|
|Đối chiếu hóa đơn|30-90 phút/HĐ|< 5 phút/HĐ|~93%↓|
|Thời gian quyết toán BHYT|2-3 ngày/tháng|< 2 giờ|~90%↓|
|Khả năng recall lô hàng|Không có|< 5 phút|Tính năng mới|
|Báo cáo điều hành|2-3 ngày tổng hợp|Real-time dashboard|100%|

## **6.2 Lợi Ích Định Tính**
- An toàn bệnh nhân: FEFO 100% và quản lý recall loại bỏ rủi ro sử dụng vật tư hết hạn hoặc bị thu hồi
- Tuân thủ pháp luật: Đáp ứng đầy đủ yêu cầu lưu trữ hồ sơ y tế, BHYT, và các quy định Bộ Y tế
- Ra quyết định dựa trên dữ liệu: Dashboard điều hành giúp lãnh đạo ra quyết định chiến lược về mua sắm
- Nâng cao sự hài lòng nhân viên: Giảm công việc thủ công tẻ nhạt, nhân viên tập trung vào công việc giá trị cao hơn
- Sẵn sàng mở rộng: Kiến trúc Frappe/ERPNext dễ dàng mở rộng khi bệnh viện phát triển hoặc thêm cơ sở

─────────────────────────────────────────────────────────────────────────────

Tài liệu To-Be Process Flow này mô tả trạng thái lý tưởng sau khi SupplyCore được triển khai và vận hành ổn định. Quá trình chuyển đổi từ As-Is sang To-Be sẽ có kế hoạch change management riêng để đảm bảo chuyển đổi suôn sẻ.
Trang  / 
