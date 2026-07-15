__SUPPLYCORE__

He thong Quan ly Chuoi Cung Ung Vat Tu Y Te

__THIET KE TICH HOP HE THONG – INTEGRATION DESIGN__

Phien ban: v1\.0  |  Ngay: 05/05/2026

Tai lieu: SC\-PH2\-INT\-010  |  Phase 2 – Thiet ke he thong

# __1\. TONG QUAN TICH HOP__

## __1\.1 Nguyen tac tich hop__

• SupplyCore la he thong nguon su that \(System of Record\) cho chuoi cung ung vat tu y te

• ERPNext v15 duoc tich hop noi tai \(in\-process\) – khong qua mang

• HIS/EMR va he thong ben ngoai tich hop qua REST API \+ Webhook

• Thiet ke API\-ready cho giai doan 2 – khong yeu cau tich hop truc tiep trong giai doan 1

• Moi truong hop ngoai le \(timeout, retry, rollback\) phai duoc xu ly ro rang

## __1\.2 Ban do tich hop tong the__

__He thong__

__Loai__

__Giao thuc__

__Chieu__

__Trang thai GD1__

__ERPNext v15__

Internal

Python in\-process

Bidirectional

Tich hop san – full

__MariaDB__

Internal

Frappe ORM

Read/Write

Tich hop san – full

__Redis__

Internal

Redis\-py

Read/Write

Tich hop san – cache/queue

__Email Server__

External

SMTP

Outbound

Da cau hinh – Frappe built\-in

__HIS / EMR__

External

REST \+ Webhook

Bidirectional \(future\)

Thiet ke API san – chua ket noi

__BHYT Portal \(BYT\)__

External

REST \(BYT API\)

Outbound

Thiet ke payload – chua ket noi

__SMS Gateway__

External

REST

Outbound

Tuy chon – chua ket noi

__LDAP / Active Directory__

External

LDAP

Inbound

Tuy chon – co the cau hinh Frappe

__LIS \(Lab\)__

External

HL7 / REST

Inbound

Ngoai pham vi GD1

__ERP Tai chinh \(SAP\)__

External

REST

Outbound \(GL\)

Ngoai pham vi GD1

# __2\. TICH HOP NOI TAI VOI ERPNEXT v15__

## __2\.1 Co che tich hop__

SupplyCore chay trong cung process voi ERPNext\. Giao tiep qua Frappe API truc tiep:

\# Cach dung Frappe API trong SupplyCore custom code

import frappe

\# Lay document ERPNext

po = frappe\.get\_doc\('Purchase Order', 'PO\-2026\-00001'\)

\# Tao document ERPNext moi

qi = frappe\.new\_doc\('Quality Inspection'\)

qi\.reference\_type = 'Purchase Receipt'

qi\.reference\_name = pr\.name

qi\.item\_code = pr\.items\[0\]\.item\_code

qi\.insert\(ignore\_permissions=False\)

\# Query ERPNext tables

open\_pos = frappe\.db\.get\_all\('Purchase Order',

    filters=\{'status': \['in', \['To Receive', 'To Receive and Bill'\]\]\},

    fields=\['name', 'supplier', 'grand\_total'\]\)

## __2\.2 ERPNext modules duoc su dung__

__ERPNext Module__

__Chuc nang su dung__

__Mo ta su dung trong SupplyCore__

__Purchase__

PO, Purchase Receipt

Quy trinh dat hang, tiec nhan – tong nguyen, chi them custom validation

__Stock__

Stock Entry, Ledger, Batch

Quan ly ton kho, lo hang, xuat nhap – tong nguyen

__Quality Management__

Quality Inspection

Kiem tra QC hang nhap – auto\-create tu Purchase Receipt

__Accounts__

Purchase Invoice, Payment Entry, GL

Ke toan cong no NCC, thanh toan, so cai

__HR / Setup__

Department, User

Khoa phong va nguoi dung – khong chinh sua

__Manufacturing__

BOM \(khong dung\)

Ngoai pham vi

__CRM__

Customer \(khong dung\)

Ngoai pham vi – benh vien khong co CRM

__Luong: Dat hang den Nhap kho__

__B__

__He thong nguon__

__Du lieu truyen__

__He thong nhan / Xu ly__

__1__

__Khoa phong / Ke hoach__

Material Request

SupplyCore M2: Kiem tra ton kho, tao MR

__2__

__SupplyCore M2__

Material Request

ERPNext: Luu vao database

__3__

__Ke toan__

Material Request

