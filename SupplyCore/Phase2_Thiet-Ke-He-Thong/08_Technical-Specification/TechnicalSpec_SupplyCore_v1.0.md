__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung Ứng Vật Tư Y Tế

__ĐẶC TẢ KỸ THUẬT – TECHNICAL SPECIFICATION__

Phiên bản: v1\.0  |  Ngày: 05/05/2026

Tài liệu: SC\-PH2\-TECH\-008  |  Phase 2 – Thiết kế hệ thống

# __1\. THÔNG TIN TÀI LIỆU__

__Thuộc tính__

__Giá trị__

__Tên tài liệu__

Technical Specification – SupplyCore

__Mã tài liệu__

SC\-PH2\-TECH\-008

__Phiên bản__

v1\.0

__Phạm vi__

Đặc tả kỹ thuật 11 module \+ SYS Admin

__Nền tảng__

Frappe Framework v15 \+ ERPNext v15

__Ngôn ngữ Backend__

Python 3\.11\+

__Ngôn ngữ Frontend__

JavaScript \(Vue 3, Frappe UI\)

__Tác giả__

Solution Architect – SupplyCore Project

__Trạng thái__

Đã phê duyệt – Phase 2 Final

# __2\. TIÊU CHUẨN LẬP TRÌNH__

## __2\.1 Python – Frappe Standards__

\# Frappe Python coding standards

import frappe

from frappe\.model\.document import Document

class FrameworkContract\(Document\):

    def validate\(self\):

        \# 1\. Luôn dùng frappe\.throw\(\) thay vì raise Exception

        if self\.valid\_to <= self\.valid\_from:

            frappe\.throw\(frappe\.\_\("Ngày hết hạn phải sau ngày hiệu lực"\)\)

    def on\_submit\(self\):

        \# 2\. Dùng frappe\.get\_doc\(\) để load doc liên quan

        supplier = frappe\.get\_doc\("Supplier", self\.supplier\)

    def on\_cancel\(self\):

        \# 3\. Dùng frappe\.db\.set\_value\(\) cho update đơn giản \(không trigger hooks\)

        frappe\.db\.set\_value\("Release Order", \{"framework\_contract": self\.name\},

                           "status", "Cancelled"\)

    @frappe\.whitelist\(\)  \# 4\. Decorator bắt buộc cho API methods

    def get\_available\_items\(self\):

        return frappe\.db\.get\_all\("FC Item",

            filters=\{"parent": self\.name, "remaining\_qty": \[">=", 0\]\},

            fields=\["item\_code", "remaining\_qty", "unit\_price"\]\)

## __2\.2 JavaScript – Frappe Form Scripts__

// Frappe JS client script – supplycore/public/js/framework\_contract\.js

frappe\.ui\.form\.on\('Framework Contract', \{

    refresh\(frm\) \{

        // Thêm custom button khi document ở trạng thái phù hợp

        if \(frm\.doc\.status === 'Active'\) \{

            frm\.add\_custom\_button\(\_\_\('Tạo Release Order'\), \(\) => \{

                frappe\.new\_doc\('Release Order', \{

                    framework\_contract: frm\.doc\.name,

                    supplier: frm\.doc\.supplier

                \}\);

            \}, \_\_\('Hành động'\)\);

        \}

    \},

    supplier\(frm\) \{

        // Dùng frm\.set\_query để lọc link field

        frm\.set\_query\('payment\_terms', \(\) => \(\{

            filters: \{ company: frappe\.defaults\.get\_default\('company'\) \}

        \}\)\);

    \}

\}\);

# __3\. HOOKS\.PY – DOCUMENT EVENTS__

Tập trung toàn bộ event triggers trong supplycore/hooks\.py:

\# supplycore/hooks\.py – Document Events

