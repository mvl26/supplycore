__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung Ứng Vật Tư Y Tế

__TÀI LIỆU API – API DOCUMENTATION__

Phiên bản: v1\.0  |  Ngày: 05/05/2026

Tài liệu: SC\-PH2\-API\-009  |  Phase 2 – Thiết kế hệ thống

# __1\. THÔNG TIN TÀI LIỆU__

__Thuộc tính__

__Giá trị__

__Tên tài liệu__

API Documentation – SupplyCore

__Mã tài liệu__

SC\-PH2\-API\-009

__Base URL \(dev\)__

http://hospital\.local:8000

__Base URL \(prod\)__

https://supplycore\.hospital\.vn

__API Version__

v1 \(Frappe standard REST\)

__Format__

JSON \(application/json\)

__Authentication__

Session Cookie \+ API Key/Secret

__Rate Limiting__

100 req/min per user \(Nginx level\)

__Tác giả__

Backend Team – SupplyCore Project

# __2\. XÁC THỰC \(AUTHENTICATION\)__

## __2\.1 Session\-based \(Browser\)__

Dùng cho web application – tự động xử lý qua Frappe login page:

POST /api/method/login

Content\-Type: application/x\-www\-form\-urlencoded

usr=admin@hospital\.vn&pwd=password123

Response: Set\-Cookie: sid=<session\_id>; HttpOnly; Secure

## __2\.2 API Key/Secret \(Integration\)__

Dung cho tich hop HIS/EMR, scheduled tasks, server\-to\-server:

GET /api/resource/Framework Contract

Authorization: token <api\_key>:<api\_secret>

\# Tao API key trong Frappe: User \-> API Access \-> Generate Keys

## __2\.3 HTTP Response Codes__

__Code__

__Status__

__Truong hop__

__200__

__OK__

Thanh cong

__201__

__Created__

Tao moi document thanh cong

__400__

__Bad Request__

Thieu tham so bat buoc, du lieu khong hop le

__401__

__Unauthorized__

Chua dang nhap hoac session het han

__403__

__Forbidden__

Khong co quyen truy cap resource

__404__

__Not Found__

Document khong ton tai

__409__

__Conflict__

Trung ban ghi \(duplicate\)

__500__

__Server Error__

Loi he thong, xem Error Log

# __3\. FRAPPE STANDARD REST API__

Frappe tu dong sinh CRUD endpoints cho moi Doctype\. Khong can code them:

## __3\.1 List Resources__

__GET__ 

__GET /api/resource/\{DocType\}?filters=\[\[\.\.\.\]\]&fields=\[\.\.\.\]&limit=20&order\_by=creation desc__

__Mô tả__

Lay danh sach documents theo bo loc\. Frappe REST standard – ap dung cho moi Doctype\.

__Xác thực__

Session cookie hoac API Key

__Tham số / Body__

filters \(JSON\): \[\["status","=","Active"\],\["supplier","=","SUP\-001"\]\]
fields \(JSON\): \["name","supplier","valid\_to","status"\]
limit \(int\): So luong ket qua tra ve \(default 20, max 500\)
order\_by \(string\): Truong va chieu sap xep

__Response mẫu__

\{"data": \[\{"name":"SC\-FC\-2026\-00001","supplier":"Cong ty A","valid\_to":"2026\-12\-31","status":"Active"\}, \.\.\.\]\}

__Mã lỗi__

401: Session expired
403: No read permission on DocType

## __3\.2 Get Single Document__

__GET__ 

__GET /api/resource/\{DocType\}/\{name\}__

__Mô tả__

Lay chi tiet 1 document bao gom tat ca fields va child tables\.

__Xác thực__

Session cookie hoac API Key

__Tham số / Body__

name \(path\): Ten document can lay \(e\.g\. SC\-FC\-2026\-00001\)

__Response mẫu__

\{"data": \{"name":"SC\-FC\-2026\-00001","supplier":"Cong ty A","valid\_from":"2026\-01\-01","valid\_to":"2026\-12\-31","total\_value":500000000,"items":\[\.\.\.\]\}\}

__Mã lỗi__

404: Document not found
403: No read permission

## __3\.3 Create Document__

__POST__ 

__POST /api/resource/\{DocType\}__

__Mô tả__

Tao moi document\. Tra ve document da tao voi name duoc auto\-generate\.

__Xác thực__

Session cookie \(can quyen Create tren DocType\)

__Tham số / Body__

Body JSON: \{"supplier":"Cong ty A","contract\_date":"2026\-05\-01","valid\_from":"2026\-05\-01","valid\_to":"2026\-12\-31","total\_value":500000000\}

__Response mẫu__

\{"data": \{"name":"SC\-FC\-2026\-00001","supplier":"Cong ty A","docstatus":0,\.\.\.\}\}

__Mã lỗi__

400: Missing mandatory fields
409: Duplicate record

