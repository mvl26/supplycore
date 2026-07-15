__SUPPLYCORE__

Hospital Supply Chain Management Platform

Built on Frappe Framework v15 \+ ERPNext v15

__DESIGN SYSTEM DOCUMENT__

Tài liệu Hệ thống Thiết kế Giao diện

Phase 3 – Tài liệu số 14/20

__Phiên bản:__

1\.0 – Initial Release

__Ngày phát hành:__

05/05/2026

__Trạng thái:__

DRAFT – Chờ Review

__Phạm vi áp dụng:__

Tất cả màn hình SupplyCore – Web & Mobile PDA

__Dự án:__

SupplyCore – Quản lý chuỗi cung ứng vật tư y tế

# __MỤC LỤC__

1\. Tổng quan Design System

2\. Brand Identity & Logo

3\. Bảng màu \(Color Palette\)

4\. Typography – Kiểu chữ

5\. Spacing & Layout Grid

6\. Elevation & Shadow

7\. Border & Radius

8\. Iconography

9\. Component Library – Buttons

10\. Component Library – Form Controls

11\. Component Library – Tables & Lists

12\. Component Library – Cards & Panels

13\. Component Library – Badges & Tags

14\. Component Library – Navigation

15\. Component Library – Modals & Alerts

16\. Motion & Animation

17\. Accessibility Guidelines

18\. Design Tokens – Bảng tổng hợp

# __1\. TỔNG QUAN DESIGN SYSTEM__

SupplyCore Design System là tập hợp các nguyên tắc thiết kế, component và token thống nhất cho toàn bộ giao diện của hệ thống quản lý chuỗi cung ứng vật tư y tế\. Mục tiêu đảm bảo tính nhất quán, khả năng sử dụng \(usability\) và khả năng bảo trì \(maintainability\) trên tất cả các màn hình\.

## __1\.1 Mục tiêu__

__Mục tiêu__

__Mô tả__

__Nhất quán__

Mọi màn hình dùng chung ngôn ngữ thiết kế: màu sắc, font, spacing, component

__Hiệu quả__

Dev team build nhanh từ library có sẵn; Designer không cần thiết kế lại từ đầu

__Tiếp cận được__

Tuân thủ WCAG 2\.1 AA – hỗ trợ người dùng có khiếm khuyết thị giác

__Responsive__

Desktop \(1920px\+\), Laptop \(1366px\+\), Tablet \(768px\+\), Mobile PDA \(360px\+\)

__Bệnh viện__

Ưu tiên độ dễ đọc cao, thao tác nhanh, màu sắc chuyên nghiệp – tránh gây nhầm lẫn y tế

## __1\.2 Nền tảng kỹ thuật__

__Layer__

__Công nghệ__

__Ghi chú__

__Framework UI__

Frappe UI \(Vue 3\)

Built\-in component: Form, List, Dialog, Toast – custom theo Design System này

__CSS Variables__

CSS Custom Properties

Tất cả token màu, spacing, radius định nghĩa qua CSS var\(\-\-sc\-\*\)

__Icon Library__

Frappe Icons \+ Remix Icon

Không dùng Font Awesome để giữ bundle size nhỏ

__Font__

Inter \(web\) / System UI \(fallback\)

Tải qua Google Fonts CDN; fallback: \-apple\-system, BlinkMacSystemFont

__Mobile PDA__

Frappe UI Mobile \+ PWA

Touch target tối thiểu 44×44px; layout single\-column

# __2\. BRAND IDENTITY & LOGO__

## __2\.1 Logo SupplyCore__

__⊕  SupplyCore__

Hospital Supply Chain

__Logo Specifications:__

• Icon: Cross symbol \(⊕\) đại diện cho y tế \+ chuỗi liên kết cung ứng

• Wordmark: 'SupplyCore' – Inter Bold, tracking 0

• Tagline: 'Hospital Supply Chain' – Inter Regular, tracking \+50

• Minimum size: 120px width \(web\) / 80px \(mobile\)

• Clear space: 1× chiều cao logo xung quanh

• Không đặt logo lên nền màu tương phản thấp

## __2\.2 Logo Variants__

__Variant__

__Nền trắng__

__Nền tối__

__Sử dụng__

__Full Color__

✓ Primary

✗

Header, trang in, marketing

__Reversed__

✗

✓ Recommended

Sidebar tối, splash screen, email header

__Monochrome__

✓

✓

Tài liệu in đen trắng, favicon

__Icon only__

✓

✓

Tab icon, app icon, avatar placeholder

# __3\. BẢNG MÀU \(COLOR PALETTE\)__

