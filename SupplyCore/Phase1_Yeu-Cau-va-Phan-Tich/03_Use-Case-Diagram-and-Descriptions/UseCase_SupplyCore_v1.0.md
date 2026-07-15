__SUPPLYCORE__

__Hệ Thống Quản Lý Chuỗi Cung Ứng Vật Tư Tiêu Hao Bệnh Viện__

__USE CASE DIAGRAM & DESCRIPTIONS__

*Sơ Đồ & Mô Tả Trường Hợp Sử Dụng*

Phiên bản: 1\.0  |  Ngày: 05/05/2026  |  Trạng thái: Bản chính thức

# 1\. DANH SÁCH ACTOR \(TÁC NHÂN\)

SupplyCore có 7 actor người dùng và 3 actor hệ thống bên ngoài tương tác với hệ thống:

__Loại__

__Actor__

__Mã__

__Mô tả__

__Loại__

👤

Quản trị viên

SC\-ADMIN

Cấu hình, phân quyền, bảo trì hệ thống

Người dùng

👤

Quản lý vật tư

SC\-MANAGER

Quản lý toàn bộ chuỗi cung ứng, phê duyệt

Người dùng

👤

Nhân viên mua hàng

SC\-PURCHASER

Xử lý PO, quản lý NCC, hợp đồng

Người dùng

👤

Thủ kho

SC\-STOREKEEPER

Nhập xuất kho, kiểm kê, QC hàng hóa

Người dùng

👤

Điều dưỡng / NV Khoa

SC\-WARD\-STAFF

Đặt yêu cầu vật tư, cấp phát, ghi nhận sử dụng

Người dùng

👤

Kế toán vật tư

SC\-ACCOUNTANT

Đối chiếu, hạch toán, thanh toán NCC

Người dùng

👤

Lãnh đạo

SC\-EXECUTIVE

Xem báo cáo, phê duyệt ở mức cao

Người dùng

⚙️

Hệ thống email

EXT\-EMAIL

Gửi thông báo, cảnh báo, PO điện tử cho NCC

Hệ thống

⚙️

Barcode/QR Scanner

EXT\-SCANNER

Đọc mã vạch vật tư, kệ hàng trong kho

Hệ thống

⚙️

HIS/EMR \(tương lai\)

EXT\-HIS

Nhận thông tin bệnh nhân, mã BHYT \(API sẵn sàng\)

Hệ thống

# 2\. DANH SÁCH USE CASE THEO MODULE

__Module__

__Mã UC__

__Tên Use Case__

__Actor chính__

__Ưu tiên__

__M1__

UC\-01

Tạo/Cập nhật hồ sơ nhà cung cấp

SC\-PURCHASER, SC\-MANAGER

Cao

M1

UC\-02

Tạo và quản lý Hợp đồng Khung

SC\-PURCHASER, SC\-MANAGER

Cao

M1

UC\-03

Tra cứu và so sánh bảng giá NCC

SC\-PURCHASER

Trung bình

__M2__

UC\-04

Thiết lập mức tồn kho Min/Max/ROP

SC\-MANAGER

Cao

M2

UC\-05

Tạo Release Order từ Hợp đồng Khung

SC\-PURCHASER, SC\-MANAGER

Cao

M2

UC\-06

Phê duyệt Release Order / Purchase Order

SC\-MANAGER, SC\-EXECUTIVE

Cao

__M3__

UC\-07

Tiếp nhận hàng và kiểm tra QC

SC\-STOREKEEPER

Cao

M3

UC\-08

Từ chối / Trả lại hàng cho NCC

SC\-STOREKEEPER, SC\-MANAGER

Cao

M3

UC\-09

Xử lý nhập kho một phần \(partial receipt\)

SC\-STOREKEEPER

Cao

__M4__

UC\-10

Quản lý vị trí kho \(bin location\)

SC\-STOREKEEPER, SC\-ADMIN

Trung bình

M4

UC\-11

Scan barcode/QR để xuất/nhập kho

SC\-STOREKEEPER, EXT\-SCANNER

