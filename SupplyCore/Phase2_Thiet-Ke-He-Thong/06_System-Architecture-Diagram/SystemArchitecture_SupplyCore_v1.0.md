__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung Ứng Vật Tư Y Tế

__KIẾN TRÚC HỆ THỐNG TỔNG THỂ__

System Architecture Document

Phiên bản: v1\.0  |  Ngày: 05/05/2026

Tài liệu: SC\-PH2\-ARCH\-006  |  Phase 2 – Thiết kế hệ thống

# __1\. THÔNG TIN TÀI LIỆU__

__Thuộc tính__

__Giá trị__

__Tên tài liệu__

System Architecture Document – SupplyCore

__Mã tài liệu__

SC\-PH2\-ARCH\-006

__Phiên bản__

v1\.0

__Nền tảng__

Frappe Framework v15 \+ ERPNext v15 \(Custom Frappe App\)

__Kiến trúc tổng thể__

Monolithic \(Frappe standard\) với module cắm vào \(plug\-in architecture\)

__Môi trường triển khai__

On\-premise / Private Cloud \(Ubuntu 22\.04 LTS\)

__Tác giả__

Solution Architect – SupplyCore Project

__Trạng thái__

Đã phê duyệt – Phase 2 Final

# __2\. TỔNG QUAN KIẾN TRÚC__

## __2\.1 Nguyên tắc thiết kế__

• Tận dụng tối đa ERPNext v15 standard – không tái phát triển những gì đã có \(Purchase, Stock, Accounting, Workflow\)

• Custom chỉ khi thực sự cần cho nghiệp vụ y tế đặc thù: Framework Contract, Release Order, Patient Dispensing, BHYT Config

• Kiến trúc app độc lập \(supplycore app\) – KHÔNG sửa ERPNext core source code

• Thiết kế tham số hóa: mọi cấu hình BHYT, ngưỡng cảnh báo, workflow phải thay đổi được qua UI

• Single\-tenant trước \(1 bệnh viện\), thiết kế để có thể multi\-site sau

## __2\.2 Mô hình kiến trúc tổng thể__

Hệ thống SupplyCore sử dụng kiến trúc phân tầng \(Layered Architecture\) với 6 tầng rõ ràng:

__PRESENTATION LAYER__

Frappe UI \(Vue 3\)   │   Jinja2 Templates   │   Mobile/PDA Web App   │   Role\-based Dashboards

▼

__APPLICATION LAYER – SupplyCore Custom App__

M1 Hợp đồng   │   M2 Kế hoạch   │   M3 Tiếp nhận   │   M4 WMS   │   M5 FEFO   │   M6 Luân chuyển   │   M7 Cấp phát   │   M8 Kế toán   │   M9 Kiểm kê   │   M10 Truy xuất   │   M11 Dashboard   │   SYS Admin

▼

__FRAPPE FRAMEWORK v15 \(Core Platform\)__

ORM / DocType Engine   │   Workflow Engine   │   Role Permission Manager   │   REST API \(Auto\-generated\)   │   Background Jobs / Scheduler   │   Report Builder   │   Email Engine

▼

__ERPNEXT v15 \(Standard Modules – Read/Extend Only\)__

Purchase Order   │   Purchase Receipt   │   Stock Entry / Ledger   │   Payment Entry / GL   │   Item Master   │   Warehouse   │   Quality Inspection   │   Accounts / Cost Center

▼

__DATA LAYER__

MariaDB 10\.6\+  \(Primary DB\)   │   Redis \(Cache & Queue\)   │   File Storage \(Local/S3\)   │   Audit Log \(Immutable\)

▼

__INFRASTRUCTURE LAYER__