## __3\.1 Primary Colors – Màu chủ đạo__

__Navy__

\#1F4E79

\-\-sc\-primary\-dark

__Royal Blue__

\#2E75B6

\-\-sc\-primary

__Sky Blue__

\#D6E4F0

\-\-sc\-primary\-light

__Ice Blue__

\#EBF5FB

\-\-sc\-primary\-xlight

■ White

__White__

\#FFFFFF

\-\-sc\-white

## __3\.2 Semantic Colors – Màu ngữ nghĩa__

__Success Dark__

\#155724

\-\-sc\-success\-dark

__Success Light__

\#E2EFDA

\-\-sc\-success\-light

__Warning Dark__

\#856404

\-\-sc\-warning\-dark

__Warning Light__

\#FFF2CC

\-\-sc\-warning\-light

__Error Dark__

\#721C24

\-\-sc\-error\-dark

__Error Light__

\#FCE4D6

\-\-sc\-error\-light

__Charcoal__

\#2C3E50

\-\-sc\-neutral\-dark

__Gray__

\#F2F2F2

\-\-sc\-neutral\-light

## __3\.3 Extended Palette – Màu mở rộng cho trạng thái__

__Token CSS__

__Hex__

__Tên màu__

__Sử dụng điển hình__

\-\-sc\-primary\-dark

\#1F4E79

Navy

Header, H1, nav text

\-\-sc\-primary

\#2E75B6

Royal Blue

CTA button, active link, badge

\-\-sc\-primary\-light

\#D6E4F0

Sky Blue

Selected row, highlighted field

\-\-sc\-primary\-xlight

\#EBF5FB

Ice Blue

Input background, hover fill

\-\-sc\-success

\#28A745

Emerald

Inline success icon

\-\-sc\-success\-light

\#E2EFDA

Mint

Bảng QC ĐẠT, trạng thái approved

\-\-sc\-warning

\#FFC107

Amber

Inline warning icon

\-\-sc\-warning\-light

\#FFF2CC

Cream

Bảng cảnh báo tồn kho thấp

\-\-sc\-error

\#DC3545

Red

Inline error icon, validation

\-\-sc\-error\-light

\#FCE4D6

Rose

Bảng thông báo lỗi, quá hạn

\-\-sc\-orange\-light

\#FCE9D6

Peach

Cảnh báo hạn dùng sắp hết

\-\-sc\-neutral\-dark

\#2C3E50

Charcoal

Body text, sidebar bg

\-\-sc\-neutral

\#6C757D

Gray

Placeholder, disabled text

\-\-sc\-neutral\-light

\#F2F2F2

Off\-White

Zebra row, disabled bg

\-\-sc\-border

\#BFBFBF

Silver

Border màn hình, table border

\-\-sc\-white

\#FFFFFF

White

Page bg, card, input bg

## __3\.4 Color Usage Rules – Quy tắc sử dụng màu__

__DO ✓__

__DON'T ✗__

__Lý do__

Dùng màu ngữ nghĩa đúng ngữ cảnh: xanh = tốt, đỏ = lỗi

Dùng màu đỏ cho thông báo bình thường

Gây nhầm lẫn cho nhân viên y tế

Contrast ratio tối thiểu 4\.5:1 cho text thường

Đặt text trắng lên nền \#FFF2CC

Không đạt WCAG AA

Dùng \-\-sc\-primary\-dark cho heading quan trọng

Dùng nhiều hơn 4 màu trong 1 màn hình

Gây rối thị giác, khó scan nhanh

Phân biệt trạng thái bằng cả màu \+ icon \+ text

Chỉ dùng màu để phân biệt trạng thái

Hỗ trợ người mù màu \(~8% nam giới\)

# __4\. TYPOGRAPHY – KIỂU CHỮ__

## __4\.1 Font Family__

__Vai trò__

__Font chính__

__Fallback__

__Áp dụng__

__Body / UI__

Inter

\-apple\-system, sans\-serif

Tất cả text UI, form, button, label

__Heading__

Inter Bold

Georgia, serif \(fallback báo cáo\)

H1–H4, section title, module name

__Monospace__

JetBrains Mono / Consolas

Courier New, monospace

Code, barcode, ID, số lô, error log

__Báo cáo in__

Times New Roman

Georgia, serif

Tài liệu in ấn, PDF export

## __4\.2 Type Scale – Thang kích thước chữ__

__Token__

__Size \(px\)__

__Size \(rem\)__

__Line Height__

__Weight__

__Sử dụng__

\-\-sc\-text\-display

36px

2\.25rem

1\.2

700

Page title, splash screen