Cao

__M5__

UC\-12

Quản lý lô và hạn sử dụng

SC\-STOREKEEPER

Cao

M5

UC\-13

Xuất kho theo FEFO tự động

SC\-STOREKEEPER

Cao

M5

UC\-14

Xử lý Product Recall theo số lô

SC\-MANAGER, SC\-STOREKEEPER

Cao

__M6__

UC\-15

Yêu cầu chuyển kho nội bộ

SC\-WARD\-STAFF, SC\-STOREKEEPER

Cao

M6

UC\-16

Phê duyệt và thực hiện chuyển kho

SC\-MANAGER, SC\-STOREKEEPER

Cao

__M7__

UC\-17

Cấp phát vật tư cho khoa/phòng

SC\-STOREKEEPER, SC\-WARD\-STAFF

Cao

M7

UC\-18

Cấp phát vật tư gắn bệnh nhân \+ BHYT

SC\-WARD\-STAFF

Cao

M7

UC\-19

Ghi nhận vật tư thực tế đã sử dụng

SC\-WARD\-STAFF

Cao

__M8__

UC\-20

Đối chiếu 3 chiều \(PO\-Receipt\-Invoice\)

SC\-ACCOUNTANT

Cao

M8

UC\-21

Tạo và duyệt lệnh thanh toán NCC

SC\-ACCOUNTANT, SC\-MANAGER

Cao

__M9__

UC\-22

Lập kế hoạch và thực hiện kiểm kê

SC\-STOREKEEPER, SC\-MANAGER

Cao

M9

UC\-23

Xử lý chênh lệch kiểm kê

SC\-MANAGER, SC\-ACCOUNTANT

Cao

__M10__

UC\-24

Truy xuất lịch sử lô hàng

SC\-MANAGER, SC\-ADMIN

Cao

__M11__

UC\-25

Xem dashboard điều hành

SC\-MANAGER, SC\-EXECUTIVE

Cao

# 3\. MÔ TẢ CHI TIẾT CÁC USE CASE QUAN TRỌNG

## 3\.1 Nhóm Use Case – Mua Hàng & Hợp Đồng

### UC\-02 – Tạo và Quản Lý Hợp Đồng Khung

__Mã Use Case__

UC\-02

__Tên Use Case__

Tạo và Quản Lý Hợp Đồng Khung

__Actor chính__

SC\-PURCHASER \(chính\), SC\-MANAGER \(phê duyệt\)

__Mô tả tóm tắt__

Nhân viên mua hàng tạo Hợp đồng Khung với NCC, xác định danh mục vật tư, đơn giá, thời hạn và điều khoản\. Quản lý phê duyệt hợp đồng\.

__Điều kiện tiên quyết__

NCC đã có trong hệ thống; Người dùng có quyền SC\-PURCHASER; Tất cả vật tư đã có mã trong danh mục

__Luồng chính \(Main Flow\):__

1. 1\. NV Mua hàng chọn NCC từ danh mục, kiểm tra lịch sử hợp tác
2. 2\. Nhập thông tin hợp đồng: số HĐ, ngày ký, giá trị tổng, thời hạn hiệu lực
3. 3\. Thêm danh mục vật tư kèm đơn giá, đơn vị tính, số lượng dự kiến
4. 4\. Đính kèm file scan hợp đồng gốc
5. 5\. Submit để chuyển sang trạng thái 'Chờ phê duyệt' – hệ thống gửi thông báo email cho SC\-MANAGER
6. 6\. SC\-MANAGER xem xét và phê duyệt – hợp đồng chuyển sang 'Có hiệu lực'
7. 7\. Hệ thống lưu hợp đồng và sẵn sàng tạo Release Order từ hợp đồng này

__Luồng thay thế \(Alternative Flow\):__

- 4a\. Nếu vật tư chưa có mã: hệ thống cho phép tạo mã mới trong cùng luồng
- 6a\. Nếu SC\-MANAGER từ chối: hệ thống gửi thông báo kèm lý do, cho phép NV Mua hàng chỉnh sửa và gửi lại
- 6b\. Hợp đồng sắp hết hạn: hệ thống gửi cảnh báo trước 30/15/7 ngày để gia hạn

