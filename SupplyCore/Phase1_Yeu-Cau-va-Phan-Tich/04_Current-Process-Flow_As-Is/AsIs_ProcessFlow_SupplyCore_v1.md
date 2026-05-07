**SupplyCore**  |  Current Process Flow – As-Is  |  v1.0

**SUPPLYCORE**

**Hệ Thống Quản Lý Chuỗi Cung Ứng Vật Tư Tiêu Hao Bệnh Viện**

|<p>**CURRENT PROCESS FLOW – AS-IS**</p><p>*Quy Trình Hiện Tại – Phân Tích Thực Trạng*</p>|
| :-: |

Phiên bản: 1.0  |  Ngày: 05/05/2026  |  Trạng thái: Bản chính thức


# **1. MỤC ĐÍCH VÀ PHẠM VI TÀI LIỆU**
Tài liệu này mô tả quy trình quản lý vật tư tiêu hao hiện tại (As-Is) tại bệnh viện trước khi triển khai SupplyCore. Mục tiêu là ghi lại chính xác cách thức hoạt động hiện tại, xác định các điểm đau (pain points), lãng phí và cơ hội cải tiến làm cơ sở thiết kế quy trình mới (To-Be).

Phân tích được thực hiện thông qua: phỏng vấn trực tiếp với thủ kho, nhân viên mua hàng, điều dưỡng các khoa và kế toán vật tư; quan sát quy trình thực tế; thu thập và phân tích các mẫu biểu hiện đang sử dụng.

## **1.1 Tóm Tắt Hiện Trạng**

|**Khía cạnh**|**Hiện trạng**|**Công cụ đang dùng**|
| :- | :- | :- |
|Quản lý tồn kho|Sổ tay + Excel không đồng bộ|Excel, sổ tay ghi chép|
|Đặt hàng mua sắm|Email, điện thoại, giấy tờ thủ công|Email, Word, fax|
|Quản lý hợp đồng NCC|File scan lưu trong folder máy tính|Folder chia sẻ, USB|
|Kiểm tra QC nhập kho|Kiểm tra mắt thường, ghi sổ|Sổ tay, biên bản giấy|
|Quản lý hạn dùng|Dán nhãn thủ công, kiểm tra không thường xuyên|Nhãn giấy, Excel riêng|
|Cấp phát khoa phòng|Điều dưỡng gọi điện/viết phiếu giấy|Điện thoại, phiếu giấy|
|Kiểm kê định kỳ|Dừng hoạt động đếm thủ công 1-2 ngày/quý|Giấy, bút, Excel tổng hợp|
|Quyết toán BHYT|Tổng hợp thủ công từ nhiều nguồn|Excel nhiều file, sổ tay|


# **2. QUY TRÌNH MUA HÀNG HIỆN TẠI (AS-IS)**
## **2.1 Quy Trình Đặt Hàng**
Mô tả: Khi một khoa phòng cần bổ sung vật tư hoặc kho tổng phát hiện sắp hết hàng, quy trình đặt hàng được khởi động theo trình tự thủ công sau:

|**B.**|**Người thực hiện**|**Hoạt động**|**Công cụ / Tài liệu**|
| :-: | :- | :- | :- |
|1|Thủ kho / Điều dưỡng|Nhận thấy tồn kho thấp (bằng cách đếm thực tế hoặc nhớ theo kinh nghiệm)|Quan sát trực tiếp|
|2|Điều dưỡng trưởng / Thủ kho|Viết tay yêu cầu mua sắm vào mẫu giấy hoặc gọi điện thoại lên phòng vật tư|Mẫu giấy, điện thoại|
|3|NV Mua hàng|Nhận yêu cầu, tra thủ công bảng giá NCC trong file Excel hoặc email cũ để tìm giá|Excel, hộp thư email|
|4|NV Mua hàng|Soạn thảo PO bằng Word/Excel, in ra giấy để trình ký|Word, Excel, máy in|
|5|Trưởng phòng Vật tư|Ký duyệt PO giấy (có khi phải chờ 1-3 ngày nếu bận họp hoặc đi công tác)|Bản in giấy|
|6|NV Mua hàng|Fax hoặc email PO cho NCC (có khi gọi điện thêm để xác nhận NCC đã nhận)|Fax, email, điện thoại|
|7|NV Mua hàng|Lưu bản sao PO vào folder máy tính và/hoặc file cứng|Folder máy tính, tủ hồ sơ|