doc\_events = \{

    "Purchase Receipt": \{

        "on\_submit": "supplycore\.controllers\.receipt\.on\_submit",

        \# Auto\-create Quality Inspection khi PR được submit

    \},

    "Quality Inspection": \{

        "on\_submit": "supplycore\.controllers\.qc\.on\_submit",

        \# Khi QC pass: update PR status, move to stock

    \},

    "Stock Entry": \{

        "on\_submit": "supplycore\.controllers\.stock\_entry\.on\_submit",

        \# Nếu type=Material Issue: check FEFO compliance

    \},

    "Batch": \{

        "after\_insert": "supplycore\.controllers\.batch\.after\_insert",

        \# Register batch to expiry tracker

    \},

    "Purchase Order": \{

        "validate": "supplycore\.controllers\.purchase\_order\.validate",

        \# Check framework contract remaining value

        "on\_submit": "supplycore\.controllers\.purchase\_order\.on\_submit",

        \# Update Release Order status to Converted

    \},

\}

\# Scheduled Jobs

scheduler\_events = \{

    "daily": \[

        "supplycore\.tasks\.check\_expiry\_alerts",

        "supplycore\.tasks\.check\_contract\_expiry",

        "supplycore\.tasks\.check\_reorder\_levels",

    \],

    "weekly": \[

        "supplycore\.tasks\.generate\_procurement\_forecast",

    \]

\}

# __4\. ĐẶC TẢ KỸ THUẬT TỪNG MODULE__

## __M1 – Hợp đồng & Nhà cung cấp__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

Supplier \(ERPNext\) – tạo/sửa NCC; Payment Terms

__Custom Doctypes__

Framework Contract, FC Item, Release Order

__Hooks & Events__

PO\.validate: check FC remaining value
PO\.on\_submit: update RO status → Converted
FC scheduler: alert 30 ngày trước hết hạn

__Business Logic__

Tính toán used\_value = SUM\(PO linked to FC\)
Remaining\_value = total\_value \- used\_value
Block PO nếu vượt remaining\_value

__Phân quyền__

SC\-ACCOUNTANT: Create/Edit FC, RO
SC\-MANAGER: Approve FC, RO
SC\-EXECUTIVE: Approve FC giá trị lớn

__Validate / Constraint__

valid\_to > valid\_from
Không tạo PO khi FC expired
Duplicate contract\_number check

## __M2 – Kế hoạch tồn kho & Gọi hàng__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

Material Request, Reorder Level \(ERPNext\)

__Custom Doctypes__

Procurement Plan \(custom – optional phase 2\)

__Hooks & Events__

Scheduler daily: check Reorder Level → auto\-draft MR
MR\.on\_submit: notify SC\-ACCOUNTANT

__Business Logic__

Dự báo nhu cầu = avg\_monthly\_consumption × lead\_time\_months \+ safety\_stock
Auto\-draft MR khi actual\_qty <= reorder\_level

__Phân quyền__

SC\-STOREKEEPER: Create MR
SC\-MANAGER: Approve MR
SC\-ACCOUNTANT: Convert MR → PO

__Validate / Constraint__

Reorder level phải > 0
MR qty phải > 0 và <= max\_stock\_qty \(nếu có\)

## __M3 – Tiếp nhận & Kiểm tra chất lượng__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

Purchase Receipt, Quality Inspection \(ERPNext\)

__Custom Doctypes__

QC Checklist template \(custom field trên Item Group\)

__Hooks & Events__

PR\.on\_submit: auto frappe\.new\_doc\('Quality Inspection'\)
QI\.on\_submit: nếu status=Accepted → PR cập nhật received\_qty
QI\.on\_submit: nếu status=Rejected → create Supplier Return draft

__Business Logic__

3\-way match: PR qty vs PO qty \(accept tolerance ±2%\)
Backorder tự động nếu nhận thiếu
QC template load theo Item Group của từng item

__Phân quyền__

SC\-STOREKEEPER: Create PR, QC
SC\-MANAGER: Approve QC result

__Validate / Constraint__

PR qty không được > PO qty \+ 5%
Batch expiry\_date phải nhập nếu item has\_batch=True
Expiry phải >= today \+ 30 ngày

## __M4 – WMS & PDA__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

Warehouse \(ERPNext\) – 3\-cấp phân cấp

__Custom Doctypes__

Bin Location \(custom field trên Warehouse \+ Stock Entry\)
Putaway Rule \(ERPNext v15 built\-in\)

__Hooks & Events__

Stock Entry\.validate: gợi ý bin theo putaway rules
Barcode scanner API: /api/method/supplycore\.api\.wms\.scan\_barcode

