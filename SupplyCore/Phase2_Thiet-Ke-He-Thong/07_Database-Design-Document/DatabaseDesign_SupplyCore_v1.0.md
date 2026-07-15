__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung Ứng Vật Tư Y Tế

__THIẾT KẾ CƠ SỞ DỮ LIỆU__

Database Design Document

Phiên bản: v1\.0  |  Ngày: 05/05/2026

Tài liệu: SC\-PH2\-DB\-007  |  Phase 2 – Thiết kế hệ thống

# __1\. THÔNG TIN TÀI LIỆU__

__Thuộc tính__

__Giá trị__

__Tên tài liệu__

Database Design Document – SupplyCore

__Mã tài liệu__

SC\-PH2\-DB\-007

__Phiên bản__

v1\.0

__DBMS__

MariaDB 10\.6\+ \(InnoDB engine\)

__ORM__

Frappe ORM \(Python\) – tự động sinh SQL từ Doctype definition

__Custom Doctypes__

9 Doctypes mới \+ ERPNext standard extension

__Tổng bảng ước tính__

> 200 bảng \(ERPNext standard ~180 \+ SupplyCore custom ~20\)

__Tác giả__

Solution Architect & DBA – SupplyCore Project

__Trạng thái__

Đã phê duyệt – Phase 2 Final

# __2\. NGUYÊN TẮC THIẾT KẾ DATABASE__

## __2\.1 Frappe ORM và quản lý schema__

Frappe Framework quản lý database schema tự động từ Doctype definition:

• Mỗi Doctype → 1 table trong MariaDB \(tên: tab \+ DocType name, ví dụ: tabPurchase Order\)

• Child Table Doctype → table riêng, liên kết qua parentfield và parenttype

• Schema migration tự động khi chạy bench migrate

• Không viết DDL thủ công – mọi schema thay đổi qua Doctype definition

## __2\.2 Cột chuẩn của mọi Doctype \(Frappe standard\)__

__Cột__

__Kiểu dữ liệu__

__Mô tả__

name

__VARCHAR\(140\)__

Primary key – document ID / auto\-name

owner

__VARCHAR\(140\)__

User tạo document \(FK → tabUser\.name\)

creation

__DATETIME__

Thời điểm tạo \(UTC\)

modified

__DATETIME__

Thời điểm sửa cuối

modified\_by

__VARCHAR\(140\)__

User sửa cuối

docstatus

__INT\(1\)__

0=Draft, 1=Submitted, 2=Cancelled

idx

__INT\(8\)__

Thứ tự trong list view

\_user\_tags

__TEXT__

Tags do user gán

\_comments

__TEXT__

JSON array comments

\_assign

__TEXT__

Assigned to \(JSON\)

\_liked\_by

__TEXT__

Users đã like

# __3\. CUSTOM DOCTYPE SCHEMAS__

Dưới đây là schema chi tiết của 9 Doctype tùy chỉnh trong SupplyCore app:

__Framework Contract \(Hợp đồng Khung\)__

Lưu trữ thông tin hợp đồng khung với nhà cung cấp\. Là cơ sở để tạo Release Order và Purchase Order\.

__Fieldname__

__Label \(VN\)__

__Fieldtype__

__Options/Link__

__Reqd__

__Mô tả__

name

Mã hợp đồng

__Data__

—

✓

Auto\-name: SC\-FC\-YYYY\-NNNNN

supplier

Nhà cung cấp

__Link__

Supplier

✓

FK → ERPNext Supplier

contract\_number

Số hợp đồng

__Data__

—

✓

Số hợp đồng chính thức

contract\_date

Ngày ký

__Date__

—

✓

valid\_from

Ngày hiệu lực

__Date__

—

✓

valid\_to

Ngày hết hạn

__Date__

—

✓

Trigger alert 30 ngày trước

total\_value

Giá trị hợp đồng

__Currency__

—

✓

VND

used\_value

Giá trị đã sử dụng