### **Điểm Đau – Quy Trình Đặt Hàng**
- ⚠ Không có cảnh báo tự động: thủ kho phát hiện hết hàng khi cần lấy thực tế, thường là quá muộn
- ⚠ Tra giá thủ công tốn 30-60 phút/đơn hàng, dễ dùng nhầm giá cũ
- ⚠ PO giấy: chờ ký duyệt 1-3 ngày, không theo dõi được trạng thái
- ⚠ Không có hệ thống so sánh giá giữa các NCC trong thời gian thực
- ⚠ Không liên kết tự động với hợp đồng khung: NV phải tự kiểm tra và áp giá hợp đồng
- ⚠ Lưu trữ phân tán: mỗi người lưu file riêng, không có phiên bản thống nhất

## **2.2 Quy Trình Tiếp Nhận Hàng Từ NCC**

|**B.**|**Người thực hiện**|**Hoạt động**|**Công cụ / Tài liệu**|
| :-: | :- | :- | :- |
|1|NCC|Giao hàng tại kho bệnh viện, mang theo phiếu giao hàng giấy|Phiếu giao hàng giấy|
|2|Thủ kho|Đối chiếu phiếu giao hàng với PO giấy (phải đi tìm file PO trong tủ hoặc folder máy tính)|PO giấy, phiếu giao hàng|
|3|Thủ kho|Đếm số lượng thực tế bằng tay, kiểm tra hạn dùng bằng mắt thường, ghi vào sổ|Sổ tay, bút|
|4|Thủ kho|Nhập số liệu vào file Excel tồn kho (có khi nhập vào cuối ngày hoặc ngày hôm sau)|Excel tồn kho|
|5|Thủ kho|Xếp hàng vào kệ, dán nhãn hạn dùng bằng tay lên từng kiện/hộp|Nhãn giấy, bút lông|
|6|NV Mua hàng|Nhận hóa đơn từ NCC, kẹp với PO gốc nộp cho kế toán (mất nhiều ngày do bị thất lạc)|Hóa đơn giấy, PO giấy|

### **Điểm Đau – Tiếp Nhận Hàng**
- ⚠ Tìm PO mất thời gian (trung bình 10-15 phút/lô hàng)
- ⚠ Kiểm tra hạn dùng bằng mắt thường dễ bỏ sót, không có ghi nhận hệ thống
- ⚠ Trễ cập nhật tồn kho (có khi 1-2 ngày sau mới cập nhật Excel)
- ⚠ Số liệu tồn kho trong Excel không phản ánh tình trạng thực tế tức thời
- ⚠ Không có QC checklist chuẩn: mỗi thủ kho kiểm tra theo thói quen riêng
- ⚠ Hóa đơn và PO dễ thất lạc, chậm trễ đến phòng kế toán


# **3. QUY TRÌNH QUẢN LÝ KHO & CẤP PHÁT HIỆN TẠI**
## **3.1 Quy Trình Cấp Phát Cho Khoa Phòng**

|**B.**|**Người thực hiện**|**Hoạt động**|**Vấn đề tiềm ẩn**|
| :-: | :- | :- | :- |
|1|Điều dưỡng khoa|Viết phiếu yêu cầu vật tư giấy, ký tên, nộp hoặc gọi điện lên kho|Phiếu thất lạc, mất thời gian|
|2|Thủ kho|Nhận phiếu, kiểm tra tồn kho xem có đủ hàng để cấp không|Không có hệ thống, phụ thuộc vào Excel/trí nhớ|
|3|Thủ kho|Lấy hàng ra theo phiếu yêu cầu, không nhất thiết theo FEFO (lấy hàng gần nhất/tiện nhất)|Vi phạm FEFO, vật tư hết hạn không được dùng|
|4|Thủ kho|Ghi vào sổ xuất kho, ký tên. Điều dưỡng ký nhận|Ghi sổ có thể thiếu thông tin lô/hạn dùng|
|5|Thủ kho|Cuối ngày/tuần cập nhật Excel tồn kho theo sổ xuất|Trễ cập nhật, sai số cộng dồn|
|6|Điều dưỡng khoa|Ghi nhận vật tư sử dụng cho bệnh nhân vào sổ điều dưỡng/phần mềm HIS (nếu có)|Không liên kết với kho, dữ liệu không đồng bộ|