__Điều kiện hậu \(Post\-condition\):__

- Hợp đồng Khung có trạng thái 'Có hiệu lực'
- Có thể tạo Release Order từ hợp đồng này
- Cảnh báo hết hạn đã được lên lịch tự động

__Xử lý ngoại lệ:__

- Trùng số hợp đồng: hệ thống cảnh báo và không cho lưu
- Đơn giá trong HĐ cao hơn giá trần BHYT: cảnh báo để người dùng xác nhận

### UC\-05 – Tạo Release Order từ Hợp Đồng Khung

__Mã Use Case__

UC\-05

__Tên Use Case__

Tạo Release Order từ Hợp Đồng Khung

__Actor chính__

SC\-PURCHASER \(chính\), SC\-MANAGER \(phê duyệt\)

__Mô tả tóm tắt__

Khi cần đặt hàng, nhân viên mua hàng tạo Release Order \(lệnh gọi hàng\) dựa trên Hợp đồng Khung hiện hành thay vì tạo PO từ đầu\. Giá và điều khoản tự động lấy từ hợp đồng\.

__Điều kiện tiên quyết__

Có ít nhất 1 Hợp đồng Khung đang có hiệu lực với NCC cho vật tư cần đặt

__Luồng chính \(Main Flow\):__

1. 1\. NV Mua hàng vào module Mua hàng, chọn 'Tạo Release Order'
2. 2\. Chọn Hợp đồng Khung từ danh sách – hệ thống tự động lọc theo NCC và vật tư còn hiệu lực
3. 3\. Hệ thống auto\-fill: tên NCC, điều khoản thanh toán, địa chỉ giao hàng từ hợp đồng
4. 4\. NV chọn vật tư cần đặt từ danh mục trong hợp đồng, nhập số lượng
5. 5\. Hệ thống tự động điền đơn giá từ hợp đồng, tính tổng giá trị
6. 6\. Hệ thống kiểm tra ngưỡng phê duyệt: nếu vượt hạn mức → yêu cầu SC\-MANAGER phê duyệt
7. 7\. Sau khi được phê duyệt, Release Order chuyển thành Purchase Order và gửi NCC

__Luồng thay thế \(Alternative Flow\):__

- 4a\. Số lượng đặt vượt số lượng tối đa trong HĐ: hệ thống cảnh báo, yêu cầu xác nhận
- 5a\. Đơn giá trong HĐ đã hết hiệu lực \(giá mới hơn\): hệ thống thông báo và dùng giá mới nhất
- 6a\. Dưới ngưỡng phê duyệt: Release Order tự động approved và tạo PO

__Điều kiện hậu \(Post\-condition\):__

- Purchase Order được tạo với trạng thái 'Đã gửi NCC'
- NCC nhận được PO qua email \(nếu cấu hình tự động gửi\)
- Tồn kho chờ nhận hàng được cập nhật

__Xử lý ngoại lệ:__

- HĐ khung hết hạn trong khi tạo RO: hệ thống từ chối và yêu cầu gia hạn HĐ trước

## 3\.2 Nhóm Use Case – Nhập Kho & Kiểm Soát Chất Lượng

### UC\-07 – Tiếp Nhận Hàng và Kiểm Tra QC

__Mã Use Case__

UC\-07

__Tên Use Case__

Tiếp Nhận Hàng và Kiểm Tra QC

__Actor chính__

SC\-STOREKEEPER \(chính\), EXT\-SCANNER \(hỗ trợ\)

__Mô tả tóm tắt__

Thủ kho tiếp nhận hàng từ NCC, thực hiện kiểm tra QC bắt buộc \(số lô, hạn dùng, số lượng, quy cách\) và nhập vào kho\.

__Điều kiện tiên quyết__

Purchase Order đã được phê duyệt và gửi NCC; NCC đã giao hàng thực tế đến bệnh viện