__Currency__

—

✓

Computed từ Release Orders

remaining\_value

Giá trị còn lại

__Currency__

—

✓

= total\_value \- used\_value

payment\_terms

Điều khoản thanh toán

__Link__

Payment Terms

✓

FK → ERPNext Payment Terms

status

Trạng thái

__Select__

Draft
Active
Expired
Terminated

✓

Workflow driven

workflow\_state

Trạng thái phê duyệt

__Link__

Workflow State

✓

Managed by Frappe Workflow

items

Danh mục vật tư

__Table__

FC Item

✓

Child table: vật tư \+ đơn giá \+ SL max

attachment

Tệp đính kèm

__Attach__

—

✓

Scan hợp đồng PDF

remarks

Ghi chú

__Small Text__

—

✓

__FC Item \(Dòng Hợp đồng Khung\)__

Child table của Framework Contract, lưu danh mục vật tư, đơn giá và số lượng tối đa trong hợp đồng\.

__Fieldname__

__Label \(VN\)__

__Fieldtype__

__Options/Link__

__Reqd__

__Mô tả__

item\_code

Mã vật tư

__Link__

Item

✓

FK → ERPNext Item

item\_name

Tên vật tư

__Data__

—

✓

Auto\-fetch từ Item

uom

Đơn vị tính

__Link__

UOM

✓

Đơn vị trong hợp đồng \(mua\)

contract\_qty

SL hợp đồng

__Float__

—

✓

Số lượng tối đa theo hợp đồng

ordered\_qty

SL đã đặt

__Float__

—

✓

Computed từ PO liên kết

remaining\_qty

SL còn lại

__Float__

—

✓

= contract\_qty \- ordered\_qty

unit\_price

Đơn giá

__Currency__

—

✓

VND / UOM

total\_amount

Thành tiền

__Currency__

—

✓

= contract\_qty × unit\_price

__Release Order \(Lệnh Gọi Hàng\)__

Lệnh gọi hàng dựa trên hợp đồng khung\. Tạo từ Framework Contract, sau phê duyệt chuyển thành Purchase Order\.

__Fieldname__

__Label \(VN\)__

__Fieldtype__

__Options/Link__

__Reqd__

__Mô tả__

name

Mã Release Order

__Data__

—

✓

Auto\-name: SC\-RO\-YYYY\-NNNNN

framework\_contract

Hợp đồng khung

__Link__

Framework Contract

✓

FK → Framework Contract

supplier

Nhà cung cấp

__Link__

Supplier

✓

Auto\-fetch từ FC

release\_date

Ngày lệnh

__Date__

—

✓

required\_by

Ngày cần giao

__Date__

—

✓

purchase\_order

Purchase Order

__Link__

Purchase Order

✓

FK sau khi convert

status

Trạng thái

__Select__

Draft
Approved
Converted
Cancelled

✓

items

Danh mục

__Table__

RO Item

✓

Chi tiết vật tư cần gọi

total\_amount

Tổng giá trị

__Currency__

—

✓

Sum of items

remarks

Ghi chú

__Small Text__

—

✓

__Patient Dispensing \(Phiếu Cấp Phát Bệnh Nhân\)__

Ghi nhận vật tư được cấp phát cho từng bệnh nhân cụ thể\. Liên kết với Stock Entry và hồ sơ bệnh nhân \(qua mã BN\)\.

__Fieldname__

__Label \(VN\)__

__Fieldtype__

__Options/Link__

__Reqd__

__Mô tả__

name

Mã phiếu

__Data__

—

✓

Auto\-name: SC\-PD\-YYYY\-NNNNN

patient\_id

Mã bệnh nhân

__Data__

—

✓

Mã BN từ hệ thống bệnh viện

patient\_name

Tên bệnh nhân

__Data__

—

✓

bhyt\_card

Số thẻ BHYT

__Data__

—

✓

Số thẻ BHYT BN \(10 ký tự\)

ward