# __4\. CUSTOM SUPPLYCORE APIs__

## __4\.1 FEFO – Get Suggested Batches__

__POST__ 

__POST /api/method/supplycore\.api\.fefo\.get\_suggested\_batches__

__Mô tả__

Tra ve danh sach batch duoc goi y theo nguyen tac FEFO \(First Expired First Out\) cho vat tu va kho cu the\.

__Xác thực__

Session cookie hoac API Key

__Tham số / Body__

Body JSON:
\{"item\_code": "VT\-BANDAGE\-001", "warehouse": "Main Store \- H", "qty": 50, "uom": "Piece"\}

__Response mẫu__

\{"message": \[\{"batch\_no":"VT\-BANDAGE\-001\-202601\-001","expiry\_date":"2026\-06\-30","available\_qty":80,"suggested\_qty":50\}, \{"batch\_no":"VT\-BANDAGE\-001\-202603\-001","expiry\_date":"2026\-09\-30","available\_qty":200,"suggested\_qty":0\}\]\}

__Mã lỗi__

400: item\_code or warehouse missing
404: No batch available for item

## __4\.2 BHYT – Calculate Cost__

__POST__ 

__POST /api/method/supplycore\.api\.bhyt\.calculate\_cost__

__Mô tả__

Tinh chi phi BHYT cho danh sach vat tu\. Lay ty le tu BHYT Code Config hien hanh\.

__Xác thực__

Session cookie hoac API Key

__Tham số / Body__

Body JSON:
\{"items": \[\{"item\_code":"VT\-GLOVE\-001","qty":10,"uom":"Pair","unit\_cost":15000\}\], "bhyt\_card":"1234567890"\}

__Response mẫu__

\{"message": \{"items": \[\{"item\_code":"VT\-GLOVE\-001","total\_cost":150000,"bhyt\_group":"N05","bhyt\_rate":80,"bhyt\_amount":120000,"patient\_pays":30000\}\], "total\_cost":150000,"bhyt\_covered":120000,"patient\_pays":30000\}\}

__Mã lỗi__

400: item\_code missing
422: No active BHYT config found for item \(auto\-fallback to 0%\)

## __4\.3 Stock – Batch Trace__

__GET__ 

__GET /api/method/supplycore\.api\.stock\.get\_batch\_trace?batch\_no=VT001\-202601\-001__

__Mô tả__

Truy xuat toan bo lich su vong doi cua 1 lo hang: tu NCC den kho den cap phat\.

__Xác thực__

Session cookie; can quyen SC\-MANAGER tro len

__Tham số / Body__

batch\_no \(query param\): Ma lo hang \(Batch ID noi bo hoac so lo NCC\)

__Response mẫu__

\{"message": \{"batch\_no":"VT001\-202601\-001","item\_code":"VT\-GLOVE\-001","expiry\_date":"2026\-06\-30","source":\{"supplier":"Cong ty A","purchase\_receipt":"MAT\-REC\-2026\-00001","received\_date":"2026\-01\-15","qc\_result":"Accepted"\},"movements":\[\{"type":"Transfer","from":"Main Store","to":"Ward A Store","date":"2026\-02\-01","qty":50\},\{"type":"Issue","to\_ward":"Ward A","patient\_id":"BN\-001","date":"2026\-02\-10","qty":10\}\],"remaining\_qty":40\}\}

__Mã lỗi__

404: Batch not found
403: Insufficient permission

## __4\.4 WMS – Scan Barcode__

__POST__ 

__POST /api/method/supplycore\.api\.wms\.scan\_barcode__

__Mô tả__

Xu ly ket qua quet barcode tu thiet bi PDA hoac dien thoai\. Tra ve thong tin vat tu, lo, bin tuong ung\.

__Xác thực__

Session cookie \(SC\-STOREKEEPER\)

__Tham số / Body__

Body JSON:
\{"barcode": "8938512345678", "context": "receipt"\}

__Response mẫu__

\{"message": \{"type":"item","item\_code":"VT\-BANDAGE\-001","item\_name":"Bang y te","uom":"Roll","has\_batch":true,"warehouse\_suggestion":"Main Store \- Shelf A1"\}\}

__Mã lỗi__

404: Barcode not recognized
400: Invalid barcode format

## __4\.5 Dashboard – KPI Data__

__GET__ 

__GET /api/method/supplycore\.api\.kpi\.get\_dashboard\_data?warehouse=all&period=this\_month__

__Mô tả__

Tra ve du lieu KPI tong hop cho Dashboard dieu hanh\. Ket qua duoc cache 5 phut trong Redis\.

__Xác thực__

Session cookie; ket qua loc theo User Permission

__Tham số / Body__

warehouse \(query\): 'all' hoac ten kho cu the
period \(query\): 'today','this\_week','this\_month','this\_quarter'

__Response mẫu__

