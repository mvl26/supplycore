__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung ứng Vật tư Y tế Bệnh viện

__CHANGE CONTROL PROCESS__

Quy trình Quản lý Thay đổi  |  Phiên bản 1\.0  |  05/2026

__Áp dụng cho__

Dự án SupplyCore – Tất cả các phase

__Phiên bản__

1\.0 – Ban hành lần đầu

__Chủ sở hữu tài liệu__

Project Manager – MedCons Vietnam

__Ngày hiệu lực__

01/05/2026

__Xét duyệt__

Change Control Board \(CCB\) – họp định kỳ 2 tuần/lần

# __1\. Mục đích & Phạm vi__

Tài liệu này mô tả quy trình chính thức để quản lý mọi yêu cầu thay đổi \(Change Request – CR\) đối với dự án SupplyCore, bao gồm thay đổi phạm vi, yêu cầu kỹ thuật, thiết kế hệ thống, timeline, ngân sách và các tài liệu đã được ký duyệt \(baselined documents\)\.

## __1\.1 Áp dụng cho__

- Thay đổi phạm vi chức năng \(thêm/bớt/sửa module, use case, tính năng\)
- Thay đổi yêu cầu kỹ thuật \(tech stack, architecture, API, database schema\)
- Thay đổi timeline hoặc ngân sách dự án
- Thay đổi tài nguyên \(nhân sự chủ chốt, công cụ, môi trường\)
- Thay đổi quy trình nghiệp vụ sau khi đã được ký duyệt trong BRD/URS

## __1\.2 Không áp dụng cho__

- Bug fix thông thường trong nội bộ sprint \(xử lý qua Bug Tracker\)
- Cải tiến nhỏ về UI/UX trong phạm vi thiết kế đã duyệt
- Thay đổi nội bộ không ảnh hưởng đến deliverable hay timeline

# __2\. Change Control Board \(CCB\)__

CCB là cơ quan phê duyệt tối cao đối với các yêu cầu thay đổi dự án\.

__Thành viên__

__Vai trò trong CCB__

__Quyền biểu quyết__

__Điều kiện Quorum__

Project Sponsor

Chủ tịch CCB

Có – Quyết định cuối

Bắt buộc có mặt

Project Manager

Thư ký CCB

Có

Bắt buộc có mặt

Business Analyst

Đánh giá tác động nghiệp vụ

Có

Bắt buộc có mặt

Technical Lead

Đánh giá tác động kỹ thuật

Có

Bắt buộc có mặt

Đại diện Bệnh viện

Xác nhận phía khách hàng

Có

Ít nhất 1 trong 2 đại diện

QA Lead

Đánh giá tác động kiểm thử

Tư vấn

Không bắt buộc

Quorum: Tối thiểu 4/6 thành viên có quyền biểu quyết phải có mặt\. Quyết định theo đa số; trường hợp hòa 3\-3 thì Project Sponsor có quyền quyết định cuối cùng\.

# __3\. Quy trình Thay đổi__

## __3\.1 Sơ đồ tổng thể__

Quy trình gồm 7 bước tuần tự từ đề xuất đến đóng CR:

__1__

__Đề xuất Thay đổi \(Change Request Submission\)__

Bất kỳ thành viên nào điền form CR; gửi tới PM trong vòng 1 ngày làm việc\.

__Thời hạn:__

Ngay khi phát sinh

__2__

__Tiếp nhận & Phân loại \(Logging & Classification\)__

PM ghi CR vào Change Log; phân loại theo mức độ ưu tiên và loại thay đổi\.

__Thời hạn:__

1 ngày làm việc

__3__

__Đánh giá Tác động \(Impact Assessment\)__

BA & Tech Lead đánh giá tác động về phạm vi, effort, cost, timeline, rủi ro\.

__Thời hạn:__

2–5 ngày làm việc

__4__

__Trình CCB \(CCB Review\)__

PM trình bày CR và Impact Assessment tại phiên họp CCB định kỳ hoặc họp khẩn\.

__Thời hạn:__

CCB họp 2 tuần/lần

__5__

__Phê duyệt / Từ chối \(Decision\)__

CCB bỏ phiếu: Chấp thuận / Từ chối / Hoãn / Yêu cầu thêm thông tin\.

__Thời hạn:__

Trong phiên họp CCB

__6__

__Thực hiện & Cập nhật tài liệu \(Implementation\)__

Nếu được duyệt: cập nhật Baseline Documents, kế hoạch sprint, ngân sách\.

__Thời hạn:__

Theo kế hoạch được duyệt

__7__

__Đóng CR & Xác nhận \(Closure & Verification\)__

QA xác nhận thay đổi đã triển khai đúng; PM đóng CR và lưu hồ sơ\.

__Thời hạn:__

Sau khi verify hoàn thành

## __3\.2 Phân loại Mức độ Thay đổi__

__Cấp độ__

__Phân loại__

__Tiêu chí__

__Người phê duyệt__

__Thời gian xét duyệt__