Khoa phòng

__Link__

Department

✓

FK → ERPNext Department

dispensing\_date

Ngày cấp phát

__Date__

—

✓

stock\_entry

Phiếu xuất kho

__Link__

Stock Entry

✓

FK → Stock Entry Issue

items

Vật tư

__Table__

PD Item

✓

Chi tiết vật tư cấp phát

total\_cost

Tổng chi phí

__Currency__

—

✓

VND

bhyt\_covered

BHYT chi trả

__Currency__

—

✓

VND

patient\_pays

Bệnh nhân tự trả

__Currency__

—

✓

= total\_cost \- bhyt\_covered

status

Trạng thái

__Select__

Draft
Submitted
Cancelled

✓

__PD Item \(Dòng Cấp Phát BN\)__

Child table của Patient Dispensing, lưu từng vật tư, số lượng, lô hàng và chi phí BHYT\.

__Fieldname__

__Label \(VN\)__

__Fieldtype__

__Options/Link__

__Reqd__

__Mô tả__

item\_code

Mã vật tư

__Link__

Item

✓

FK → ERPNext Item

item\_name

Tên vật tư

__Data__

—

✓

Auto\-fetch

qty

Số lượng

__Float__

—

✓

uom

Đơn vị

__Link__

UOM

✓

Đơn vị sử dụng

batch\_no

Số lô

__Link__

Batch

✓

FK → ERPNext Batch

unit\_cost

Đơn giá

__Currency__

—

✓

Lấy từ Stock Ledger

total\_cost

Thành tiền

__Currency__

—

✓

= qty × unit\_cost

bhyt\_code

Mã BHYT

__Link__

BHYT Code Config

✓

FK → BHYT Code Config

bhyt\_group

Nhóm BHYT

__Select__

N01
N02
N03
N04
N05
N06
N07
N08
N09

✓

Auto\-fetch từ BHYT Code

bhyt\_rate

Tỉ lệ BHYT \(%\)

__Percent__

—

✓

% BHYT thanh toán

bhyt\_amount

BHYT chi trả

__Currency__

—

✓

= total\_cost × bhyt\_rate / 100

__BHYT Code Config \(Cấu hình Mã BHYT\)__

Bảng cấu hình mã BHYT cho vật tư\. Tham số hóa hoàn toàn – không hard\-code\. Hỗ trợ 1\-N mã BHYT cho 1 vật tư\.

__Fieldname__

__Label \(VN\)__

__Fieldtype__

__Options/Link__

__Reqd__

__Mô tả__

name

Mã config

__Data__

—

✓

Auto\-name: SC\-BHYT\-NNNNN

item\_code

Mã vật tư

__Link__

Item

✓

FK → ERPNext Item

bhyt\_code

Mã BHYT

__Data__

—

✓

Mã theo quy định BYT

bhyt\_group

Nhóm BHYT

__Select__

N01
N02
N03
N04
N05
N06
N07
N08
N09

✓

bhyt\_name

Tên BHYT

__Data__

—

✓

Tên theo danh mục BYT

payment\_rate

Tỉ lệ thanh toán \(%\)

__Percent__

—

✓

Thay đổi theo TT BYT

effective\_from

Hiệu lực từ

__Date__

—

✓

effective\_to

Hiệu lực đến

__Date__

—

✓

NULL = còn hiệu lực

is\_active

Đang áp dụng

__Check__

—

✓

1 = active

remarks

Ghi chú

__Small Text__

—

✓

Căn cứ pháp lý \(TT số\.\.\.\)

__Dispensing Request \(Phiếu Yêu Cầu Cấp Phát\)__

Phiếu yêu cầu lĩnh vật tư từ khoa phòng gửi kho\. Sau phê duyệt chuyển thành Stock Entry Issue\.

__Fieldname__

__Label \(VN\)__

__Fieldtype__

__Options/Link__

__Reqd__

__Mô tả__

name

Mã yêu cầu