\-\-sc\-text\-h1

28px

1\.75rem

1\.3

700

Section header, module name

\-\-sc\-text\-h2

22px

1\.375rem

1\.35

600

Sub\-section, card title

\-\-sc\-text\-h3

18px

1\.125rem

1\.4

600

Group label, panel header

\-\-sc\-text\-body\-lg

16px

1rem

1\.5

400

Body text, form label prominent

\-\-sc\-text\-body

14px

0\.875rem

1\.5

400

Thân văn bản, form input

\-\-sc\-text\-body\-sm

13px

0\.8125rem

1\.4

400

Helper text, secondary info

\-\-sc\-text\-caption

12px

0\.75rem

1\.4

400

Caption, tooltip, metadata

\-\-sc\-text\-mono

13px

0\.8125rem

1\.5

400

Mã vật tư, số lô, barcode

## __4\.3 Typography Rules__

__Quy tắc__

__Chi tiết__

__Contrast text__

Text tối trên nền sáng: minimum 4\.5:1 \(AA\)\. Text lớn ≥ 18px: minimum 3:1

__Line length__

Tối đa 80 ký tự / dòng cho đoạn văn dài\. Form label: 1 dòng nếu có thể

__Số & dữ liệu__

Dùng monospace \(JetBrains Mono\) cho mã vật tư, số lô, số lượng trong bảng – dễ scan theo cột

__Tiếng Việt__

Inter hỗ trợ đầy đủ Unicode Vietnamese\. Không dùng font thiếu dấu trong UI

__Số liệu y tế__

Số lượng, đơn giá luôn right\-align\. Phân cách nghìn bằng dấu phẩy \(1,234,567 VND\)

__Truncation__

Tên vật tư dài: text\-overflow: ellipsis \+ tooltip hiện full text\. KHÔNG truncate mã BHYT, số lô

# __5\. SPACING & LAYOUT GRID__

## __5\.1 Spacing Scale – Thang khoảng cách__

SupplyCore dùng hệ thống spacing cơ sở 4px \(0\.25rem\)\. Mọi margin, padding, gap đều là bội số của 4px\.

__Token__

__px__

__rem__

__Sử dụng điển hình__

__\-\-sc\-space\-1__

4px

0\.25rem

Icon padding, micro gap

__\-\-sc\-space\-2__

8px

0\.5rem

Button horizontal padding nhỏ, badge padding

__\-\-sc\-space\-3__

12px

0\.75rem

Input padding, inline icon gap

__\-\-sc\-space\-4__

16px

1rem

Card padding, form field gap, list item

__\-\-sc\-space\-5__

20px

1\.25rem

Section gap nhỏ, table cell padding

__\-\-sc\-space\-6__

24px

1\.5rem

Card gap, modal padding

__\-\-sc\-space\-8__

32px

2rem

Section padding, panel gap

__\-\-sc\-space\-10__

40px

2\.5rem

Page section break

__\-\-sc\-space\-12__

48px

3rem

Header height, large section spacing

__\-\-sc\-space\-16__

64px

4rem

Page top padding, hero section

## __5\.2 Layout Grid – Lưới bố cục__

__Breakpoint__

__Width__

__Layout__

__xs – Mobile PDA__

320–480px

1 col, full\-width, no sidebar\. Nav: hamburger bottom bar

__sm – Tablet__

481–768px

1–2 col, collapsible sidebar \(icon\-only mode\)

__md – Laptop__

769–1366px

Sidebar 240px \+ content fluid\. Grid 12\-col\.

__lg – Desktop__

1367–1920px

Sidebar 260px \+ content max 1200px centered

__xl – Wide Screen__

1921px\+

Sidebar 280px \+ dual\-panel content \(list \+ detail\)

## __5\.3 Page Layout Template__

TOPBAR  \(height: 48px\)  |  Logo \+ Page title \+ User menu \+ Notifications

SIDEBAR \(260px\)
─────────────
▸ M1 Hợp đồng
▸ M2 Kế hoạch
▸ M3 Tiếp nhận
▸ M4 WMS
▸ M5 Lô/Hạn
▸ M6 Luân chuyển
▸ M7 Cấp phát
▸ M8 Kế toán
▸ M9 Kiểm kê
▸ M10 Truy xuất
▸ M11 Dashboard

CONTENT AREA \(fluid\)
────────────────────
Breadcrumb
Page Header \(title \+ action buttons\)
─────────────────────────────────────
Main Content \(List / Form / Dashboard\)
─────────────────────────────────────
Pagination / Footer

# __6\. ELEVATION & SHADOW__

__Token__

__CSS Value__

__Sử dụng__