### **Điểm Đau – Cấp Phát Khoa Phòng**
- ⚠ Không có quy tắc FEFO được áp dụng: thủ kho lấy hàng theo tiện lợi, không theo hạn dùng
- ⚠ Phiếu giấy dễ thất lạc, không có lịch sử cấp phát rõ ràng theo từng lô
- ⚠ Không theo dõi được vật tư nào đã dùng cho bệnh nhân nào
- ⚠ Điều dưỡng phải ghi nhận riêng trong sổ/HIS mà không có liên kết với kho
- ⚠ Không có dữ liệu tiêu thụ thực tế để dự báo nhu cầu

## **3.2 Quy Trình Quản Lý Hạn Dùng Hiện Tại**

|**B.**|**Người thực hiện**|**Hoạt động**|**Vấn đề tiềm ẩn**|
| :-: | :- | :- | :- |
|1|Thủ kho|Khi nhập kho: dán nhãn hạn dùng bằng tay lên từng kiện|Tốn thời gian, nhãn dễ rơi/phai|
|2|Thủ kho|Hàng tháng: kiểm tra thủ công từng kệ hàng để phát hiện hàng sắp hết hạn|Kiểm tra không đều, dễ bỏ sót|
|3|Thủ kho|Nếu phát hiện hàng sắp hết hạn: báo miệng lên trưởng phòng để tăng tốc sử dụng|Không có tài liệu, dễ bị bỏ qua|
|4|Thủ kho|Nếu hàng đã hết hạn: viết đề xuất hủy, chờ duyệt 1-2 tuần, lập biên bản hủy giấy|Hủy muộn gây lãng phí, không có audit trail rõ|

### **Điểm Đau – Quản Lý Hạn Dùng**
- ⚠ Không có hệ thống cảnh báo tự động: phát hiện hết hạn hoàn toàn phụ thuộc vào kiểm tra thủ công
- ⚠ Vật tư hết hạn vẫn có thể bị xuất kho nếu thủ kho không để ý
- ⚠ Không theo dõi được tồn kho theo từng lô (batch tracking): không biết lô nào đang ở kệ nào
- ⚠ Không có khả năng recall: nếu có thông báo thu hồi lô hàng, không thể truy vết nhanh


# **4. QUY TRÌNH KẾ TOÁN & THANH TOÁN NCC HIỆN TẠI**

|**B.**|**Người thực hiện**|**Hoạt động**|**Vấn đề tiềm ẩn**|
| :-: | :- | :- | :- |
|1|NV Mua hàng|Nhận hóa đơn giấy từ NCC, kẹp với PO và phiếu nhập kho, nộp cho kế toán|Bộ hồ sơ dễ thiếu tài liệu|
|2|Kế toán|Đối chiếu thủ công 3 tài liệu: PO gốc, phiếu nhập kho, hóa đơn NCC|Tốn 30-90 phút/hóa đơn, dễ sai sót|
|3|Kế toán|Nhập hóa đơn vào phần mềm kế toán riêng (nếu có) hoặc Excel kế toán|Nhập liệu 2 lần: kho + kế toán|
|4|Kế toán|Lập lệnh chi, trình ký giám đốc, chuyển khoản thủ công|Quy trình dài, thanh toán thường chậm 30-60 ngày|
|5|Kế toán|Lưu trữ hồ sơ giấy và/hoặc scan file vào máy tính|Tìm kiếm hồ sơ cũ mất nhiều thời gian|

### **Điểm Đau – Kế Toán & Thanh Toán**
- ⚠ Dữ liệu kho và kế toán tách rời: phải nhập liệu 2 lần, dẫn đến sai lệch
- ⚠ Đối chiếu 3 chiều thủ công tốn 30-90 phút/hóa đơn
- ⚠ Không có cảnh báo thanh toán đến hạn: thường thanh toán muộn, ảnh hưởng quan hệ NCC
- ⚠ Công nợ NCC không được theo dõi thời gian thực