__Data__

—

✓

Auto\-name: SC\-DR\-YYYY\-NNNNN

department

Khoa phòng

__Link__

Department

✓

FK → ERPNext Department

requested\_by

Người yêu cầu

__Link__

User

✓

request\_date

Ngày yêu cầu

__Date__

—

✓

required\_by

Ngày cần

__Date__

—

✓

purpose

Mục đích

__Select__

Routine
Urgent
Patient\-specific

✓

patient\_id

Mã BN \(nếu có\)

__Data__

—

✓

Optional

items

Danh mục

__Table__

DR Item

✓

Vật tư cần lĩnh

status

Trạng thái

__Select__

Draft
Pending
Approved
Issued
Cancelled

✓

Workflow

stock\_entry

Phiếu xuất

__Link__

Stock Entry

✓

Liên kết sau khi xuất

__Recall Notice \(Thông Báo Thu Hồi\)__

Quản lý quy trình thu hồi vật tư khi phát hiện sự cố chất lượng hoặc nhận thông báo từ nhà sản xuất\.

__Fieldname__

__Label \(VN\)__

__Fieldtype__

__Options/Link__

__Reqd__

__Mô tả__

name

Mã thu hồi

__Data__

—

✓

Auto\-name: SC\-RCL\-YYYY\-NNNNN

recall\_date

Ngày thu hồi

__Date__

—

✓

item\_code

Vật tư

__Link__

Item

✓

batch\_no

Số lô

__Link__

Batch

✓

Lô bị thu hồi

recall\_reason

Lý do

__Small Text__

—

✓

recall\_type

Loại thu hồi

__Select__

Voluntary
Mandatory
Precautionary

✓

affected\_qty

SL bị ảnh hưởng

__Float__

—

✓

Tính toán từ trace

recovered\_qty

SL đã thu hồi

__Float__

—

✓

Cập nhật khi thu hồi

status

Trạng thái

__Select__

Open
In Progress
Completed

✓

resolution

Xử lý

__Select__

Return to Supplier
Destroy
Pending

✓

resolution\_date

Ngày xử lý

__Date__

—

✓

__SupplyCore Settings \(Cấu hình Hệ thống\)__

Single\-record Doctype lưu tất cả cấu hình vận hành của SupplyCore: ngưỡng cảnh báo, workflow rules, format\.

__Fieldname__

__Label \(VN\)__

__Fieldtype__

__Options/Link__

__Reqd__

__Mô tả__

po\_approval\_threshold

Ngưỡng duyệt PO \(VND\)

__Currency__

—

✓

PO ≥ ngưỡng → cần Lãnh đạo duyệt

expiry\_alert\_days\_critical

Cảnh báo hết hạn \(đỏ, ngày\)

__Int__

—

✓

Mặc định: 30 ngày

expiry\_alert\_days\_warning

Cảnh báo hết hạn \(vàng, ngày\)

__Int__

—

✓

Mặc định: 90 ngày

default\_safety\_stock\_pct

Safety stock mặc định \(%\)

__Percent__

—

✓

% tiêu thụ tháng làm safety stock

contract\_expiry\_alert\_days

Cảnh báo HĐ hết hạn \(ngày\)

__Int__

—

✓

Mặc định: 30 ngày

fefo\_strict\_mode

FEFO nghiêm ngặt

__Check__

—

✓

1 = block override, 0 = warn only

default\_warehouse

Kho tổng mặc định

__Link__

Warehouse

✓

bhyt\_auto\_calculate

Tự động tính BHYT

__Check__

—

✓

1 = tự động khi save PD

email\_alert\_recipients

Email nhận cảnh báo

__Small Text__

—

✓

Phân cách bằng dấu phẩy

audit\_log\_retention\_days

Lưu audit log \(ngày\)

__Int__

—

✓

Mặc định: 2555 \(7 năm\)

# __4\. BẢNG ERPNEXT CHUẨN SỬ DỤNG__