\-\-sc\-shadow\-none

none

Flat element, table row

\-\-sc\-shadow\-sm

0 1px 2px rgba\(0,0,0,0\.08\)

Chip, badge, small button

\-\-sc\-shadow\-md

0 2px 8px rgba\(0,0,0,0\.12\)

Card, dropdown, datepicker

\-\-sc\-shadow\-lg

0 4px 16px rgba\(0,0,0,0\.16\)

Modal, drawer, notification panel

\-\-sc\-shadow\-xl

0 8px 32px rgba\(0,0,0,0\.20\)

Full\-screen overlay, critical alert

\-\-sc\-shadow\-focus

0 0 0 3px rgba\(46,117,182,0\.35\)

Focus ring – keyboard nav, a11y

# __7\. BORDER & RADIUS__

__Token__

__Value__

__Sử dụng__

\-\-sc\-border\-color

\#BFBFBF

Border chung: table, input, card

\-\-sc\-border\-focus

\#2E75B6

Input/select focus state

\-\-sc\-border\-error

\#DC3545

Input validation error

\-\-sc\-border\-success

\#28A745

Input validation OK

\-\-sc\-radius\-sm

4px

Button nhỏ, badge, chip, tag

\-\-sc\-radius\-md

6px

Input, select, card, panel

\-\-sc\-radius\-lg

8px

Modal, drawer, large card

\-\-sc\-radius\-xl

12px

Hero card, KPI panel

\-\-sc\-radius\-full

9999px

Avatar, toggle switch, pill

# __8\. ICONOGRAPHY__

## __8\.1 Icon Library__

SupplyCore dùng Remix Icon \(ri\-\*\) làm thư viện chính, kết hợp Frappe Icons cho các component built\-in\. Remix Icon là open\-source, hỗ trợ SVG \+ Web Font, có đầy đủ icon y tế và logistics\.

## __8\.2 Icon Usage – Module Icons__

__Module__

__Icon Name__

__Emoji đại diện__

__Mô tả__

__M1 Hợp đồng__

ri\-file\-text\-line

📄

Hợp đồng khung, nhà cung cấp

__M2 Kế hoạch__

ri\-calendar\-line

📅

Kế hoạch tồn kho, gọi hàng

__M3 Tiếp nhận__

ri\-truck\-line

🚚

Nhập hàng, kiểm tra QC

__M4 WMS__

ri\-warehouse\-line

🏭

Quản lý kho, PDA scan

__M5 Lô/Hạn__

ri\-qr\-code\-line

📦

Quản lý lô, hạn dùng, FEFO

__M6 Luân chuyển__

ri\-exchange\-line

🔄

Chuyển kho nội bộ

__M7 Cấp phát__

ri\-syringe\-line

💉

Cấp phát vật tư bệnh nhân, khoa

__M8 Kế toán__

ri\-money\-dollar\-circle\-line

💰

Thanh toán NCC, đối soát

__M9 Kiểm kê__

ri\-clipboard\-line

📋

Kiểm kê định kỳ, đối chiếu

__M10 Truy xuất__

ri\-search\-line

🔍

Truy xuất nguồn gốc, recall

__M11 Dashboard__

ri\-dashboard\-line

📊

Báo cáo, KPI, cảnh báo

## __8\.3 Action Icons – Biểu tượng hành động__

__Action__

__Icon__

__Context__

__Thêm mới__

ri\-add\-circle\-line \(➕\)

Tất cả List view – primary action

__Sửa__

ri\-edit\-line \(✏️\)

Form view, inline row action

__Xóa__

ri\-delete\-bin\-line \(🗑️\)

Soft\-delete; confirm dialog bắt buộc

__Lưu__

ri\-save\-line \(💾\)

Form header – cạnh nút Submit

__In__

ri\-printer\-line \(🖨️\)

PO, receipt, dispensing ticket

__Export__

ri\-download\-line \(📥\)

Export Excel/PDF từ List view

__Lọc__

ri\-filter\-line \(🔽\)

Filter panel toggle

__Tìm__

ri\-search\-line \(🔍\)

Search input prepend icon

__Cảnh báo__

ri\-alert\-line \(⚠️\)

Expiry warning, low stock

__Scan__

ri\-qr\-scan\-line \(📷\)

PDA barcode scan trigger

__Approve__

ri\-check\-double\-line \(✅\)

Workflow approve action

__Reject__

ri\-close\-circle\-line \(❌\)

Workflow reject action

# __9\. COMPONENT LIBRARY – BUTTONS__

## __9\.1 Button Variants__

__Variant__

__Background__

__Text__