# **5. QUY TRÌNH QUẢN LÝ BHYT HIỆN TẠI**

|**B.**|**Người thực hiện**|**Hoạt động**|**Vấn đề tiềm ẩn**|
| :-: | :- | :- | :- |
|1|Điều dưỡng khoa|Ghi nhận vật tư dùng cho bệnh nhân vào sổ điều dưỡng/HIS, kèm mã BHYT tra tay|Sai mã BHYT, bỏ sót vật tư|
|2|NV kế toán / phòng BHYT|Tổng hợp từ nhiều nguồn: sổ điều dưỡng, phiếu cấp phát, HIS|Dữ liệu không đồng bộ, mất nhiều giờ|
|3|NV kế toán|Đối chiếu mã BHYT với danh mục BHXH (thường dùng file Excel do tự lập)|Danh mục thường không cập nhật kịp|
|4|NV kế toán|Lập hồ sơ quyết toán, nộp BHXH. Bị từ chối thanh toán phải điều chỉnh và nộp lại|Tỷ lệ bị từ chối 3-8%/kỳ quyết toán|

### **Điểm Đau – Quản Lý BHYT**
- ⚠ Mã BHYT tra thủ công: dễ nhầm lẫn giữa các nhóm N01-N09, đặc biệt khi thông tư mới ban hành
- ⚠ Không có cảnh báo khi giá vật tư vượt giá trần BHYT
- ⚠ Dữ liệu phân tán giữa kho, điều dưỡng, kế toán: tổng hợp quyết toán mất 2-3 ngày/tháng
- ⚠ Tỷ lệ từ chối quyết toán cao do sai mã, sai đơn vị tính, thiếu chứng từ


# **6. TỔNG HỢP ĐIỂM ĐAU VÀ TỔN THẤT**
## **6.1 Ma Trận Điểm Đau Theo Quy Trình**

|**Điểm đau**|**Quy trình ảnh hưởng**|**Tần suất xảy ra**|**Mức độ tác động**|**Rủi ro**|
| :- | :- | :- | :- | :- |
|Thiếu cảnh báo tồn kho tự động|Mua hàng, Cấp phát|Hàng ngày|Cao – Thiếu vật tư điều trị|Cao|
|Không áp dụng FEFO|Xuất kho, Cấp phát|Mỗi lần xuất kho|Cao – An toàn bệnh nhân|Rất cao|
|Trễ cập nhật tồn kho|Nhập kho, Xuất kho|Hàng ngày|Trung bình – Sai số liệu|Trung bình|
|PO giấy chờ ký 1-3 ngày|Mua hàng|Mỗi đơn hàng|Trung bình – Chậm nhập hàng|Trung bình|
|Nhập liệu 2 lần (kho + KT)|Kế toán, Nhập kho|Mỗi hóa đơn|Thấp – Lãng phí thời gian|Thấp|
|Sai mã BHYT thủ công|Cấp phát BHYT|3-8% giao dịch|Cao – Mất doanh thu BHYT|Cao|
|Không truy vết được lô hàng|Recall, Điều tra sự cố|Khi có sự cố|Rất cao – Pháp lý y tế|Rất cao|

## **6.2 Ước Tính Tổn Thất**

|**Loại tổn thất**|**Ước tính**|**Ghi chú**|
| :- | :- | :- |
|Vật tư hết hạn phải hủy|1-3% giá trị tồn kho/năm|Do không áp dụng FEFO|
|Thất thoát quyết toán BHYT|3-8% giá trị vật tư BHYT/kỳ|Do sai mã, thiếu chứng từ|
|Lao động hành chính thủ công|2-4 giờ/ngày/người mua hàng|Nhập liệu, tổng hợp báo cáo|
|Tồn kho dư thừa|20-30% vốn tồn kho bị đọng|Do dự báo thiếu chính xác|
|Rủi ro pháp lý không truy vết được|Không định lượng được|Nghiêm trọng khi xảy ra recall|

─────────────────────────────────────────────────────────────────────────────

Tài liệu As-Is này là cơ sở để so sánh với quy trình To-Be sau khi triển khai SupplyCore. Các điểm đau được xác định ở đây sẽ trở thành thước đo cải tiến sau khi hệ thống đi vào vận hành.
Trang  / 