\{"message": \{"stock\_value":1250000000,"pending\_pos":5,"expiring\_soon":12,"low\_stock\_items":3,"monthly\_cost":185000000,"top\_items":\[\{"item":"VT\-GLOVE\-001","qty\_used":1200\}\],"last\_updated":"2026\-05\-05T08:30:00"\}\}

__Mã lỗi__

403: No dashboard permission

## __4\.6 Report – BHYT Summary__

__GET__ 

__GET /api/method/supplycore\.api\.report\.bhyt\_summary?from\_date=2026\-05\-01&to\_date=2026\-05\-31&ward=all__

__Mô tả__

Bao cao tong hop chi phi BHYT theo ky, phan loai theo nhom N01\-N09 va theo khoa phong\.

__Xác thực__

Session cookie \(SC\-ACCOUNTANT tro len\)

__Tham số / Body__

from\_date, to\_date \(query\): Khoang thoi gian bao cao
ward \(query\): 'all' hoac ten khoa cu the

__Response mẫu__

\{"message": \{"period":"2026\-05","total\_cost":85000000,"bhyt\_covered":68000000,"patient\_pays":17000000,"by\_group":\[\{"group":"N05","name":"Vat tu tieu hao","amount":45000000,"bhyt":36000000\},\{"group":"N08","name":"Chi phi khac","amount":40000000,"bhyt":32000000\}\],"by\_ward":\[\{"ward":"Noi","amount":30000000\},\{"ward":"Ngoai","amount":55000000\}\]\}\}

__Mã lỗi__

400: Invalid date range
403: No report access

# __5\. WEBHOOKS – OUTBOUND NOTIFICATIONS__

SupplyCore gui webhook den HIS/EMR khi co su kien quan trong \(cau hinh trong Frappe Webhook\):

__Su kien__

__DocType trigger__

__Payload chinh__

__patient\_dispensing\.submitted__

Patient Dispensing

patient\_id, ward, items\[\], total\_cost, bhyt\_covered, dispensing\_date

__recall\_notice\.submitted__

Recall Notice

batch\_no, item\_code, recall\_reason, affected\_wards\[\]

__stock\_alert\.low\_stock__

Scheduled Task

item\_code, warehouse, current\_qty, reorder\_level

__po\.approved__

Purchase Order

po\_number, supplier, total\_amount, expected\_delivery

__contract\.expiring\_soon__

Scheduled Task

contract\_number, supplier, valid\_to, days\_remaining

## __5\.1 Webhook payload format__

\{

  "event": "patient\_dispensing\.submitted",

  "timestamp": "2026\-05\-05T10:30:00\+07:00",

  "source": "SupplyCore",

  "data": \{

    "name": "SC\-PD\-2026\-00045",

    "patient\_id": "BN\-2026\-00123",

    "ward": "Noi khoa A",

    "dispensing\_date": "2026\-05\-05",

    "total\_cost": 250000,

    "bhyt\_covered": 200000,

    "patient\_pays": 50000

  \}

\}

# __6\. PAGINATION, FILTERING & SORTING__

## __6\.1 Pagination__

\# Phan trang: dung limit va limit\_start

GET /api/resource/Purchase Order?limit=20&limit\_start=40

\# => Lay records 41\-60

\# Response bao gom tong so ban ghi \(neu set with\_comment\_count=1\)

## __6\.2 Filtering syntax__

\# Cac phep so sanh ho tro:

\# "=" , "\!=" , ">" , ">=" , "<" , "<=" , "like" , "not like" , "in" , "not in" , "is" , "is not"

\# Vi du: HĐ con hieu luc, supplier la 'Cong ty A', gia tri > 100tr

GET /api/resource/Framework Contract

  ?filters=\[\["status","=","Active"\],\["supplier","=","Cong ty A"\],\["total\_value",">",100000000\]\]

  &fields=\["name","supplier","valid\_to","total\_value"\]

  &order\_by=valid\_to asc

# __7\. RATE LIMITING & BAO MAT API__

__Bien phap__

__Chinh sach__

__Ghi chu__

__Rate Limiting__

100 req/min/user

Nginx limit\_req; 429 Too Many Requests khi vuot

__HTTPS__

Bat buoc

HTTP bi redirect sang HTTPS; HSTS header

__CORS__

Whitelist domain

Chi chap nhan request tu hospital\.local va prod domain

__API Key Rotation__

Khach hang tu quay

Frappe API key co the thu hoi bat ky luc nao

__Session Timeout__

8 gio khong hoat dong

Frappe session lifetime = 28800 giay

__Input Validation__

Frappe built\-in

SQL injection bao ve boi Frappe ORM parameterized queries

__Audit API calls__

Frappe Error Log

Moi request co Error Log neu co loi; access log Nginx

__IP Whitelist__

Tuy chon

Co the cau hinh IP whitelist cho API key trong Frappe