__Border__

__Sử dụng__

__Primary__

\#2E75B6

\#FFFFFF

none

CTA chính: Lưu, Submit, Tạo mới, Xác nhận

__Secondary__

\#F2F2F2

\#2C3E50

\#BFBFBF

Hành động phụ: Hủy, Đóng, Trở lại

__Danger__

\#DC3545

\#FFFFFF

none

Xóa, Hủy đơn – luôn confirm trước

__Ghost__

transparent

\#2E75B6

\#2E75B6

Icon button, toolbar action

__Success__

\#28A745

\#FFFFFF

none

Duyệt, Xác nhận QC ĐẠT

Disabled

\#E9ECEF

\#6C757D

none

Disabled state – không có pointer\-events

### __9\.2 Button Component Props__

__Property__

__Type__

__Default__

__Description__

variant

'primary'|'secondary'|'danger'|'ghost'|'success'

'primary'

Màu sắc và style của button

size

'xs'|'sm'|'md'|'lg'

'md'

xs:24px, sm:28px, md:32px, lg:40px height

icon

string \(icon name\)

undefined

Remix icon name hiện trước label

icon\-right

string

undefined

Remix icon name hiện sau label

loading

boolean

false

Hiện spinner, disable click

disabled

boolean

false

Disable state, giảm opacity 0\.5

full\-width

boolean

false

width: 100% – dùng trong mobile form

confirm

string

undefined

Nếu set: hiện confirm dialog trước khi emit click

## __9\.3 Button Sizing__

__Size__

__Height__

__Padding H__

__Font size__

__Sử dụng__

__xs__

24px

8px

12px

Compact table row action

__sm__

28px

12px

13px

Sidebar action, filter chip

__md__

32px

16px

14px

Standard form button, toolbar

__lg__

40px

20px

16px

Page CTA, mobile primary action

# __10\. COMPONENT LIBRARY – FORM CONTROLS__

## __10\.1 Input States__

__State__

__Border__

__Background__

__Mô tả__

__Default__

\#BFBFBF

\#FFFFFF

Trạng thái bình thường chưa tương tác

__Hover__

\#2E75B6

\#EBF5FB

Mouse\-over: highlight nhẹ border và bg

__Focus__

\#2E75B6 \(3px ring\)

\#FFFFFF

Focus ring xanh: keyboard nav, a11y bắt buộc

__Filled__

\#BFBFBF

\#FFFFFF

Đã nhập dữ liệu – style giống default

__Disabled__

\#E9ECEF

\#F2F2F2

Không thể edit – giảm opacity text

__Error__

\#DC3545

\#FFF5F5

Validation fail: đỏ \+ icon ⚠ \+ message

__Success__

\#28A745

\#F0FFF4

Validation pass: xanh \+ icon ✓

## __10\.2 Form Layout Rules__

__Quy tắc__

__Chi tiết__

__Label placement__

Label trên input \(top\-aligned\)\. Không dùng placeholder làm label\. Required field: dấu \* đỏ sau label

__Field width__

Full\-width trong mobile\. Desktop: 2–4 cols 12\-col grid\. Trường ngày/giờ: max 180px\. Trường số: max 120px

__Validation timing__

Validate on\-blur \(không validate ngay khi gõ, trừ format\)\. Hiện error message dưới input, màu đỏ, có icon

__Group & Section__

Nhóm các field liên quan bằng fieldset \+ legend\. Section divider: đường kẻ 1px \#BFBFBF \+ heading

__Required vs Optional__

Đánh dấu field bắt buộc \(\*\)\. Field optional có thể thêm '\(tùy chọn\)' nhỏ bên cạnh label

__Character count__

Textarea có character limit: hiện counter 'x/500'\. Đỏ khi > 90%

__Autocomplete__

Link\-field \(Select NCC, Select vật tư\): dropdown search với debounce 300ms, min 2 ký tự

# __11\. COMPONENT LIBRARY – TABLES & LISTS__

## __11\.1 Data Table Variants__

__Variant__

__Đặc điểm & Sử dụng__

__Standard List__

Header row: \-\-sc\-primary\-dark \+ white text\. Body: zebra stripe FFFFFF / F2F2F2\. Dùng cho tất cả List DocType

__Child Table__

Inline trong Form \(PO items, Receipt items\)\. Header: LIGHT\_BLUE\. Rows: editable\. Add/Remove buttons cuối

__Report Table__

Report Builder output\. Sortable, filterable\. Export Excel/PDF\. Group\-by support với subtotal row

__Summary Table__

Dashboard widget: 5–10 rows, 3–5 cols\. Compact padding\. Click row → navigate to detail