SupplyCore M2: Tao Purchase Order, kiem tra FC

__4__

__ERPNext__

Purchase Order

Email den NCC qua Frappe Email Engine

__5__

__Thu kho__

Purchase Receipt

ERPNext: Ghi nhan nhap kho

__6__

__ERPNext \(hooks\)__

Purchase Receipt submitted

SupplyCore M3: Auto\-create Quality Inspection

__7__

__Thu kho__

Quality Inspection

ERPNext: Ket qua QC Accepted/Rejected

__8__

__ERPNext \(hooks\)__

QI submitted

SupplyCore M5: Dang ky Batch vao expiry tracker

# __3\. TICH HOP VOI HIS / EMR \(GIAI DOAN 2\)__

## __3\.1 Tong quan__

Trong Giai doan 1, SupplyCore va HIS/EMR hoat dong doc lap\. SupplyCore san sang API de tich hop o GD2:

• SupplyCore GUI thiet ke cho phep nhap ma benh nhan thu cong \(Patient ID\)

• API endpoints cho Patient Dispensing da san sang nhan tu HIS

• Webhook se gui thong bao khi cap phat xong de HIS cap nhat ho so benh an

## __3\.2 Luong tich hop cap phat BN \(GD2\)__

__Cap phat vat tu cho Benh nhan \(sau tich hop GD2\)__

__B__

__He thong nguon__

__Du lieu truyen__

__He thong nhan / Xu ly__

__1__

__Bac si \(HIS/EMR\)__

Ke don vat tu cho BN ma=BN\-001

HIS gui POST request den SupplyCore

__2__

__HIS__

POST /api/method/supplycore\.api\.dispensing\.create\_from\_request

SupplyCore tao Dispensing Request tu HIS order

__3__

__SupplyCore__

Dispensing Request

Thu kho nhan thong bao, chuan bi vat tu

__4__

__Thu kho \(SupplyCore\)__

Stock Entry Issue

Xuat kho, tao Patient Dispensing

__5__

__SupplyCore \(Webhook\)__

Webhook: patient\_dispensing\.submitted

HIS nhan webhook, cap nhat ho so BN: vat tu da cap

__6__

__HIS__

Cap nhat ho so BN

Tinh chi phi, quyet toan BHYT

## __3\.3 Interface contract \(GD2 – de tham khao\)__

__Diem tich hop__

__Endpoint__

__Mo ta__

__HIS \-> SupplyCore__

POST /api/method/\.\.\.dispensing\.create\_from\_request

HIS tao yeu cau cap phat voi ma BN va danh sach vat tu

__SupplyCore \-> HIS__

Webhook patient\_dispensing\.submitted

SupplyCore thong bao da cap phat, gui chi tiet chi phi

__HIS \-> SupplyCore__

GET /api/resource/Patient Dispensing

HIS lay lich su cap phat de hien thi trong ho so BN

__HIS \-> SupplyCore__

GET /api/method/\.\.\.bhyt\.calculate\_cost

HIS tinh truoc chi phi BHYT truoc khi ke don

__SupplyCore \-> HIS__

Webhook recall\_notice\.submitted

SupplyCore thong bao thu hoi lo hang den bac si

# __4\. TICH HOP CONG THONG TIN BHYT \(GIAI DOAN 2\)__

## __4\.1 Pham vi tich hop__

SupplyCore se tich hop voi cong BHYT cua Bo Y te de quyet toan chi phi vat tu theo quy trinh BHYT\. Giai doan 1 chi tong hop bao cao noi bo\.

__Chuc nang__

__GD1__

__GD2 \(Ke hoach\)__

__Tinh phi BHYT__

Co – noi bo

Van hanh, tinh theo BHYT Code Config

__Quyet toan BHYT__

Bao cao Excel xuat tay

Xuat file XML/JSON theo dinh dang BYT

__Xac minh the BHYT__

Nhap thu cong

Nhap so the BHY

__Nhan ket qua duyet__

Thu cong

Xem bao cao

## __4\.2 Cau truc du lieu quyet toan \(GD1 – xuat Excel\)__

• Don vi tinh theo nhom N01\-N09 theo TT 04/2024/TT\-BYT \(cap nhat khi co thong tu moi\)

• Moi dong: ma vat tu, ten, so luong, don vi, don gia, thanh tien, ty le BH, so BH tra, benh nhan tra

• Tong hop theo khoa phong, theo ky bao cao \(thang/quy\)

• Format xuat: Excel co ky so / chu ky dien tu cua Thu quy BHYT benh vien