__Luồng chính \(Main Flow\):__

1. 1\. Thủ kho mở màn hình 'Tiếp nhận hàng', tìm PO theo số PO hoặc tên NCC
2. 2\. Hệ thống hiển thị danh sách vật tư cần nhận theo PO
3. 3\. Thủ kho scan barcode hoặc nhập mã từng vật tư – hệ thống tự điền thông tin
4. 4\. Nhập số lô \(Batch Number\) và hạn sử dụng cho từng mặt hàng
5. 5\. Nhập số lượng thực tế nhận được
6. 6\. Kiểm tra quy cách đóng gói: đánh dấu Pass/Fail từng tiêu chí QC
7. 7\. Nếu tất cả QC Pass: xác nhận nhập kho → hệ thống tạo Stock Entry và cập nhật tồn kho
8. 8\. In phiếu nhập kho có đầy đủ thông tin lô/hạn dùng để ký xác nhận

__Luồng thay thế \(Alternative Flow\):__

- 5a\. Số lượng thực tế < PO: hệ thống tạo partial receipt và backorder tự động
- 5b\. Số lượng thực tế > PO: hệ thống cảnh báo, yêu cầu xác nhận từ SC\-MANAGER
- 4a\. Hạn dùng < 30 ngày: cảnh báo đỏ, yêu cầu phê duyệt đặc biệt
- 6a\. QC Fail: luồng UC\-08 \(Từ chối hàng\) được kích hoạt

__Điều kiện hậu \(Post\-condition\):__

- Stock Entry loại 'Material Receipt' được tạo
- Tồn kho tại kho nhận hàng được cập nhật theo lô và hạn dùng
- Purchase Receipt liên kết với PO được xác nhận
- Kế toán nhận thông báo để xử lý hóa đơn

__Xử lý ngoại lệ:__

- Vật tư không khớp với mã trong hệ thống: thủ kho phải báo SC\-MANAGER để xử lý trước khi nhập

## 3\.3 Nhóm Use Case – Cấp Phát & BHYT

### UC\-18 – Cấp Phát Vật Tư Gắn Bệnh Nhân & BHYT

__Mã Use Case__

UC\-18

__Tên Use Case__

Cấp Phát Vật Tư Gắn Bệnh Nhân & BHYT

__Actor chính__

SC\-WARD\-STAFF \(chính\), EXT\-HIS \(tùy chọn\)

__Mô tả tóm tắt__

Điều dưỡng khoa tạo phiếu cấp phát vật tư cho bệnh nhân cụ thể, gắn mã BHYT tương ứng để tự động tính toán phần BHYT chi trả và phần bệnh nhân tự chi trả\.

__Điều kiện tiên quyết__

Bệnh nhân đã có hồ sơ; Vật tư có mã BHYT trong danh mục; Khoa có tồn kho đủ

__Luồng chính \(Main Flow\):__

1. 1\. Điều dưỡng mở màn hình 'Cấp phát vật tư', tìm bệnh nhân theo mã BN hoặc tên
2. 2\. Hệ thống hiển thị thông tin bệnh nhân, loại BHYT \(nếu có\), mức hưởng
3. 3\. Thêm vật tư cần cấp phát: chọn mã vật tư, số lượng
4. 4\. Hệ thống tự động: gán mã BHYT \(N01\-N09\), hiển thị giá trần, tỷ lệ BH chi trả
5. 5\. Hệ thống tính toán: phần BHYT trả / phần bệnh nhân tự trả cho từng vật tư
6. 6\. Điều dưỡng xác nhận và submit phiếu cấp phát
7. 7\. Hệ thống tạo Stock Entry loại 'Material Issue', trừ tồn kho theo FEFO
8. 8\. Tổng hợp dữ liệu BHYT để phục vụ quyết toán

__Luồng thay thế \(Alternative Flow\):__