__Ví dụ__

Cấp 1

Minor

Không ảnh hưởng timeline/budget; effort < 4 giờ

PM

1 ngày LV

Sửa nhãn hiển thị, thêm cột báo cáo nhỏ

Cấp 2

Moderate

Ảnh hưởng < 1 sprint; effort 4h–3 ngày; budget < 5%

PM \+ Tech Lead

3 ngày LV

Thêm trường dữ liệu mới, điều chỉnh quy trình nhỏ

Cấp 3

Major

Ảnh hưởng > 1 sprint hoặc budget 5–15%

CCB đầy đủ

Phiên họp CCB gần nhất

Thêm module mới, thay đổi kiến trúc

Cấp 4

Critical

Ảnh hưởng milestone, Go\-Live hoặc budget > 15%

CCB \+ Sponsor

Họp khẩn trong 48h

Thay đổi tech stack, trì hoãn Go\-Live

# __4\. Change Request Form \(Mẫu CR\)__

Tất cả CR phải được điền đầy đủ vào mẫu sau trước khi gửi PM:

__Thông tin CR__

__Nội dung điền__

__CR ID__

CR\-\[YYYY\]\-\[NNN\]  \(Ví dụ: CR\-2026\-001\)

__Ngày đề xuất__

DD/MM/YYYY

__Người đề xuất__

Họ tên, vai trò, đơn vị

__Tiêu đề CR__

Mô tả ngắn gọn thay đổi đề xuất

__Mô tả chi tiết__

Mô tả đầy đủ nội dung thay đổi, lý do, lợi ích mong đợi

__Ảnh hưởng đến__

Phạm vi / Thiết kế / Kỹ thuật / Timeline / Ngân sách / Tài liệu nào?

__Mức độ ưu tiên__

Khẩn cấp / Cao / Bình thường / Thấp

__Ước tính effort__

Số giờ/ngày công ước tính \(BA \+ Dev \+ QA\)

__Tác động tài chính__

Thêm chi phí ước tính \(nếu có\)

__Tác động rủi ro__

Rủi ro nếu thực hiện / nếu không thực hiện

__Tài liệu đính kèm__

Mockup, spec, email liên quan\.\.\.

__Quyết định CCB__

\[ \] Chấp thuận   \[ \] Từ chối   \[ \] Hoãn   \[ \] Cần thêm thông tin

__Ghi chú CCB__

Lý do quyết định, điều kiện kèm theo \(nếu có\)

__Ngày quyết định__

DD/MM/YYYY

__Chữ ký Sponsor__

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

# __5\. Change Log – Sổ theo dõi CR__

PM duy trì Change Log cập nhật liên tục trong suốt dự án:

__CR ID__

__Ngày đề xuất__

__Tiêu đề__

__Người đề xuất__

__Cấp độ__

__Trạng thái__

__Ngày quyết định__

__Kết quả__

__Sprint thực hiện__

CR\-2026\-001

10/01/2026

Thêm trường "Mã BHYT" vào phiếu nhập kho

Kế toán BV

Cấp 2

Đã duyệt

15/01/2026

Chấp thuận

Sprint 2

CR\-2026\-002

20/02/2026

Tích hợp SMS alert khi tồn kho thấp

Trưởng Khoa VTYT

Cấp 3

Đang xét duyệt

—

—

—

CR\-2026\-003

05/03/2026

Bỏ yêu cầu offline mode cho PDA

Technical Lead

Cấp 3

Từ chối

10/03/2026

Từ chối – Offline là yêu cầu bắt buộc

—

\(Change Log được cập nhật sau mỗi phiên họp CCB và lưu trong SharePoint/Google Drive dự án\)

# __6\. Quy tắc Bổ sung__

## __6\.1 Emergency Change \(Thay đổi Khẩn cấp\)__

Trong trường hợp cần thay đổi khẩn cấp ảnh hưởng đến production hoặc Go\-Live:

1. PM có quyền phê duyệt tạm thời \(interim approval\) để thực hiện ngay
2. Trong vòng 24 giờ, phải hoàn thiện CR form và trình CCB xem xét
3. CCB họp khẩn \(virtual\) trong vòng 48 giờ để phê duyệt chính thức hoặc rollback

## __6\.2 Freeze Period \(Giai đoạn Đóng băng\)__

Trong các giai đoạn sau, KHÔNG chấp nhận CR mức Cấp 3 và Cấp 4:

- 2 tuần trước UAT lần 1 \(từ 17/08/2026\)
- 2 tuần trước Go\-Live \(từ 17/09/2026\)
- Trong thời gian Hypercare \(tháng 10–12/2026\) – chỉ CR critical bug

## __6\.3 Lưu trữ Hồ sơ__

- Tất cả CR form, biên bản họp CCB được lưu trữ trong thư mục Change Management của dự án
- Thời gian lưu trữ: tối thiểu 5 năm sau khi dự án kết thúc
- Quyền truy cập: PM, BA, Sponsor, IT Bệnh viện \(read\-only\)

