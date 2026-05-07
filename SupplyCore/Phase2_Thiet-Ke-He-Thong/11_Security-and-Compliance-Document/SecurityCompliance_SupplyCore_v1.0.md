__SUPPLYCORE__

He thong Quan ly Chuoi Cung Ung Vat Tu Y Te

__BAO MAT & TUAN THU – SECURITY & COMPLIANCE__

Phien ban: v1\.0  |  Ngay: 05/05/2026

Tai lieu: SC\-PH2\-SEC\-011  |  Phase 2 – Thiet ke he thong

# __1\. THONG TIN TAI LIEU__

__Thuoc tinh__

__Gia tri__

__Ten tai lieu__

Security & Compliance Document – SupplyCore

__Ma tai lieu__

SC\-PH2\-SEC\-011

__Pham vi__

He thong SupplyCore – 11 module \+ SYS Admin

__Tieu chuan tham chieu__

Luat An toan thong tin mang VN \(2015\), TT Bo Y te ve BHYT, OWASP Top 10, ISO 27001 \(roadmap\)

__Moi truong__

On\-premise / Private Cloud – Benh vien

__Du lieu nhay cam__

Thong tin benh nhan, chi phi BHYT, hop dong NCC, so the BHYT

__Tac gia__

Security Architect – SupplyCore Project

__Trang thai__

Da phe duyet – Phase 2 Final

# __2\. XAC THUC VA QUAN LY PHIEN LAM VIEC__

## __2\.1 Co che xac thuc__

__Phuong thuc__

__Dung cho__

__Chi tiet ky thuat__

__Session Cookie__

Web browser

Frappe session; HttpOnly; Secure; SameSite=Lax; TTL = 8h

__API Key/Secret__

Server\-to\-server, integrations

Bearer token: Authorization: token key:secret; Rotate theo quy trinh

__Password Policy__

Tat ca user

Min 12 ky tu, co chu hoa, so, ky tu dac biet; doi sau 90 ngay

__2FA \(Tuy chon\)__

SC\-MANAGER tro len

TOTP \(Google Authenticator\) – co the bat trong Frappe Settings

__LDAP \(Tuy chon\)__

Tich hop AD benh vien

Xac thuc qua AD; fallback sang Frappe auth neu LDAP xuong

## __2\.2 Chinh sach phien lam viec__

• Session timeout: 8 gio khong hoat dong \-> tu dong logout

• Concurrent sessions: cho phep nhieu thiet bi; can ghi log

• Failed login: khoa tai khoan sau 5 lan sai mat khau lien tiep \(30 phut\)

• Session hijacking: session ID rotate sau khi dang nhap thanh cong

• Logout: huy session phia server, xoa cookie

# __3\. PHAN QUYEN THEO VAI TRO \(RBAC\)__

## __3\.1 Co che phan quyen – Frappe Role Permission Manager__

Frappe cung cap phan quyen chi tiet theo DocType \+ field level\. SupplyCore su dung day du co che nay:

• Role\-level permission: Doc\-type x Role x Action \(Read/Write/Create/Delete/Submit/Cancel/Amend\)

• User Permission: Gioi han pham vi du lieu \(Chi xem kho A, chi xem khoa Noi\.\.\.\)

• Field\-level permission: An truong nhay cam voi role khong can thiet

• Frappe Permission Manager: Giao dien GUI de cap nhat quyen, khong can code

## __3\.2 Ma tran phan quyen – DocType x Role__

R=Read, W=Write, S=Submit, D=Delete, SD=Submit\+Delete, RWSD=Full Access, \-=Khong co quyen

__DocType__

__STOREKEEPER__

__WARD\-STAFF__

__ACCOUNTANT__

__MANAGER__

__EXECUTIVE__

__SYSADMIN__

__Framework Contract__

\-

R

RW

__RWSD__

R

__RWSD__

__Release Order__

R

\-

RWS

__RWSD__

\-

__RWSD__

__Purchase Order__

R

\-

RWS

RSD

\-

__RWSD__

__Purchase Receipt__

RWS

\-

R

RS

R

__RWSD__

__Quality Inspection__

RWS

\-

R

RS

\-

__RWSD__

__Stock Entry__

RWS

R\(dept\)

R

RS

R

__RWSD__

__Batch__

RWS

\-

R

R

\-

__RWSD__

__Patient Dispensing__

RWS

RW

R

RSD

R

__RWSD__

__Dispensing Request__

R