Ubuntu 22\.04 LTS Server   │   bench CLI \(Frappe Deploy Tool\)   │   Nginx Reverse Proxy   │   Supervisor \(Process Manager\)   │   SSL/TLS \(Let's Encrypt / Hospital Cert\)   │   Docker \(Optional\)

▼

# __3\. CHI TIẾT THÀNH PHẦN__

## __3\.1 SupplyCore Custom App__

SupplyCore là một Frappe App riêng biệt, cài đặt bên cạnh ERPNext\. Cấu trúc thư mục:

__Đường dẫn__

__Nội dung__

supplycore/\_\_init\_\_\.py

App entry point, version

supplycore/hooks\.py

Document Events, Scheduler Jobs, Fixtures

supplycore/supplycore/doctype/

Custom Doctypes: Framework Contract, Release Order, Patient Dispensing\.\.\.

supplycore/supplycore/report/

Custom Reports \(Script Reports, Query Reports\)

supplycore/supplycore/page/

Custom Pages \(Dashboard, PDA Interface\)

supplycore/public/js/

Client Scripts: form validations, FEFO picker UI

supplycore/templates/

Jinja2 print formats: PO, Receipt, Dispensing Slip

supplycore/config/

App menu, desktop icons, permissions fixtures

## __3\.2 Ma trận Module – Thành phần kỹ thuật__

__Mã__

__Tên Module__

__ERPNext Standard__

__Custom Extension__

__Kỹ thuật chính__

__M1__

__Hợp đồng & NCC__

Supplier, Framework Contract

Custom Doctype: Framework Contract, Release Order

hooks\.py, validate, on\_submit

__M2__

__Kế hoạch & Gọi hàng__

Material Request, Purchase Order

Custom: Procurement Plan

Scheduler, auto\-draft MR

__M3__

__Tiếp nhận & QC__

Purchase Receipt, Quality Inspection

Custom: QC Checklist template

on\_submit: auto\-create QC

__M4__

__WMS & PDA__

Warehouse, Stock Entry

Custom: Bin Location, Putaway Rule

Mobile API, barcode scan

__M5__

__Lô & FEFO__

Batch, Expiry

Custom: FEFO picker algorithm

get\_batches\_for\_fifo\(\) override

__M6__

__Luân chuyển__

Stock Entry Transfer

Custom: Transfer Request workflow

Workflow states, permissions

__M7__

__Cấp phát & BHYT__

Stock Entry Issue

Custom: Patient Dispensing, BHYT Config

BHYT rate lookup, patient link

__M8__

__Kế toán__

Purchase Invoice, Payment Entry

Custom: 3\-way match logic

validate: price vs PO vs Receipt

__M9__

__Kiểm kê__

Stock Reconciliation

Custom: Inventory Count Sheet

Scheduled periodic count

__M10__

__Truy xuất__

Batch, Stock Ledger

Custom: Recall Notice, Trace Report

get\_batch\_trace\(\) API

__M11__

__Dashboard__

ERPNext Dashboard

Custom: KPI Widgets, Alert Rules

Scheduled reports, webhooks

__SYS__

__Quản trị__

User, Role Permission

Custom: SupplyCore Settings

System\-level config Doctype

# __4\. TECHNOLOGY STACK__

__Thành phần__

__Công nghệ__

__Ghi chú__

__Backend Runtime__

__Python 3\.11\+__

Core language cho Frappe app; type hints, async support

__Web Framework__

__Frappe Framework v15__

DocType engine, ORM, REST API, Workflow, Scheduler

__ERP Core__

__ERPNext v15__

Accounting, Stock, Purchase – tận dụng tối đa module chuẩn

__Database__

__MariaDB 10\.6\+__

ACID transactions; JSON field support; Full\-text search

__Cache / Queue__

__Redis 7\+__

Session cache, background job queue \(RQ\), real\-time events

__Frontend__

__Vue 3 \(Frappe UI\)__

SPA components; Frappe Form/List/Report views

__Template Engine__

__Jinja2__

Server\-side render cho print formats, email templates

__Web Server__

__Nginx 1\.24\+__

Reverse proxy, static files, SSL termination, rate limiting

__Process Mgmt__

__Supervisor__

Manage gunicorn workers, RQ workers, socketio

__Deploy Tool__

__bench CLI__

Frappe deployment, site management, app install/update

__Containerization__

__Docker \+ Docker Compose__

Optional: dev environment, staging; production on bare metal

__CI/CD__

__GitHub Actions \(optional\)__

Auto\-run tests, lint, deploy to staging

__Monitoring__

__ERPNext Error Log \+ Sentry__

Exception tracking, performance monitoring

__API Protocol__

__REST \(JSON\) \+ Webhooks__

Frappe built\-in REST; custom whitelist endpoints

__Auth__

__Frappe Session \+ API Key__

Cookie\-based sessions; API Key/Secret for integrations

__Mobile/PDA__

__Progressive Web App__

Frappe mobile\-friendly views; barcode via JS BarcodeDetector API

# __5\. KIẾN TRÚC TRIỂN KHAI__

## __5\.1 Topology triển khai__

__Node__

__Thành phần__

__Spec tối thiểu__

__Ghi chú__

__App Server__

Frappe \+ ERPNext \+ SupplyCore

Nginx \+ Supervisor

8 vCPU, 16 GB RAM

200 GB SSD

Single node hoặc HA cluster; gunicorn 4–8 workers

__DB Server__

MariaDB 10\.6\+

4 vCPU, 8 GB RAM

500 GB SSD \(RAID\)

Có thể chung App Server cho bệnh viện nhỏ; tách riêng cho >500 users

__Cache Server__

Redis 7\+ \(cache \+ queue\)

2 vCPU, 4 GB RAM

Có thể chạy cùng App Server

__File Storage__

Local disk / MinIO S3

1 TB\+

Lưu tài liệu đính kèm, backup, file upload

__Reverse Proxy__

Nginx \+ SSL

\(Trên App Server\)

Rate limiting, static file serve, TLS termination

__Backup__

Cron \+ rclone / S3

Off\-site storage

Daily full backup, hourly incremental; retain 30 ngày

__Monitoring__

ERPNext Error Log

\+ Sentry \(optional\)

—

Alert khi error rate tăng đột biến

## __5\.2 Quy trình triển khai \(bench CLI\)__

\# 1\. Cài đặt Frappe bench

pip install frappe\-bench

bench init frappe\-bench \-\-frappe\-branch version\-15

\# 2\. Tạo site mới

bench new\-site hospital\.local \-\-db\-name supplycore

\# 3\. Cài ERPNext

bench get\-app erpnext \-\-branch version\-15

bench \-\-site hospital\.local install\-app erpnext

\# 4\. Cài SupplyCore

bench get\-app supplycore https://github\.com/org/supplycore

bench \-\-site hospital\.local install\-app supplycore

\# 5\. Migrate và start

bench \-\-site hospital\.local migrate

bench start  \# development

sudo bench setup production hospital\-user  \# production

# __6\. LUỒNG DỮ LIỆU CHÍNH__

## __6\.1 Luồng Nhập kho__

__Bước__

__Hành động__

__Doctype/Module__

__Trigger__

__1__

Tạo Purchase Order

ERPNext PO

Manual / from MR

__2__

NCC giao hàng → Tạo Purchase Receipt

ERPNext PR

Manual

__3__

Auto\-create Quality Inspection

ERPNext QI

hooks: after\_insert PR

__4__

QC Pass → nhập kho chính thức

ERPNext Stock Ledger

QI: on\_submit

__5__

Gán Batch \+ Hạn dùng

ERPNext Batch

PR submit, custom validate

__6__

Cập nhật Bin Location

WMS Module \(M4\)

Custom putaway\_rules

__7__

Kích hoạt FEFO tracker

M5 FEFO

Batch created event

__8__

Cảnh báo nếu sắp hết hạn

M11 Alert

Scheduled job daily

## __6\.2 Luồng Cấp phát vật tư__

__Bước__

__Hành động__

__Doctype/Module__

__Trigger__

__1__

Khoa phòng tạo yêu cầu cấp phát

Custom: Dispensing Request

Manual

__2__

FEFO picker gợi ý Batch

M5 FEFO Algorithm

on\_load form

__3__

Thủ kho xác nhận, tạo Stock Entry Issue

ERPNext Stock Entry

Manual submit

__4__

Ghi nhận sử dụng cho Bệnh nhân

Custom: Patient Dispensing

Manual after issue

__5__

Tra cứu mã BHYT → tính chi phí

M7 BHYT Config

on\_save Patient Dispensing

__6__

Tổng hợp chi phí vào hồ sơ BN

Custom report

Aggregation query

# __7\. YÊU CẦU PHI CHỨC NĂNG__

__Thuộc tính__

__Chỉ tiêu__

__Cơ chế đảm bảo__

__Hiệu năng__

Page load < 2s

API response < 500ms

Nginx caching, Redis cache, DB index optimization, gunicorn workers

__Khả năng mở rộng__

≥ 100 concurrent users

≥ 50 khoa phòng

Horizontal scaling gunicorn workers; Read replica MariaDB

__Tính sẵn sàng__

Uptime ≥ 99\.5%

< 4h downtime/tháng

Supervisor auto\-restart; daily backup; documented rollback procedure

__Bảo mật__

RBAC, TLS 1\.2\+

Audit trail không thể xóa

Frappe Role Permission; HTTPS only; immutable GL/Stock Ledger

__Khả năng phục hồi__

RPO ≤ 1 giờ

RTO ≤ 4 giờ

Incremental backup hourly; documented DR runbook

__Khả năng bảo trì__

Zero\-downtime deploy \(staging\)

bench migrate; hot\-reload frontend; blue/green optional

__Tuân thủ__

Luật CNTT VN, TT BYT BHYT

ISO 27001 \(roadmap\)

Audit log, data masking, role\-based access, BHYT configurable

# __8\. ĐIỂM TÍCH HỢP & GIAO TIẾP__

__Hệ thống__

__Giao thức__

__Phương thức__

__Trạng thái__

__ERPNext v15__

In\-process

Python API call \(frappe\.get\_doc\)

✅ Tích hợp sẵn

__HIS / EMR__

REST \+ Webhook

Outbound webhook khi cấp phát BN

📋 Giai đoạn 2

__Cổng BHYT__

REST \(Bộ Y tế API\)

POST quyết toán BHYT định kỳ

📋 Giai đoạn 2

__Email Server__

SMTP

Frappe Email Queue

✅ Cấu hình qua Settings

__SMS Gateway__

REST

Frappe SMS integration

📋 Tùy chọn

__LIS \(Lab\)__

HL7 / REST

Nhận kết quả xét nghiệm vật tư

📋 Ngoài phạm vi GĐ1

# __9\. BẢO MẬT VÀ TUÂN THỦ \(TÓM TẮT\)__

• Authentication: Frappe session\-based \+ API Key/Secret cho tích hợp

• Authorization: Role Permission Manager – phân quyền theo Doctype \+ field level

• Transport: HTTPS/TLS 1\.2\+ bắt buộc; HTTP bị redirect sang HTTPS

• Audit Trail: ERPNext Version \(Change Log\) \+ Custom Audit Log không thể xóa

• Data at Rest: Mã hóa disk \(LUKS\) cho server production; backup mã hóa AES\-256

• Compliance: Thiết kế phù hợp Luật An toàn thông tin VN, TT Bộ Y tế về BHYT

# __10\. QUYẾT ĐỊNH KIẾN TRÚC__

__Quyết định__

__Lý do__

__Hệ quả / Đánh đổi__

__Dùng Frappe \+ ERPNext thay vì build from scratch__

Tiết kiệm 60\-70% effort; có sẵn PO, Stock, Accounting

Phụ thuộc Frappe release cycle; cần follow Frappe conventions

__Custom App riêng, không sửa ERPNext core__

Có thể upgrade ERPNext độc lập; dễ maintain

Một số customization phức tạp hơn, cần hooks/monkey\-patch

__MariaDB thay vì PostgreSQL__

Frappe officially supports MariaDB; tốt hơn cho Frappe ORM

Không dùng được PostgreSQL\-specific features

__Monolith thay vì Microservices__

Hospital IT team nhỏ; simpler ops; Frappe design pattern

Khó scale individual modules; OK cho quy mô bệnh viện đơn

__PWA thay vì native mobile app__

Dùng Frappe built\-in mobile; zero extra dev cost

Một số tính năng PDA bị giới hạn so với native \(offline limited\)