__Business Logic__

Putaway rule: assign item → preferred bin
Bin capacity check trước khi nhập
Mobile\-friendly scan: BarcodeDetector API \(JS\)

__Phân quyền__

SC\-STOREKEEPER: Manage bins, do transfers
SC\-WARD\-STAFF: View only warehouse location

__Validate / Constraint__

Bin capacity check: current\_qty \+ incoming <= max\_capacity
Không cho xóa bin đang có hàng

## __M5 – Lô, Hạn dùng & FEFO__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

Batch \(ERPNext\) – expiry\_date, manufacture\_date

__Custom Doctypes__

FEFO Picker \(custom Python utility \+ JS client\)

__Hooks & Events__

Batch\.after\_insert: register to expiry scheduler
Scheduler daily: check\_expiry\_alerts\(\)
Stock Entry\.validate: call fefo\_picker\.get\_suggested\_batches\(\)

__Business Logic__

FEFO algorithm: SELECT batch ORDER BY expiry\_date ASC WHERE qty\_available > 0
Override FEFO: requires SC\-MANAGER approval \+ audit log entry
Expiry alerts: < 30 ngày \(RED\), 30–90 ngày \(YELLOW\)

__Phân quyền__

SC\-STOREKEEPER: Confirm/override batch selection
SC\-MANAGER: Approve FEFO override

__Validate / Constraint__

Batch expiry\_date phải nhập trước khi stock entry submit
FEFO override phải có ghi chú lý do

## __M6 – Luân chuyển nội bộ__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

Stock Entry \(Material Transfer\), Stock Reconciliation \(ERPNext\)

__Custom Doctypes__

Transfer Request \(custom workflow Doctype – optional\)

__Hooks & Events__

Stock Entry\.validate: check source warehouse qty
Stock Reconciliation\.on\_submit: tạo GL Entry điều chỉnh tự động

__Business Logic__

Material Transfer: kiểm tra tồn kho nguồn > 0 trước khi submit
Stock Reconciliation: tính difference qty \+ amount, tạo accounting entry
Cross\-warehouse transfer: cần approval SC\-MANAGER

__Phân quyền__

SC\-STOREKEEPER: Create transfers, reconciliation
SC\-MANAGER: Approve inter\-warehouse transfers
SC\-ACCOUNTANT: Approve stock reconciliation \(GL impact\)

__Validate / Constraint__

Transfer qty <= available qty tại kho nguồn
Không cho transfer sang kho inactive

## __M7 – Cấp phát & Ghi nhận sử dụng__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

Stock Entry \(Material Issue\), Department \(ERPNext\)

__Custom Doctypes__

Dispensing Request, Patient Dispensing, PD Item, BHYT Code Config

__Hooks & Events__

DR\.on\_submit: notify SC\-STOREKEEPER
Stock Entry Issue\.on\_submit: create Patient Dispensing draft
PD\.on\_save: auto\-calculate BHYT cost via bhyt\_calculator\(\)

__Business Logic__

FEFO\-based dispensing \(gọi fefo\_picker\)
BHYT calculation: lookup BHYT Code Config → apply rate
Patient link optional \(khoa vs bệnh nhân cụ thể\)
Aggregation report: cost per patient / per ward / per period

__Phân quyền__

SC\-WARD\-STAFF: Create Dispensing Request, fill Patient Dispensing
SC\-STOREKEEPER: Process DR → create Stock Entry
SC\-ACCOUNTANT: View BHYT reports

__Validate / Constraint__

Dispensing qty <= available stock
BHYT rate: 0–100%
Patient ID mandatory nếu purpose = Patient\-specific

## __M8 – Kế toán & Thanh toán__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

Purchase Invoice, Payment Entry, GL Entry, Cost Center \(ERPNext\)

__Custom Doctypes__

Custom validate: 3\-way match logic; custom report: BHYT reconciliation

__Hooks & Events__

PI\.validate: 3\-way match \(PI vs PO vs PR\)
PI\.on\_submit: tạo GL Entry tự động \(ERPNext standard\)
Payment Entry: approval workflow theo threshold \(SupplyCore Settings\)

__Business Logic__