# __5\. TICH HOP EMAIL \(FRAPPE BUILT\-IN\)__

## __5\.1 Cau hinh Email__

• Dung Frappe built\-in Email Domain & Outgoing Mail Server

• Cau hinh qua: Email Domain \-> Outgoing Mail Settings \(SMTP Host, Port, TLS, Credentials\)

• Email queue xu ly boi RQ Worker – khong gui truc tiep, tranh block

## __5\.2 Cac email tu dong__

__Trigger__

__Gui den__

__Noi dung__

__PO duoc tao va duyet__

NCC \(email trong Supplier record\)

Chi tiet don hang, so luong, ngay giao du kien

__Vat tu sap het han \(daily\)__

SC\-STOREKEEPER, SC\-MANAGER

Danh sach vat tu, lo, so ngay con lai, de xuat xu ly

__Ton kho xuong duoi Reorder Level__

SC\-STOREKEEPER

Vat tu, kho, ton kho hien tai, muc tai dat hang

__Hop dong sap het han__

SC\-ACCOUNTANT, SC\-MANAGER

Ten HĐ, NCC, ngay het han, gia tri chua su dung

__PO cho duyet > 24h__

SC\-MANAGER

Danh sach PO dang cho, nguoi tao, gia tri

__Thu hoi lo hang__

Tat ca SC\-\* lien quan

Lot hang, vat tu, ly do thu hoi, khoa phong can tra

__Ket qua QC Reject__

SC\-STOREKEEPER, SC\-ACCOUNTANT

Chi tiet hang tu tra, PO goc, xu ly de nghi

__Chao mung user moi__

User moi tao

Link dang nhap, mat khau tam thoi, huong dan

# __6\. TICH HOP LDAP / ACTIVE DIRECTORY \(TUY CHON\)__

Frappe Framework ho tro LDAP authentication\. Benh vien co the cau hinh de nguoi dung dang nhap bang tai khoan AD cua benh vien:

• Cau hinh qua: Frappe Settings \-> LDAP Settings \-> Server, Base DN, User Filter

• Dong bo group LDAP voi Role Frappe qua LDAP Group mapping

• Nguoi dung van can duoc tao trong Frappe User list, nhung password xac thuc qua AD

• Fallback: neu LDAP khong kha dung, nguoi dung dang nhap bang mat khau Frappe

Khong bat buoc – SupplyCore hoat dong tot voi Frappe built\-in authentication\.

# __7\. XU LY LOI VA CAC TRUONG HOP NGOAI LE__

__Truong hop loi__

__Phan loai__

__Xu ly__

__Email server khong kha dung__

External

Queue email, retry 3 lan x 5 phut; sau do log loi va bao cao

__HIS timeout \(GD2\)__

External

Retry 2 lan x 10 giay; tao draft manual; log cho dieu tra

__Webhook HIS that bai \(GD2\)__

External

Retry 5 lan theo exponential backoff; chuyen sang manual

__BHYT API loi \(GD2\)__

External

Ghi nhan loi, giu bao cao noi bo, retry vao ngay hom sau

__ERPNext loi validate__

Internal

frappe\.throw\(\) – hien thi message ro rang cho user

__Database connection mat__

Internal

Frappe tu dong retry; neu qua 30s \-> 503 Service Unavailable

__Redis khong kha dung__

Internal

Fallback sang database cho session; scheduled jobs delay

__File upload loi__

Internal

Xac nhan kich thuoc toi da \(10MB\), dinh dang cho phep truoc upload

# __8\. LO TRINH TICH HOP THEO GIAI DOAN__

__Giai doan__

__Thoi gian__

__Tich hop__

__Ket qua mong doi__

__GD1__

05/2026

__ERPNext, Email, PDA/Barcode__

He thong van hanh day du noi bo, khong phu thuoc HIS

__GD2__

Q3/2026

__HIS/EMR \(REST \+ Webhook\)__

Cap phat BN tu dong, BHYT tu dong tinh

__GD2__

Q3/2026

__BHYT Portal BYT__

Quyet toan BHYT tu dong, giam sai so

__GD3__

Q1/2027

__LDAP/AD \(tuy chon\)__

SSO voi tai khoan benh vien, giam quan ly mat khau

__GD3__

Q2/2027

__LIS \(Lab\)__

Nhan du lieu xet nghiem, lien ket chi phi vat tu xet nghiem

__GD4__

2027\+

__ERP Tai chinh \(SAP\)__

Dong bo GL cuoi thang, giam nhap lieu kep