__Comparison Table__

So sánh giá NCC, đối soát tồn kho\. Highlighted diff cells màu YELLOW\_BG hoặc RED\_BG

## __11\.2 Table Rules__

__Quy tắc__

__Chi tiết__

__Column alignment__

Text: left\-align\. Số lượng, đơn giá, thành tiền: right\-align\. Mã, trạng thái, ngày: center\-align

__Row height__

Standard: 36px\. Compact \(report\): 28px\. Form child table: 40px \(dễ click\)

__Sticky header__

List view > 10 rows: sticky table header\. Sidebar scroll độc lập với content

__Pagination__

Default: 20 rows/page\. Options: 20, 50, 100\. Hiện 'Trang X / Y – Tổng Z bản ghi'

__Row selection__

Checkbox đầu dòng cho bulk action\. Highlighted row: \-\-sc\-primary\-light bg

__Empty state__

Khi không có dữ liệu: icon minh họa \+ 'Chưa có dữ liệu' \+ CTA button 'Tạo mới'

__Loading state__

Skeleton rows \(shimmer animation\) trong khi fetch\. KHÔNG dùng spinner che toàn bảng

# __12\. COMPONENT LIBRARY – CARDS & PANELS__

## __12\.1 Card Variants__

__Card Type__

__Shadow__

__Sử dụng__

__KPI Card__

\-\-sc\-shadow\-md

Dashboard: metric number lớn, delta indicator, sparkline mini chart

__Summary Card__

\-\-sc\-shadow\-sm

Thông tin tổng hợp 1 entity: NCC, Hợp đồng, Vật tư

__Alert Card__

\-\-sc\-shadow\-md

Cảnh báo tồn kho, sắp hết hạn – màu nền theo severity

__Stats Card__

\-\-sc\-shadow\-sm

Tỷ lệ, biểu đồ nhỏ, progress bar

__Action Card__

\-\-sc\-shadow\-sm

Quick action: Tạo PO, Scan barcode, Kiểm kê nhanh

## __12\.2 KPI Card Anatomy__

Tổng tồn kho

__1,247__

▲ \+3\.2% so tháng trước

Cảnh báo tồn kho

__8__

mặt hàng dưới ngưỡng tối thiểu

Sắp hết hạn \(30 ngày\)

__3__

lô vật tư hết hạn trước 31/05/2026

# __13\. COMPONENT LIBRARY – BADGES & TAGS__

## __13\.1 Status Badge__

Status badge dùng để hiển thị trạng thái DocType trong List view và Form header\. Luôn dùng cả màu \+ text – KHÔNG chỉ dùng màu\.

__Trạng thái__

__Màu nền__

__Text__

__Áp dụng cho__

__Draft / Nháp__

\#F2F2F2

\#6C757D

PO, Receipt, Dispensing mới tạo

__Pending / Chờ duyệt__

\#FFF2CC

\#856404

Workflow stage 1: chờ Manager duyệt

__Submitted / Đã gửi__

\#D6E4F0

\#1F4E79

Đã submit, chờ xử lý tiếp

__Approved / Đã duyệt__

\#E2EFDA

\#155724

Workflow hoàn thành, được duyệt

__Rejected / Từ chối__

\#FCE4D6

\#721C24

Workflow bị từ chối, cần sửa

__On Hold / Tạm dừng__

\#FCE9D6

\#7D4707

Bị giữ lại chờ thêm thông tin

__Cancelled / Hủy__

\#F2F2F2

\#495057

Đã hủy – strikethrough text

__Completed / Hoàn thành__

\#28A745

\#FFFFFF

Đã xử lý xong toàn bộ

__Overdue / Quá hạn__

\#DC3545

\#FFFFFF

Deadline đã qua – blink animation nhẹ

__Partial__

\#EBF5FB

\#1F4E79

Nhận/cấp phát một phần

## __13\.2 Tag / Chip Component__

__Tag Type__

__Mô tả & Sử dụng__

__BHYT Code__

Hiện mã N01–N09 bên cạnh tên vật tư\. Màu nền: LIGHT\_BLUE\. Click → filter theo nhóm BHYT

__Warehouse Tag__

Tên kho: 'Kho Tổng', 'Ngoại khoa'\. Màu nền: GRAY\_BG\. Non\-interactive

__Expiry Tag__

Hạn dùng: 'Hết hạn 15/06/2026'\. Màu: YELLOW\_BG nếu < 30 ngày; RED\_BG nếu < 7 ngày

__Lot Tag__

Số lô: 'LOT\-G\-202601'\. Font: monospace\. Copy\-on\-click behavior