3\-way match tolerance: ±1% allowed; >1% → flag for review
Payment threshold: < 50tr \(SC\-MANAGER\), >= 50tr \(SC\-EXECUTIVE\)
BHYT report: aggregate PD Item by bhyt\_group per period

__Phân quyền__

SC\-ACCOUNTANT: Create PI, Payment Entry
SC\-MANAGER: Approve PI mismatch, Payment <= 50tr
SC\-EXECUTIVE: Approve Payment >= 50tr

__Validate / Constraint__

PI total phải khớp PR amount ± tolerance
Không duplicate invoice number cho cùng 1 NCC

## __M9 – Kiểm kê & Đối soát__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

Stock Reconciliation, Physical Inventory Count \(ERPNext\)

__Custom Doctypes__

Inventory Count Sheet \(custom print format \+ scheduled creation\)

__Hooks & Events__

Scheduler: tạo draft Inventory Count Sheet định kỳ
Stock Reconciliation\.on\_submit: tạo GL Entry điều chỉnh

__Business Logic__

Count sheet in: list item \+ bin \+ system\_qty \(ẩn để tránh bias\)
Enter actual\_qty → system tính difference
Recount trigger: |difference| / system\_qty > threshold \(configurable\)

__Phân quyền__

SC\-STOREKEEPER: Do physical count, enter results
SC\-MANAGER: Review discrepancies, approve reconciliation
SC\-ACCOUNTANT: Approve GL adjustment

__Validate / Constraint__

Chỉ submit count khi tất cả items đã được đếm
Difference value > threshold → require manager approval

## __M10 – Truy xuất & Điều tra__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

Batch, Stock Ledger Entry \(ERPNext – read only\)

__Custom Doctypes__

Recall Notice; Batch Trace Report \(Script Report\)

__Hooks & Events__

Recall Notice\.on\_submit: block tất cả giao dịch batch bị ảnh hưởng
Batch Trace: traverse SLE backward từ dispensing đến receipt

__Business Logic__

Batch trace algorithm: SLE chain traversal theo batch\_no
Recall: set Batch\.disabled = 1 → block mọi stock transaction
Audit trail query: Version table của Frappe \(không thể xóa\)

__Phân quyền__

SC\-MANAGER: Create Recall Notice, view Trace Reports
SC\-STOREKEEPER: Execute physical recall
SC\-SYSADMIN: View audit trail full

__Validate / Constraint__

Recall Notice cần approval SC\-EXECUTIVE nếu số lô lớn
Không cho xóa audit trail \(immutable by design\)

## __M11 – Dashboard & Cảnh báo điều hành__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

ERPNext Dashboard, Number Card, Dashboard Chart

__Custom Doctypes__

Alert Rule Config \(custom\); KPI Widget \(custom Frappe Page\)

__Hooks & Events__

Scheduler daily: check\_expiry, check\_reorder, check\_contract\_expiry → tạo Notification
Dashboard: cache 5 phút trong Redis
Email alert: frappe\.sendmail\(\) qua scheduled task

__Business Logic__

KPI tính theo: SUM\(SLE\) cho stock value; COUNT\(PO\) chờ duyệt
Alert priority: Khẩn \(< 30 ngày expire\), Quan trọng, Thông tin
Role\-based dashboard: SC\-EXECUTIVE thấy tất cả; SC\-STOREKEEPER thấy kho của mình

__Phân quyền__

SC\-EXECUTIVE, SC\-MANAGER: View all dashboards
SC\-STOREKEEPER: View warehouse\-specific dashboard
SC\-SYSADMIN: Configure alert rules

__Validate / Constraint__

Alert threshold phải > 0
Email recipients phải là valid email format

## __SYS – Quản trị hệ thống__

__Thuộc tính__

__Chi tiết__

__ERPNext Standard dùng__

User, Role, Role Permission Manager \(Frappe standard\)

__Custom Doctypes__

SupplyCore Settings \(single\-record config Doctype\)

__Hooks & Events__

User\.after\_insert: send welcome email với temp password
SupplyCore Settings\.on\_update: clear relevant Redis cache

__Business Logic__

User provisioning: assign SC\-\* roles theo chức danh
Data scope: Department\-level permission qua User Permission
Config: load từ SupplyCore Settings singleton \(cached\)