- 2a\. Bệnh nhân không có thẻ BHYT: tất cả chi phí tự chi trả, không gán mã BHYT
- 4a\. Vật tư có nhiều mã BHYT: hiển thị danh sách để điều dưỡng chọn đúng loại
- 4b\. Giá vật tư > giá trần BHYT: hệ thống tự động chia phần vượt trần
- 6a\. Tồn kho khoa không đủ: hệ thống cho phép tạo yêu cầu chuyển kho khẩn cấp

__Điều kiện hậu \(Post\-condition\):__

- Stock Entry được tạo, tồn kho khoa phòng giảm
- Dữ liệu BHYT của bệnh nhân được ghi nhận
- Phiếu cấp phát có thể in ra để lưu hồ sơ

__Xử lý ngoại lệ:__

- Vật tư sắp hết hạn được dùng để cấp phát \(FEFO\): hệ thống thông báo cho điều dưỡng về hạn dùng

## 3\.4 Nhóm Use Case – Kiểm Kê & Truy Xuất

### UC\-22 – Lập Kế Hoạch và Thực Hiện Kiểm Kê

__Mã Use Case__

UC\-22

__Tên Use Case__

Lập Kế Hoạch và Thực Hiện Kiểm Kê

__Actor chính__

SC\-MANAGER \(lập kế hoạch\), SC\-STOREKEEPER \(thực hiện\), EXT\-SCANNER \(hỗ trợ\)

__Mô tả tóm tắt__

Quản lý lập kế hoạch kiểm kê định kỳ\. Thủ kho thực hiện đếm thực tế, nhập số liệu vào hệ thống để đối chiếu với số liệu sổ sách, xử lý chênh lệch\.

__Điều kiện tiên quyết__

Kho có tồn kho trong sổ sách; Quản lý có quyền tạo phiếu kiểm kê; Thiết bị PDA đã được cấu hình

__Luồng chính \(Main Flow\):__

1. 1\. SC\-MANAGER tạo Phiếu Kiểm Kê, chọn kho/khu vực, đặt ngày kiểm kê
2. 2\. Hệ thống tự động tạo danh sách vật tư cần kiểm kê từ tồn kho sổ sách \(ẩn số lượng tồn\)
3. 3\. SC\-MANAGER phân công thủ kho và in/gửi danh sách lên PDA
4. 4\. Thủ kho đến từng vị trí, scan bin location, scan vật tư, nhập số lượng thực đếm
5. 5\. Nhập thêm thông tin lô và hạn dùng nếu cần
6. 6\. Sau khi hoàn thành đếm, submit kết quả
7. 7\. Hệ thống so sánh số liệu thực tế vs sổ sách, hiển thị danh sách chênh lệch
8. 8\. SC\-MANAGER xem xét và phê duyệt điều chỉnh: tạo Stock Reconciliation Entry

__Luồng thay thế \(Alternative Flow\):__

- 4a\. Thủ kho tìm thấy vật tư không có trong danh sách \(hàng lạc\): ghi nhận thêm vào phiếu
- 7a\. Chênh lệch > ngưỡng cho phép \(VD: >5%\): hệ thống yêu cầu kiểm kê lại lần 2
- 8a\. Nguyên nhân chênh lệch do hao hụt/mất mát: ghi nhận lý do và chuyển sang UC\-23

__Điều kiện hậu \(Post\-condition\):__

- Stock Reconciliation Entry được tạo và phê duyệt
- Tồn kho sổ sách khớp với thực tế
- Báo cáo kiểm kê được lưu để kiểm toán

__Xử lý ngoại lệ:__

- Phiếu kiểm kê bị lock sau khi submit: không cho phép sửa, chỉ quản lý mới có quyền mở khóa nếu cần

### UC\-14 – Xử Lý Product Recall Theo Số Lô

__Mã Use Case__

UC\-14

__Tên Use Case__

Xử Lý Product Recall Theo Số Lô

__Actor chính__

SC\-MANAGER \(chính\), SC\-STOREKEEPER \(thực hiện\)

__Mô tả tóm tắt__