RWS

R

RS

R

__RWSD__

__Purchase Invoice__

\-

\-

RWS

RS

\-

__RWSD__

__Payment Entry__

\-

\-

RWS

RS

RS

__RWSD__

__Stock Reconciliation__

RW

\-

RS

RSD

\-

__RWSD__

__Framework Contract \(view\)__

R

R

RW

__RWSD__

R

__RWSD__

__BHYT Code Config__

\-

\-

R

RWS

\-

__RWSD__

__SupplyCore Settings__

\-

\-

\-

R

R

__RWSD__

__User__

\-

\-

\-

R

R

__RWSD__

__Recall Notice__

R

\-

R

__RWSD__

R

__RWSD__

__Dashboard \(all\)__

partial

partial

partial

R

R

R

# __4\. BAO MAT DU LIEU__

## __4\.1 Ma hoa__

__Lop du lieu__

__Giai phap__

__Chi tiet__

__Du lieu truyen \(In Transit\)__

__TLS 1\.2\+__

Nginx enforce HTTPS; HSTS header; TLS 1\.0/1\.1 disabled

__Du lieu luu \(At Rest\)__

__LUKS disk encryption__

Toan bo SSD server duoc ma hoa; khoa LUKS luu an toan

__Backup files__

__AES\-256__

rclone encrypt truoc khi day len off\-site storage

__Mat khau user__

__bcrypt \(Frappe built\-in\)__

Salt \+ hash; khong luu plaintext

__API Keys__

__Frappe secure storage__

Hash cua secret stored; key chi xem mot lan khi tao

__So the BHYT__

__Partial masking trong UI__

Hien thi 4 so cuoi khi xem; full khi cap phat

__Du lieu benh nhan__

__Phong nguyen__

Chi nguoi dung co User Permission moi xem

## __4\.2 Du lieu nhay cam – Data Classification__

__Loai du lieu__

__Muc do nhay cam__

__Vi du__

__Bien phap bao ve__

__Thong tin benh nhan__

__Bi mat cao__

Ma BN, so the BHYT, chi phi

RBAC strict; audit trail; partial masking

__Du lieu tai chinh__

__Bi mat trung binh__

Gia hop dong, chi phi vat tu

Role\-based; financial module restricted

__Thong tin NCC__

__Noi bo__

Ten, dia chi, so TK ngan hang

Noi bo only; khong share ra ngoai

__Du lieu kho / ton kho__

__Noi bo__

So luong, lo, han dung

Role\-based; read\-only cho ward staff

__Cau hinh he thong__

__Bi mat cao__

SMTP credentials, API keys

Sysadmin only; ma hoa trong storage

__Log & Audit__

__Luu tru bat buoc__

Lich su giao dich

Immutable; chi admin moi xem; luu 7 nam

# __5\. AUDIT TRAIL VA KIEM SOAT TRUY CU__

## __5\.1 Frappe Version \(Change Log\)__

Frappe tu dong ghi lai lich su thay doi cua moi document co track\_changes = 1:

• Luu: Truong nao thay doi, gia tri cu, gia tri moi, nguoi thay doi, thoi gian \(UTC\)

• Luu truy cap vao Version doctype – chi admin co the xem

• Khong the xoa Version records – immutable by design

## __5\.2 Custom Audit Log cho cac hanh dong dac biet__

__Hanh dong__

__Loai log__

__Du lieu ghi lai__

__FEFO override__

Custom Audit Log

User, thoi gian, vat tu, lo bi bo qua, ly do, batch duoc chon

__Thu hoi lo hang \(Recall\)__

Custom Audit Log

User, thoi gian, lo, li do, danh sach khoa phong lien quan

__Thay doi ma BHYT__

Frappe Version \+ Custom

Gia tri cu, gia tri moi, can cu phap ly \(so TT\)

__Dang nhap that bai__

Frappe Error Log

IP, username, thoi gian, so lan that bai

__Thay doi quyen \(Role\)__

Frappe Activity Log

Admin, user duoc thay doi, role truoc/sau

__Xuat du lieu \(Reports\)__

Custom Audit Log

User, loai bao cao, bo loc, thoi gian xuat

__Xu ly chung tu huy__

Frappe Cancel Log

User, doc name, ly do huy

__API access tu ben ngoai__

Nginx Access Log

IP, endpoint, method, response code, timestamp

# __6\. BAO MAT MANG VA HAP TANG__

## __6\.1 Cau hinh Nginx – Security Headers__