__Phân quyền__

SC\-SYSADMIN: Manage users, roles, settings
SC\-MANAGER: View user list \(read only\)

__Validate / Constraint__

Email không được trùng trong hệ thống
Role phải thuộc danh sách SC\-\* roles hợp lệ
Config values phải trong phạm vi hợp lệ

# __5\. XỬ LÝ LỖI VÀ EXCEPTION__

## __5\.1 Nguyên tắc__

• Dùng frappe\.throw\(\) cho lỗi nghiệp vụ – hiển thị message thân thiện cho user

• Dùng frappe\.log\_error\(\) cho lỗi kỹ thuật cần điều tra

• Không dùng bare except – luôn catch cụ thể exception type

• Transaction rollback tự động khi exception trong on\_submit hook

## __5\.2 Error codes SupplyCore__

__Mã lỗi__

__Tên__

__Mô tả & Xử lý__

__SC\-E001__

__FEFO\_OVERRIDE__

Xuất kho không theo FEFO – yêu cầu ghi lý do và phê duyệt

__SC\-E002__

__FC\_EXCEEDED__

Vượt hạn mức hợp đồng khung – block PO, thông báo cảnh báo

__SC\-E003__

__EXPIRY\_TOO\_CLOSE__

Hạn dùng < 30 ngày – yêu cầu xác nhận trước khi nhập

__SC\-E004__

__QC\_FAILED__

QC không đạt – auto\-create supplier return draft

__SC\-E005__

__STOCK\_INSUFFICIENT__

Tồn kho không đủ – hiển thị số lượng tối đa có thể xuất

__SC\-E006__

__BHYT\_CONFIG\_MISSING__

Vật tư không có cấu hình BHYT – ghi nhận tự trả 100%

__SC\-E007__

__DUPLICATE\_INVOICE__

Số hóa đơn trùng – block submit, yêu cầu kiểm tra

__SC\-E008__

__BATCH\_RECALLED__

Lô hàng đang bị thu hồi – block toàn bộ giao dịch

__SC\-E009__

__THREE\_WAY\_MISMATCH__

Hóa đơn không khớp PO/PR > 1% – flag for review

__SC\-E010__

__USER\_PERMISSION\_DENIED__

Người dùng không có quyền thao tác kho/khoa này

# __6\. CHIẾN LƯỢC KIỂM THỬ KỸ THUẬT__

__Loại test__

__Công cụ__

__Phạm vi__

__Unit Test__

pytest \(Frappe\)

Validate functions, FEFO algorithm, BHYT calculator, 3\-way match logic

__Integration Test__

Frappe test runner

Document lifecycle: PR → QI → Stock Entry → Patient Dispensing

__API Test__

Postman / pytest\-requests

Tất cả whitelist endpoints; auth, pagination, error codes

__UI Test__

Selenium / Playwright \(optional\)

Critical flows: nhập kho, cấp phát, tạo PO

__Performance Test__

Locust

100 concurrent users; API response < 500ms

__Security Test__

OWASP checklist manual

SQL injection, XSS, CSRF, session fixation

## __6\.1 Frappe Unit Test template__

\# supplycore/tests/test\_fefo\.py

import frappe

from frappe\.tests\.utils import FrappeTestCase

from supplycore\.utils\.fefo\_picker import get\_suggested\_batches

class TestFEFO\(FrappeTestCase\):

    def test\_fefo\_order\(self\):

        """FEFO: batch với hạn dùng gần nhất phải được chọn trước"""

        batches = get\_suggested\_batches\('TEST\-ITEM\-001', 'Main Warehouse', qty=10\)

        \# Batch đầu tiên phải có expiry gần nhất

        self\.assertLessEqual\(batches\[0\]\.expiry\_date, batches\[\-1\]\.expiry\_date\)

    def test\_fefo\_skip\_expired\(self\):

        """FEFO: không trả về batch đã hết hạn"""

        batches = get\_suggested\_batches\('TEST\-ITEM\-001', 'Main Warehouse', qty=10\)

        import datetime

        today = datetime\.date\.today\(\)

        for b in batches:

            self\.assertGreater\(b\.expiry\_date, today\)