__Unit Tag__

Đơn vị tính: 'Hộp', 'Đôi', 'Lọ'\. Màu: plain gray\. Non\-interactive

# __14\. COMPONENT LIBRARY – NAVIGATION__

## __14\.1 Sidebar Navigation__

__Element__

__Spec__

__Width__

260px desktop / 240px laptop / 0px \(hidden\) mobile

__Background__

\#2C3E50 \(Charcoal\)

__Active item__

Background: \#2E75B6 \+ left border 3px \#FFFFFF \+ text bold white

__Hover item__

Background: rgba\(255,255,255,0\.08\) \+ text white

__Icon__

24×24px, Remix icon, color: \#AACCEE \(muted blue\)

__Text__

Inter 14px Regular, color: \#D0D8E4

__Group header__

ALL CAPS, 11px, letter\-spacing 1px, color: \#7A9CC0

__Collapse__

Arrow icon, rotate 90° on expand\. Sub\-items indent 16px

__Badge__

Notification count: red circle, top\-right icon corner

__Scroll__

Auto scroll khi > viewport\. Sticky module group header

## __14\.2 Breadcrumb__

Home > Module > SubModule > Document ID \(truncate nếu > 4 levels, hiện … giữa\)

• Font: 13px, color: \#6C757D\. Separator: ' > ' màu \#BFBFBF

• Last item: bold, color: \#2C3E50, không có link

• Mobile: chỉ hiện item trước và item hiện tại

## __14\.3 Tabs__

__State__

__Style__

__Active tab__

Border\-bottom: 2px solid \#2E75B6\. Text: bold \#1F4E79

__Inactive tab__

Text: \#6C757D\. Hover: text \#2E75B6, border\-bottom 1px

__Disabled tab__

Opacity 0\.4, cursor not\-allowed

__Tab with badge__

Count badge bên phải tab label – dùng cho cảnh báo

__Responsive__

Mobile: scroll horizontally\. Hoặc dùng Select dropdown thay tabs nếu > 5 tabs

# __15\. COMPONENT LIBRARY – MODALS & ALERTS__

## __15\.1 Modal Dialog__

__Modal Type__

__Max Width__

__Sử dụng__

__Confirm Dialog__

400px

Xóa, hủy, approve – 2 button: Confirm \+ Cancel

__Form Modal__

600px

Tạo nhanh \(Quick Entry\) NCC, vật tư, danh mục

__Large Modal__

900px

Xem chi tiết, preview PDF, chọn từ list dài

__Full Screen__

100vw

Scan barcode PDA, camera capture, map view

__Notification__

320px \(toast\)

Success/Error/Warning toast – auto\-dismiss 4s

## __15\.2 Toast / Notification Rules__

__Type__

__Icon__

__Duration__

__Ví dụ message__

__Success__

✅ ri\-check\-circle

4 giây

'PO\-2026\-00052 đã được lưu thành công'

__Error__

❌ ri\-error\-warning

Không tự tắt

'Lỗi: Mã vật tư VT\-001 đã tồn tại'

__Warning__

⚠️ ri\-alert

6 giây

'Tồn kho Gang tay sắp dưới ngưỡng tối thiểu'

__Info__

ℹ️ ri\-information

4 giây

'Đồng bộ PDA hoàn tất: 45 bản ghi'

__Loading__

⏳ spinner

Đến khi xong

'Đang xuất báo cáo Excel\.\.\.'

## __15\.3 Alert Banner \(Inline\)__

__⚠ CẢNH BÁO: 3 lô vật tư sẽ hết hạn trong 7 ngày\. Vui lòng xử lý trước 12/05/2026\.__

⚠ Lưu ý: Hợp đồng SC\-FC\-2026\-00003 còn hạn mức 127,600,000 VND – thấp hơn 20% hạn mức ban đầu\.

✅ Kiểm kê tháng 4/2026 đã hoàn tất\. Độ chênh lệch: 0\.3%\. Xem báo cáo đối soát\.

# __16\. MOTION & ANIMATION__

__Token__

__Value__

__Sử dụng__

\-\-sc\-duration\-instant

80ms

Hover state, focus ring

\-\-sc\-duration\-fast

150ms

Button click feedback, badge appear

\-\-sc\-duration\-normal

250ms

Modal open/close, dropdown, toast slide

\-\-sc\-duration\-slow

400ms

Page transition, sidebar expand

\-\-sc\-easing\-standard

cubic\-bezier\(0\.4, 0, 0\.2, 1\)

Phần lớn transitions

\-\-sc\-easing\-enter

cubic\-bezier\(0, 0, 0\.2, 1\)