SupplyCore tận dụng các Doctype sau của ERPNext \(extend qua custom fields, không sửa core\):

__ERPNext Doctype__

__Dùng cho__

__Ghi chú tùy chỉnh__

__Supplier__

Quản lý NCC

Thêm custom fields: NCC type, blacklist flag, rating

__Item__

Danh mục vật tư

Thêm: has\_bhyt, use\_uom, buy\_uom, uom\_conversion\_factor

__Purchase Order__

Đặt hàng

Liên kết Framework Contract qua custom field

__Purchase Receipt__

Tiếp nhận

Trigger auto\-create Quality Inspection on\_submit

__Quality Inspection__

Kiểm tra QC

Template QC theo Item Group \(custom field\)

__Stock Entry__

Xuất/nhập/chuyển kho

Loại Material Issue: link Patient Dispensing

__Batch__

Quản lý lô

Thêm: manufacturer, manufacture\_date; expiry\_date \(built\-in\)

__Warehouse__

Quản lý kho

3\-cấp: Parent Warehouse; thêm: bin\_enabled, ward\_link

__Purchase Invoice__

Hóa đơn NCC

3\-way match validation qua custom validate

__Payment Entry__

Thanh toán

Approval threshold qua custom workflow

__GL Entry__

Sổ cái

Immutable – không custom; chỉ read

__Stock Ledger Entry__

Nhật ký kho

Immutable – không custom; chỉ read

__Department__

Khoa phòng

Dùng để phân cấp, link Warehouse & Permission

__UOM / UOM Conversion__

Đơn vị tính

Cấu hình buy\_uom ↔ use\_uom conversion

# __5\. QUAN HỆ GIỮA CÁC DOCTYPE__

## __5\.1 Quan hệ chính__

__Doctype cha__

__Quan hệ__

__Doctype con/liên kết__

__Mô tả__

__Framework Contract__

1\-N

__FC Item \(child\)__

Mỗi HĐ có nhiều dòng vật tư

__Framework Contract__

1\-N

__Release Order__

1 HĐ có nhiều lệnh gọi hàng

__Release Order__

1\-1

__Purchase Order__

Sau duyệt RO → convert thành PO

__Purchase Order__

1\-N

__Purchase Receipt__

1 PO nhận nhiều lần \(partial\)

__Purchase Receipt__

1\-1

__Quality Inspection__

Auto\-create QI khi tạo PR

__Purchase Receipt__

1\-N

__Batch__

Mỗi item trong PR → 1\+ batch

__Stock Entry \(Issue\)__

1\-1

__Patient Dispensing__

1 xuất kho → 1 phiếu cấp phát BN

__Patient Dispensing__

1\-N

__PD Item \(child\)__

Mỗi phiếu có nhiều vật tư

__PD Item__

N\-1

__BHYT Code Config__

Nhiều phiếu dùng cùng cấu hình BHYT

__Item__

1\-N

__BHYT Code Config__

1 vật tư có 1\-N mã BHYT

__Dispensing Request__

1\-1

__Stock Entry \(Issue\)__

DR sau phê duyệt → tạo Stock Entry

__Batch__

1\-N

__Stock Ledger Entry__

Mỗi batch có nhiều giao dịch SLE

__Recall Notice__

N\-1

__Batch__

Thu hồi theo lô

# __6\. INDEXING STRATEGY__

## __6\.1 Index khuyến nghị cho custom tables__

__Bảng__

__Index trên cột__

__Lý do__