Khi nhận được thông báo thu hồi sản phẩm \(recall\) từ NCC hoặc cơ quan quản lý, quản lý kho thực hiện truy vết và cách ly toàn bộ lô hàng bị ảnh hưởng\.

__Điều kiện tiên quyết__

Có thông tin số lô cần thu hồi; SC\-MANAGER đã đăng nhập hệ thống

__Luồng chính \(Main Flow\):__

1. 1\. SC\-MANAGER vào module M10 \(Truy xuất\), nhập số lô bị recall
2. 2\. Hệ thống tìm kiếm toàn bộ vị trí của lô hàng: tồn kho các kho, đã cấp phát, đã sử dụng
3. 3\. Hệ thống hiển thị báo cáo truy xuất: số lượng còn tồn, số lượng đã cấp phát \(kèm khoa/bệnh nhân\)
4. 4\. SC\-MANAGER khởi tạo lệnh Recall: hệ thống tự động khóa toàn bộ tồn kho của lô này
5. 5\. Hệ thống gửi thông báo đến tất cả kho và khoa phòng đang có lô hàng này
6. 6\. Thủ kho các kho thực hiện cách ly vật tư vào khu vực kiểm dịch
7. 7\. SC\-MANAGER ghi nhận kết quả xử lý: trả NCC, tiêu hủy, hoặc chờ hướng dẫn thêm

__Luồng thay thế \(Alternative Flow\):__

- 2a\. Lô hàng không tìm thấy trong hệ thống: thông báo lỗi, kiểm tra lại số lô nhập vào
- 4a\. Một phần lô đã sử dụng cho bệnh nhân: hệ thống liệt kê danh sách bệnh nhân để thông báo lâm sàng

__Điều kiện hậu \(Post\-condition\):__

- Tất cả tồn kho của lô bị recall đã được cách ly \(không thể xuất kho\)
- Báo cáo recall đầy đủ được lưu trữ
- Thông báo đã gửi đến tất cả bên liên quan

__Xử lý ngoại lệ:__

- Lô hàng đã sử dụng hết: hệ thống vẫn ghi nhận recall và tạo báo cáo để lưu hồ sơ an toàn

# 4\. QUAN HỆ GIỮA CÁC USE CASE

## 4\.1 Quan Hệ <<include>> \(Bao Gồm Bắt Buộc\)

__Use Case chính__

__Include__

__Lý do bắt buộc__

UC\-07 Tiếp nhận hàng

UC\-11 Scan barcode

Mọi lần nhập kho đều phải xác nhận danh tính vật tư

UC\-05 Tạo Release Order

UC\-06 Phê duyệt

Mọi RO đều qua workflow phê duyệt \(dù tự động hay thủ công\)

UC\-17/18 Cấp phát

UC\-13 FEFO

Mọi giao dịch xuất kho đều áp dụng FEFO tự động

UC\-20 Đối chiếu 3 chiều

UC\-21 Thanh toán

Phải đối chiếu thành công trước khi tạo lệnh thanh toán

## 4\.2 Quan Hệ <<extend>> \(Mở Rộng Có Điều Kiện\)

__Use Case cơ sở__

__Extends__

__Điều kiện kích hoạt__

UC\-07 Tiếp nhận hàng

UC\-08 Từ chối hàng

Chỉ khi QC Fail hoặc hàng không đúng quy cách

UC\-07 Tiếp nhận hàng

UC\-09 Partial Receipt

Chỉ khi số lượng thực tế < PO

UC\-12 Quản lý lô/hạn dùng

UC\-14 Product Recall

Chỉ khi nhận được thông báo recall chính thức

UC\-22 Kiểm kê

UC\-23 Xử lý chênh lệch

Chỉ khi có sự chênh lệch giữa thực tế và sổ sách

─────────────────────────────────────────────────────────────────────────────

Tài liệu Use Case này cần được xem xét và xác nhận bởi đại diện từng nhóm người dùng\. Các Use Case Diagram dạng đồ họa \(UML\) sẽ được bổ sung trong giai đoạn thiết kế giao diện \(Phase 3\)\.