__HTTP Header__

__Gia tri khuyen nghi__

__Strict\-Transport\-Security__

max\-age=31536000; includeSubDomains; preload

__X\-Frame\-Options__

SAMEORIGIN – Ngan clickjacking

__X\-Content\-Type\-Options__

nosniff – Ngan MIME sniffing

__Content\-Security\-Policy__

default\-src 'self'; script\-src 'self' 'unsafe\-inline' \(Frappe yeu cau\); img\-src 'self' data:

__Referrer\-Policy__

strict\-origin\-when\-cross\-origin

__Permissions\-Policy__

geolocation=\(\), microphone=\(\), camera=\(\)

__X\-XSS\-Protection__

1; mode=block \(legacy browsers\)

__Server__

\(an di – khong tiet lo version Nginx\)

## __6\.2 Firewall va Network segmentation__

• Firewall: Chi mo port 80 \(redirect\) va 443 \(HTTPS\) ra ngoai

• SSH: Chi cho phep tu IP quan tri \(Jump host / VPN\); Port 22 doi thanh non\-standard

• Database port: MariaDB port 3306 chi accessible tu localhost hoac app server IP

• Redis: Khong expose ra ngoai; chi localhost binding

• Nguyen tac least privilege: Server chi co cac port can thiet

# __7\. QUAN LY LO HONG VA CAP NHAT BAO MAT__

## __7\.1 Quy trinh cap nhat__

__Thanh phan__

__Tan suat__

__Quy trinh__

__Frappe/ERPNext__

Theo phien ban

Test tren staging, backup, bench update, migrate, verify

__Python packages__

Hang thang

pip\-audit kiem tra CVE; cap nhat sau test

__Ubuntu OS__

Hang tuan

apt update && apt upgrade; kernel update can reboot

__Nginx__

Khi co CVE

Cap nhat theo advisory; test SSL config

__MariaDB__

Khi co CVE

Test truoc tren staging do co the can schema migration

__SSL Certificate__