Elements entering screen

\-\-sc\-easing\-exit

cubic\-bezier\(0\.4, 0, 1, 1\)

Elements leaving screen

__Quy tắc Animation__

__Chi tiết__

__Purposeful only__

Chỉ animate khi có mục đích: hướng dẫn sự chú ý, phản hồi action, chuyển cảnh

__Bệnh viện context__

Tránh animation phức tạp, flash, blink – có thể gây xao nhãng nhân viên y tế

__Reduced motion__

Luôn respect prefers\-reduced\-motion: reduce – tắt hoặc đơn giản hóa animation

__Loading feedback__

Skeleton shimmer \(không spinner che content\)\. Progress bar cho action dài > 2 giây

__Error shake__

Input lỗi: shake 3px horizontal, 3 lần, 300ms – chỉ khi validate fail

__Overdue blink__

Badge 'Quá hạn': opacity 1→0\.5→1, 1\.5s infinite – subtle, không gây phiền

# __17\. ACCESSIBILITY GUIDELINES__

## __17\.1 WCAG 2\.1 AA Compliance__

__Tiêu chí__

__Level__

__Yêu cầu SupplyCore__

__1\.1\.1 Non\-text Content__

AA

Tất cả icon chức năng có aria\-label\. Biểu đồ có alt text mô tả dữ liệu

__1\.3\.1 Info & Relationships__

AA

Table có scope header\. Form có label liên kết với input \(for/id\)

__1\.4\.1 Use of Color__

AA

Trạng thái phân biệt bằng màu \+ icon \+ text\. Không chỉ dùng màu

__1\.4\.3 Contrast \(Text\)__

AA

Text thường: 4\.5:1 min\. Text lớn \(≥18px\): 3:1 min

__1\.4\.4 Resize Text__

AA

Text scale đến 200% không mất nội dung, không scroll ngang

__2\.1\.1 Keyboard__

AA

Tất cả action thực hiện được bằng keyboard\. Tab order logic

__2\.4\.3 Focus Order__

AA

Focus visible: \-\-sc\-shadow\-focus ring 3px\. Không mất focus

__2\.4\.6 Headings__

AA

H1–H4 phân cấp đúng trên mỗi trang\. Không skip level

__3\.2\.2 On Input__

AA

Không thay đổi context khi chỉ focus \(trừ khi có thông báo rõ\)

__4\.1\.3 Status Messages__

AA

Toast/Alert dùng role='alert' hoặc aria\-live='polite'

# __18\. DESIGN TOKENS – BẢNG TỔNG HỢP__

Tất cả design token được định nghĩa trong file CSS: supplycore/public/css/design\-tokens\.css và áp dụng toàn bộ qua :root \{ \} selector\.

__Nhóm__

__CSS Variables__

__Colors__

\-\-sc\-primary\-dark, \-\-sc\-primary, \-\-sc\-primary\-light, \-\-sc\-primary\-xlight
\-\-sc\-success, \-\-sc\-success\-light, \-\-sc\-warning, \-\-sc\-warning\-light
\-\-sc\-error, \-\-sc\-error\-light, \-\-sc\-orange\-light
\-\-sc\-neutral\-dark, \-\-sc\-neutral, \-\-sc\-neutral\-light, \-\-sc\-border, \-\-sc\-white

__Typography__

\-\-sc\-font\-body: 'Inter', \-apple\-system, sans\-serif
\-\-sc\-font\-mono: 'JetBrains Mono', 'Courier New', monospace
\-\-sc\-text\-display / h1 / h2 / h3 / body\-lg / body / body\-sm / caption / mono

__Spacing__

\-\-sc\-space\-1\(4px\) / 2\(8px\) / 3\(12px\) / 4\(16px\) / 5\(20px\)
\-\-sc\-space\-6\(24px\) / 8\(32px\) / 10\(40px\) / 12\(48px\) / 16\(64px\)

__Shadows__

\-\-sc\-shadow\-none / sm / md / lg / xl / focus

__Borders__

\-\-sc\-border\-color / focus / error / success
\-\-sc\-radius\-sm\(4px\) / md\(6px\) / lg\(8px\) / xl\(12px\) / full\(9999px\)

__Animation__

\-\-sc\-duration\-instant\(80ms\) / fast\(150ms\) / normal\(250ms\) / slow\(400ms\)
\-\-sc\-easing\-standard / enter / exit

__SupplyCore Design System v1\.0__

18 sections | Color Palette · Typography · Spacing · Components · Tokens

Frappe Framework v15 \+ ERPNext v15 | Phase 3 – Document 14/20