\`tabFramework Contract\`

supplier, valid\_to, status

Tra cứu HĐ theo NCC, lọc sắp hết hạn

\`tabRelease Order\`

framework\_contract, status

Join với FC để tính used\_value

\`tabPatient Dispensing\`

patient\_id, dispensing\_date, ward

Tra cứu chi phí theo BN, theo khoa, theo ngày

\`tabPD Item\`

item\_code, bhyt\_code

Tổng hợp chi phí BHYT theo vật tư

\`tabBHYT Code Config\`

item\_code, is\_active, effective\_from

Lookup nhanh mã BHYT hiện hành

\`tabBatch\`

item, expiry\_date

FEFO sort: ORDER BY expiry\_date ASC

\`tabStock Ledger Entry\`

item\_code, warehouse, batch\_no, posting\_date

Trace và balance queries – Frappe đã có index

\`tabRecall Notice\`

batch\_no, status

Tra cứu recall theo lô

## __6\.2 Lưu ý hiệu năng__

• Stock Ledger Entry là bảng lớn nhất – không thêm index thừa, dùng ERPNext built\-in reporting

• Batch traceability query dùng recursive CTE hoặc application\-level traversal \(Frappe get\_value chain\)

• Báo cáo nặng chạy qua Report Builder với caching Redis 5 phút

• MariaDB query cache enable; innodb\_buffer\_pool\_size = 70% RAM server

# __7\. QUY ƯỚC ĐẶT TÊN__

__Doctype__

__Format__

__Ví dụ__

__Ghi chú__

__Framework Contract__

SC\-FC\-YYYY\-NNNNN

SC\-FC\-2026\-00001

N = 5 chữ số, reset mỗi năm

__Release Order__

SC\-RO\-YYYY\-NNNNN

SC\-RO\-2026\-00001

__Patient Dispensing__

SC\-PD\-YYYY\-NNNNN

SC\-PD\-2026\-00001

__Dispensing Request__

SC\-DR\-YYYY\-NNNNN

SC\-DR\-2026\-00001

__Recall Notice__

SC\-RCL\-YYYY\-NNNNN

SC\-RCL\-2026\-00001

__BHYT Code Config__

SC\-BHYT\-NNNNN

SC\-BHYT\-00001

Không reset theo năm

__Batch ID \(nội bộ\)__

\[ItemCode\]\-YYYYMM\-NNN

VT001\-202601\-001

Custom batch naming

__Purchase Order__

PO\-YYYY\-NNNNN

PO\-2026\-00001

ERPNext standard naming

__Purchase Receipt__

MAT\-REC\-YYYY\-NNNNN

MAT\-REC\-2026\-00001

ERPNext standard naming

__Stock Entry__

STE\-YYYY\-NNNNN

STE\-2026\-00001

ERPNext standard naming

# __8\. CHÍNH SÁCH LƯU TRỮ DỮ LIỆU__

__Loại dữ liệu__

__Thời gian lưu__

__Ghi chú__

__Giao dịch kho \(SLE, GL\)__

Vĩnh viễn

Immutable – không được xóa theo quy định kế toán

__Purchase Order/Receipt__

≥ 10 năm

Theo Luật Kế toán VN

__Patient Dispensing__

≥ 10 năm

Liên quan hồ sơ bệnh án; tham chiếu quyết toán BHYT

__Audit Log__

≥ 7 năm

SupplyCore Settings: audit\_log\_retention\_days = 2555

__QC Records__

≥ 5 năm

Theo quy định kiểm soát chất lượng vật tư y tế

__Recall Records__

≥ 10 năm

Truy xuất trách nhiệm

__User Activity Log__

≥ 2 năm

Security audit

__Temp/Draft documents__

90 ngày

Xóa draft cũ bằng scheduled job

__Cache \(Redis\)__

Session: 24h
Report cache: 5 phút

TTL cấu hình trong Frappe settings

# __9\. BACKUP VÀ PHỤC HỒI__

• Full backup hàng ngày: bench \-\-site hospital\.local backup \-\-with\-files

• Incremental WAL backup theo giờ \(nếu dùng MariaDB binlog replication\)

• Backup được mã hóa AES\-256 và lưu off\-site \(S3 hoặc NAS riêng\)

• Test restore hàng tháng theo quy trình DR; RPO ≤ 1h, RTO ≤ 4h

• bench restore dùng để khôi phục site từ backup