90 ngay \(Let's Encrypt\) / 1 nam

Auto\-renew Certbot hoac cap nhat thu cong cert benh vien

## __7\.2 OWASP Top 10 – Bien phap xu ly__

__\#__

__Loi hong__

__Muc do \(SupplyCore\)__

__Bien phap trong SupplyCore__

__A01__

__Broken Access Control__

__Cao__

Frappe RBAC \+ User Permission; test permission cho moi DocType

__A02__

__Cryptographic Failures__

__Trung binh__

TLS 1\.2\+; bcrypt mat khau; ma hoa disk; backup ma hoa AES\-256

__A03__

__Injection \(SQL/Command\)__

__Thap__

Frappe ORM parameterized queries; khong nhan shell input tu user

__A04__

__Insecure Design__

__Trung binh__

Audit trail bat buoc; FEFO immutable; 3\-way match validation

__A05__

__Security Misconfiguration__

__Trung binh__

Checklist hardening; remove default accounts; tat debug mode prod

__A06__

__Vulnerable Components__

__Trung binh__

Hang thang kiem tra pip\-audit; theo Frappe security advisories

__A07__

__Auth Failures__

__Trung binh__

Account lockout 5 lan sai; session timeout; HTTPS only

__A08__

__Software Integrity Failures__

__Thap__

Frappe verified releases; khong dung third\-party untrusted plugins

__A09__

__Security Logging Failures__

__Thap__

Audit trail day du; Nginx access log; Error log Frappe

__A10__

__Server\-Side Request Forgery__

__Thap__

Khong co tinh nang fetch URL tu user input trong GD1

# __8\. TUAN THU PHAP LY VA CHUAN MUC__

## __8\.1 Quy dinh Viet Nam__

__Van ban phap ly__

__Noi dung lien quan__

__Bien phap tuan thu__

__Luat An toan thong tin mang 2015 \(86/2015/QH13\)__

Bao ve thong tin ca nhan; bao mat HTTT

RBAC, ma hoa, audit trail, chinh sach bao mat van ban

__Nghi dinh 13/2023/ND\-CP ve bao ve du lieu ca nhan__

Du lieu ca nhan benh nhan la du lieu nhay cam

Phan quyen truy cap, audit, quy trinh xu ly vi pham

__TT 09/2020/TT\-BYT – ung dung CNTT trong KCB__

Quy dinh he thong thong tin y te

Kha nang ket noi HIS, luu vet audit, bao cao BHYT

__TT 04/2024/TT\-BYT \(vi du\) – Danh muc BHYT__

Ma nhom N01\-N09, ty le thanh toan

Thiet ke tham so hoa BHYT – thay doi khong can code lai

__Quy dinh ke toan benh vien \(Che do ke toan DVHCSN\)__

Luu tru chung tu >= 10 nam

Data retention policy; backup off\-site; immutable GL

## __8\.2 Tham chieu tieu chuan quoc te__

__Tieu chuan__

__Trang thai__

__Muc do tuan thu hien tai__

__ISO 27001__

Roadmap GD3

Core controls: access control, cryptography, audit log, incident response duoc thuc hien\. Chua co chung nhan chinh thuc\.

__HIPAA \(My\)__

Tham khao

Khong bat buoc tai VN\. Ap dung nguyen tac: PHI access control, audit trail, encryption at rest/transit\.

__GDPR \(EU\)__

Tham khao

Khong bat buoc cho benh vien noi dia VN\. Nguyen tac data minimization, right to access, data retention ap dung\.

__SOC 2__

Ngoai pham vi

Danh cho cloud provider\. Khong ap dung cho on\-premise\.

__OWASP ASVS L1__

Hien tai

Application Security Verification Standard Level 1 – duoc ap dung trong thiet ke va kiem thu\.

# __9\. QUY TRINH XU LY SU CO BAO MAT__

## __9\.1 Phan loai su co__

__Cap do__

__Vi du__

__Thoi gian phan hoi__

__Nguoi xu ly__

__P1__

Lo lo du lieu benh nhan; tan cong thu hoi lo hang

< 1 gio thong bao; xu ly ngay

SYSADMIN \+ Giam doc CNTT

__P2__

Tai khoan bi xam nhap; bat thuong audit log

< 4 gio phan hoi

SYSADMIN

__P3__

Loi bao mat phat hien trong code/config

< 24 gio danh gia; fix trong sprint

Backend Team

__P4__

Canh bao bao mat thong thuong \(failed login\.\.\.\)

< 72 gio xem xet

SYSADMIN

## __9\.2 Quy trinh xu ly su co P1/P2__

__1\. __Phat hien & xac nhan su co

__2\. __Khoa tai khoan / IP lien quan \(neu can\)

__3\. __Thu thap chung cu \(audit log, access log\)

__4\. __Danh gia pham vi anh huong \(du lieu nao, bao nhieu user\)

__5\. __Xu ly ky thuat \+ patch

__6\. __Bao cao ban lanh dao va nguoi dung bi anh huong

# __10\. DANG KY RUI RO BAO MAT__

__ID__

__Rui ro__

__Muc do__

__Kha nang__

__Bien phap giam thieu__

__SEC\-R01__

Rui ro ro ri thong tin benh nhan qua loi phan quyen

__Cao__

Trung binh

RBAC strict; test permission; field\-level masking; audit log

__SEC\-R02__

Tan cong brute force vao tai khoan quan tri

__Cao__

Trung binh

Account lockout; 2FA cho admin; IP whitelist SSH

__SEC\-R03__

Du lieu BHYT bi gian lan boi nhan vien noi bo

__Cao__

Thap

Audit trail day du; bao cao bat thuong; role separation

__SEC\-R04__

Man\-in\-the\-middle do dung HTTP

__Trung binh__

Thap

HTTPS bat buoc; HSTS; tat HTTP

__SEC\-R05__

SQL Injection qua API

__Trung binh__

Rat thap

Frappe ORM parameterized; input validation

__SEC\-R06__

Lo lo du lieu qua backup khong ma hoa

__Cao__

Trung binh

Backup ma hoa AES\-256; kiem soat truy cap off\-site storage

__SEC\-R07__

Xam pham phien lam viec qua session hijacking

__Trung binh__

Thap

HttpOnly cookie; session ID rotate; HTTPS only

__SEC\-R08__

Uptime thap do tan cong hoac loi ky thuat

__Trung binh__

Trung binh

Backup hang ngay; DR plan; RPO 1h / RTO 4h; monitor

__SEC\-R09__

Loi bao mat trong thu vien third\-party \(CVE\)

__Trung binh__

Trung binh

Monthly pip\-audit; theo Frappe advisories; update quy trinh

__SEC\-R10__

Tai khoan admin mac dinh chua doi

__Cao__

Thap

Checklist hardening; doi mat khau truoc go\-live; audit

