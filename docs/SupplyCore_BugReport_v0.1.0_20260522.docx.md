**BÁO CÁO CÁC VẤN ĐỀ & ĐỀ XUẤT CẢI THIỆN**

**Hệ thống SupplyCore \- Cung ứng Bệnh viện (v0.1.0)**

| Người thực hiện | Đội Kiểm thử / Triển khai |
| :---- | :---- |
| **Ngày kiểm thử** | 22/05/2026 |
| **Môi trường** | https://asset.miyano.com.vn/supplycore/ |
| **Phiên bản** | v0.1.0 |
| **Tài khoản test** | Miyano Viet Nam (role: User) |
| **Trình duyệt** | Chrome (latest) |
| **Số vấn đề ghi nhận** | 15 (1 Blocker, 1 High, 7 Medium, 6 Low) |

 

# **1\. Tóm tắt điều hành**

Sau phiên kiểm thử hệ thống SupplyCore phiên bản v0.1.0, đội kiểm thử đã ghi nhận tổng cộng 15 vấn đề bao gồm bug chức năng, vấn đề UX, thiếu hụt tính năng và rủi ro hiệu năng. Trong đó có 01 lỗi Blocker liên quan đến cấu trúc dữ liệu phân cấp (NestedSet) khiến KHÔNG thể tạo Nhóm vật tư và Kho \- làm tê liệt toàn bộ luồng nghiệp vụ end-to-end. Đề nghị đội Phát triển ưu tiên xử lý các vấn đề mức P0/P1 trước khi tổ chức demo cho khách hàng hoặc đưa vào UAT.

 

### **Thống kê vấn đề theo mức ưu tiên**

| Mức ưu tiên | Số lượng | Mô tả |
| :---- | :---- | :---- |
| **P0 \- Blocker** | 1 | Lỗi nghiêm trọng chặn vận hành, phải fix ngay trước mọi hoạt động khác |
| **P1 \- High** | 1 | Lỗi ảnh hưởng nghiệp vụ chính, fix trong sprint hiện tại |
| **P2 \- Medium** | 7 | Vấn đề trung bình, ảnh hưởng UX hoặc tuân thủ, fix trong 1-2 sprint tới |
| **P3 \- Low** | 6 | Cải thiện chất lượng, đưa vào backlog |

 

# **2\. Chi tiết các vấn đề & hướng cải thiện**

## **1\. \[BUG-001\] Lỗi backend "lft" trên các DocType có cấu trúc cây**

| Mã vấn đề | BUG-001 |
| :---- | :---- |
| **Mức độ** | Blocker |
| **Module liên quan** | M0 \- Dữ liệu nền / M4 \- Quản lý kho |
| **Đối tượng ảnh hưởng** | SC Item Group, SC Warehouse (có thể cả Bin Location, SC Department dạng cây) |
| **Mô tả vấn đề** | Khi nhấn Lưu trên form tạo Nhóm vật tư hoặc Kho, hệ thống trả về toast lỗi: "'SCItemGroup' object has no attribute 'lft'" hoặc "'SCWarehouse' object has no attribute 'lft'". Bản ghi KHÔNG được lưu vào DB. Hậu quả: không thể tạo nhóm vật tư, không thể tạo kho, từ đó chặn toàn bộ luồng nghiệp vụ (MR, PO, Receipt, Putaway, Transfer, Dispense, Stock Reconciliation). |
| **Tác động nghiệp vụ** | Toàn bộ luồng end-to-end (MR \-\> PO \-\> Receipt \-\> Putaway \-\> Dispense) không thực hiện được. Hệ thống ở trạng thái KHÔNG THỂ DEMO cho khách hàng. |
| **Đề xuất cải thiện** | Bổ sung các trường lft, rgt, is\_group, old\_parent vào schema (NestedSet doctype). Trong class Python, kế thừa frappe.utils.nestedset.NestedSet và override on\_update/on\_trash. Đồng thời thêm hook before\_insert để khởi tạo lft=0, rgt=0 tránh lỗi attribute. Sau khi fix cần viết unit test cho hierarchical CRUD. |
| **Ưu tiên xử lý** | P0 \- Khẩn cấp, fix ngay |

 

## **2\. \[BUG-002\] Form Supplier thiếu hiển thị trường bắt buộc "Loại NCC"**

| Mã vấn đề | BUG-002 |
| :---- | :---- |
| **Mức độ** | High |
| **Module liên quan** | M0 \- Dữ liệu nền |
| **Đối tượng ảnh hưởng** | SC Supplier (form Tạo Nhà cung cấp) |
| **Mô tả vấn đề** | Khi điền đủ Tên NCC, Mã số thuế, Email, Điện thoại, Địa chỉ, Xếp hạng và nhấn Lưu, hệ thống báo lỗi: "Error: Value missing for SC Supplier: Loại NCC". Tuy nhiên trên UI KHÔNG có field "Loại NCC" để người dùng nhập. Field bị ẩn hoặc bị quên render. |
| **Tác động nghiệp vụ** | Không thể tạo Nhà cung cấp qua UI \-\> không có dữ liệu NCC cho PO, Contract, Invoice. |
| **Đề xuất cải thiện** | Bổ sung dropdown "Loại NCC" lên form Supplier với các giá trị: Trong nước / Nước ngoài / Cá nhân / Tổ chức (hoặc theo nghiệp vụ thực tế). Hoặc nếu field bị quên: kiểm tra form schema (JSON config) đảm bảo loai\_ncc có thuộc tính hidden=0 và in\_create=1. Set default value để legacy data không bị crash. |
| **Ưu tiên xử lý** | P1 \- Cao, fix trong sprint hiện tại |

 

## **3\. \[BUG-003\] Phân quyền Submit chưa được cấu hình cho role mặc định**

| Mã vấn đề | BUG-003 |
| :---- | :---- |
| **Mức độ** | Medium |
| **Module liên quan** | Workflow / Người dùng & Quyền |
| **Đối tượng ảnh hưởng** | Tất cả DocType có workflow (SC UOM, SC Item, SC Department, SC Material Request, ...) |
| **Mô tả vấn đề** | Tài khoản đăng nhập với role "User" (Miyano Viet Nam) nhấn nút "Gửi duyệt" trên bản ghi UOM nhận lỗi: "Không có quyền submit SC UOM Hộp". Bản ghi chỉ giữ ở trạng thái Nháp. |
| **Tác động nghiệp vụ** | Không đẩy được bản ghi qua workflow approval; nếu demo cho khách hàng phải đăng nhập role khác. Khó test luồng duyệt đầy đủ. |
| **Đề xuất cải thiện** | Rà soát ma trận phân quyền (Role Permission Manager): role nào được quyền Submit/Cancel/Amend trên từng DocType. Tạo sẵn các role demo có quyền đầy đủ: SupplyCore Executive, SupplyCore Manager, SupplyCore Storekeeper. Cung cấp tài liệu Permission Matrix cho người triển khai. |
| **Ưu tiên xử lý** | P2 \- Trung bình |

 

## **4\. \[DATA-001\] Môi trường trống hoàn toàn, không có dữ liệu mẫu**

| Mã vấn đề | DATA-001 |
| :---- | :---- |
| **Mức độ** | Medium |
| **Module liên quan** | Toàn hệ thống |
| **Đối tượng ảnh hưởng** | Tất cả module M0-M11 |
| **Mô tả vấn đề** | Mọi card trên Dashboard và Module hiển thị "0 bản ghi", "Chưa có dữ liệu". Không có master data mẫu (UOM, Item Group, Item, Supplier, Warehouse, Department) để người dùng mới khám phá tính năng. Người demo phải tự tạo dữ liệu từ đầu, nhưng vì BUG-001 nên KHÔNG thể tạo được hierarchical data. |
| **Tác động nghiệp vụ** | Trải nghiệm tệ khi demo, không thể minh họa biểu đồ (Xu hướng chi phí 12 tháng, Top 10 vật tư tiêu thụ, Cảnh báo). |
| **Đề xuất cải thiện** | Tạo bộ seed data "demo fixture" gồm: \~5 UOM (Hộp, Viên, Vỉ, Chai, Ống), \~10 Item Group (Kháng sinh, Giảm đau, Vật tư tiêu hao, ...), \~50 Item phổ biến trong bệnh viện, 5 Supplier, 5 Department, 3 Warehouse với hierarchy, vài Framework Contract, 1-2 PO đã hoàn thành, vài lô có expiry để demo cảnh báo. Cung cấp lệnh CLI: bench \--site demo install-app supplycore\_demo\_data. |
| **Ưu tiên xử lý** | P2 \- Trung bình |

 

## **5\. \[UX-001\] Thông báo lỗi kỹ thuật lộ ra UI người dùng cuối**

| Mã vấn đề | UX-001 |
| :---- | :---- |
| **Mức độ** | Medium |
| **Module liên quan** | Toàn hệ thống |
| **Đối tượng ảnh hưởng** | Toast notification |
| **Mô tả vấn đề** | Khi gặp lỗi backend, hệ thống hiển thị raw exception cho người dùng cuối, ví dụ: "'SCItemGroup' object has no attribute 'lft'". Người dùng nghiệp vụ (thủ kho, dược viên, kế toán) không hiểu nội dung này. |
| **Tác động nghiệp vụ** | Trải nghiệm chuyên nghiệp giảm, người dùng hoang mang, không biết nên làm gì tiếp theo. Lộ chi tiết kỹ thuật ra ngoài (có thể coi là lỗ hổng info disclosure nhẹ). |
| **Đề xuất cải thiện** | Wrap exception ở backend, map về thông báo nghiệp vụ thân thiện. Log chi tiết kỹ thuật vào server log \+ show error code. Ví dụ: "Có lỗi hệ thống khi lưu Nhóm vật tư. Mã lỗi: SC-IG-001. Vui lòng liên hệ quản trị viên." Tạo trang Error Log để admin tra cứu. |
| **Ưu tiên xử lý** | P2 \- Trung bình |

 

## **6\. \[UX-002\] Toast thông báo lỗi che khuất thông tin user (chồng lên header)**

| Mã vấn đề | UX-002 |
| :---- | :---- |
| **Mức độ** | Low |
| **Module liên quan** | UI/UX |
| **Đối tượng ảnh hưởng** | Toast component (top-right) |
| **Mô tả vấn đề** | Khi có lỗi/thông báo, toast hiển thị chồng lên khối thông tin user "Miyano Viet Nam / User" ở góc phải trên, khiến text bị chồng chéo, khó đọc. |
| **Tác động nghiệp vụ** | Ảnh hưởng thẩm mỹ, khó đọc thông báo. |
| **Đề xuất cải thiện** | Điều chỉnh z-index và vị trí container toast (ví dụ: top: 70px thay vì top: 12px), hoặc dùng slide-in panel riêng. Test với thông báo dài (multi-line) để đảm bảo không tràn. |
| **Ưu tiên xử lý** | P3 \- Thấp |

 

## **7\. \[UX-003\] Không có nút "Lưu nháp" rõ ràng & nút "Gửi duyệt" gây nhầm lẫn**

| Mã vấn đề | UX-003 |
| :---- | :---- |
| **Mức độ** | Low |
| **Module liên quan** | Workflow UI |
| **Đối tượng ảnh hưởng** | Form Chi tiết các DocType |
| **Mô tả vấn đề** | Khi mở form mới, có nút "Lưu" và sau khi lưu thì xuất hiện "Nháp / Hoàn tác / Lưu / Gửi duyệt". Người dùng mới khó hiểu sự khác biệt giữa Lưu (lưu sửa đổi) và Gửi duyệt (submit workflow). Không có tooltip giải thích. |
| **Tác động nghiệp vụ** | Người dùng có thể nhấn nhầm Gửi duyệt khi chưa hoàn thiện form. |
| **Đề xuất cải thiện** | Bổ sung tooltip cho từng nút. Khi hover "Gửi duyệt", giải thích: "Gửi bản ghi vào quy trình duyệt. Sau khi gửi duyệt sẽ không sửa được trừ khi Hủy duyệt." Cân nhắc confirm dialog trước khi submit. |
| **Ưu tiên xử lý** | P3 \- Thấp |

 

## **8\. \[UX-004\] Dropdown tìm kiếm Item Group không hỗ trợ "Tạo mới ngay" (inline create)**

| Mã vấn đề | UX-004 |
| :---- | :---- |
| **Mức độ** | Low |
| **Module liên quan** | M0 \- Form SC Item |
| **Đối tượng ảnh hưởng** | Dropdown Nhóm vật tư trên form Tạo Vật tư |
| **Mô tả vấn đề** | Khi tạo Item mới mà chưa có Item Group, dropdown chỉ hiển thị "Không có kết quả cho 'X'". Không có gợi ý "+ Tạo nhóm vật tư mới 'X'". |
| **Tác động nghiệp vụ** | Người dùng phải rời form Item, sang M0 tạo Item Group, rồi quay lại Item \-\> mất thao tác và dữ liệu nhập dở. |
| **Đề xuất cải thiện** | Thêm option "+ Tạo nhóm mới" trong dropdown khi không tìm thấy kết quả. Mở modal inline tạo Item Group, sau khi tạo xong auto-select vào field. Áp dụng cho mọi linked field (UOM, Supplier, Warehouse, Department). |
| **Ưu tiên xử lý** | P3 \- Thấp |

 

## **9\. \[UX-005\] Thiếu validation real-time ở client side**

| Mã vấn đề | UX-005 |
| :---- | :---- |
| **Mức độ** | Low |
| **Module liên quan** | Form validation |
| **Đối tượng ảnh hưởng** | Mọi form có required field |
| **Mô tả vấn đề** | Khi nhấn Lưu mà thiếu trường bắt buộc, hệ thống chỉ báo qua toast một dòng liệt kê. Field bắt buộc không được highlight đỏ (chỉ có dấu \* ở label). |
| **Tác động nghiệp vụ** | Khó nhận biết field nào thiếu, đặc biệt với form dài (Supplier, Item). |
| **Đề xuất cải thiện** | Highlight field thiếu (border đỏ) khi submit. Scroll auto đến field đầu tiên bị lỗi. Hiển thị error message ngay dưới field thay vì chỉ ở toast. |
| **Ưu tiên xử lý** | P3 \- Thấp |

 

## **10\. \[FEAT-001\] Không có chức năng Import dữ liệu từ Excel/CSV**

| Mã vấn đề | FEAT-001 |
| :---- | :---- |
| **Mức độ** | Medium |
| **Module liên quan** | M0 \- Dữ liệu nền |
| **Đối tượng ảnh hưởng** | Tất cả master data (Item, Supplier, Department, ...) |
| **Mô tả vấn đề** | Khi triển khai cho bệnh viện thật, cần nhập hàng ngàn item/supplier. Hiện tại trên list view có nút "Nhập" nhưng chưa kiểm chứng hoạt động. Cần xác minh và bổ sung tài liệu hướng dẫn template. |
| **Tác động nghiệp vụ** | Triển khai go-live mất rất nhiều thời gian nếu phải nhập tay từng record. |
| **Đề xuất cải thiện** | Hoàn thiện chức năng Import: cung cấp template Excel mẫu (.xlsx) có sẵn dropdown reference, validation, hướng dẫn ở sheet đầu. Hỗ trợ Preview trước khi commit, hiển thị lỗi từng dòng. Có thể bổ sung API REST/RPC để import từ HIS/ERP khác. |
| **Ưu tiên xử lý** | P2 \- Trung bình |

 

## **11\. \[FEAT-002\] Dashboard chưa có dữ liệu biểu đồ minh họa**

| Mã vấn đề | FEAT-002 |
| :---- | :---- |
| **Mức độ** | Low |
| **Module liên quan** | M11 \- Dashboard & Cảnh báo |
| **Đối tượng ảnh hưởng** | SCR-01 Dashboard điều hành |
| **Mô tả vấn đề** | Khu vực "Xu hướng chi phí 12 tháng" và "Top 10 vật tư tiêu thụ" hiển thị "Chưa có dữ liệu" do môi trường trống. Khi có dữ liệu, cần xác nhận chart render đúng (không có rủi ro NaN/divide-by-zero). |
| **Tác động nghiệp vụ** | Demo không trực quan, khó thuyết phục stakeholder về giá trị BI. |
| **Đề xuất cải thiện** | Sau khi seed demo data (DATA-001), kiểm thử biểu đồ: line chart, bar chart, treemap. Bổ sung tùy chọn "Xem dạng bảng" \+ "Export CSV" cho mỗi widget. Cân nhắc đưa biểu đồ về Apache ECharts hoặc Chart.js nếu chưa dùng. |
| **Ưu tiên xử lý** | P3 \- Thấp |

 

## **12\. \[FEAT-003\] Chưa có Audit Trail rõ ràng cho hành động người dùng**

| Mã vấn đề | FEAT-003 |
| :---- | :---- |
| **Mức độ** | Medium |
| **Module liên quan** | Bảo mật & Tuân thủ |
| **Đối tượng ảnh hưởng** | Toàn hệ thống |
| **Mô tả vấn đề** | Form có "Lịch sử sửa" nhưng chưa kiểm chứng độ chi tiết. Ngành y tế (bệnh viện) yêu cầu audit trail đầy đủ theo quy định Bộ Y tế (truy xuất ai \- làm gì \- khi nào \- giá trị cũ/mới). |
| **Tác động nghiệp vụ** | Có thể không đạt yêu cầu kiểm toán nội bộ/Bộ Y tế khi vận hành thực tế. |
| **Đề xuất cải thiện** | Đảm bảo mọi DocType bật field\_change\_log. Bổ sung Activity Log toàn cục cho login/logout, export, print. Cung cấp báo cáo Audit Trail có thể lọc theo người dùng/khoảng thời gian/DocType. Lưu trữ tối thiểu 5 năm theo quy định ngành y. |
| **Ưu tiên xử lý** | P2 \- Trung bình |

 

## **13\. \[FEAT-004\] Chưa thấy chức năng cảnh báo lô sắp hết hạn / dưới tồn an toàn theo email/SMS**

| Mã vấn đề | FEAT-004 |
| :---- | :---- |
| **Mức độ** | Medium |
| **Module liên quan** | M11 \- Cảnh báo / M5 \- Quản lý lô |
| **Đối tượng ảnh hưởng** | Notification system |
| **Mô tả vấn đề** | Dashboard hiển thị KPI "Lô sắp hết hạn 30 ngày", "Vật tư dưới tồn an toàn" nhưng chỉ là số đếm trên UI. Chưa thấy cấu hình notification qua email/SMS/Zalo cho các vai trò liên quan (Thủ kho, Dược trưởng). |
| **Tác động nghiệp vụ** | Người dùng phải vào hệ thống mới biết cảnh báo, có thể bỏ lỡ hàng hết hạn \-\> tổn thất tài chính & rủi ro y tế. |
| **Đề xuất cải thiện** | Bổ sung Notification Settings: ngưỡng cảnh báo (7 ngày / 30 ngày / 60 ngày trước hết hạn), tần suất (daily/weekly), kênh (Email/SMS/Zalo OA/Telegram). Tích hợp scheduler job chạy 6h sáng mỗi ngày. Cho phép escalation: nếu Thủ kho không xử lý trong 3 ngày \-\> gửi lên Manager. |
| **Ưu tiên xử lý** | P2 \- Trung bình |

 

## **14\. \[FEAT-005\] Phiên bản v0.1.0 \- thiếu changelog và roadmap công khai**

| Mã vấn đề | FEAT-005 |
| :---- | :---- |
| **Mức độ** | Low |
| **Module liên quan** | Quản lý phiên bản |
| **Đối tượng ảnh hưởng** | Footer hệ thống |
| **Mô tả vấn đề** | Footer hiển thị "v0.1.0 \- User" nhưng không có link đến Changelog/Release Notes. Khách hàng và team triển khai không biết tính năng mới nào vừa release, fix gì. |
| **Tác động nghiệp vụ** | Khó truyền thông cập nhật cho khách hàng, support khó tra cứu phiên bản đang chạy. |
| **Đề xuất cải thiện** | Thêm trang /changelog hoặc modal "What's new" khi user login lần đầu sau update. Tích hợp version footer click \-\> dialog hiển thị: version, build date, commit hash, link release notes. Áp dụng SemVer (Major.Minor.Patch) nhất quán. |
| **Ưu tiên xử lý** | P3 \- Thấp |

 

## **15\. \[PERF-001\] Chưa có thông tin về benchmark hiệu năng**

| Mã vấn đề | PERF-001 |
| :---- | :---- |
| **Mức độ** | Low |
| **Module liên quan** | Hiệu năng |
| **Đối tượng ảnh hưởng** | Tổng thể |
| **Mô tả vấn đề** | Trong phiên test không phát hiện lag rõ ràng nhưng môi trường rỗng (0 record). Cần benchmark khi data đạt quy mô thực tế: 50,000+ items, 10,000+ batches/năm, 100,000+ stock ledger entries/năm. |
| **Tác động nghiệp vụ** | Rủi ro chậm/treo khi đưa vào production. |
| **Đề xuất cải thiện** | Thiết lập môi trường stress test với data lớn. Đo response time của: list view (filter/sort), report Stock Balance, Dashboard load. Thiết lập index DB cho cột thường query (item\_code, batch\_no, warehouse, posting\_date). Implement pagination cho mọi list/report. |
| **Ưu tiên xử lý** | P3 \- Thấp |

 

# **3\. Khuyến nghị lộ trình xử lý**

### **Sprint 1 (1-2 tuần) \- Khôi phục khả năng vận hành**

* Fix BUG-001 (lft attribute) cho SC Item Group, SC Warehouse, SC Department \- đây là blocker.

* Fix BUG-002 \- bổ sung field "Loại NCC" lên form Supplier.

* Verify luồng E2E: Item Group \-\> Item \-\> Supplier \-\> Warehouse \-\> Material Request \-\> Purchase Order \-\> Purchase Receipt \-\> Stock Ledger.

### **Sprint 2 (2-3 tuần) \- Hoàn thiện trải nghiệm**

* BUG-003: Cấu hình ma trận phân quyền chuẩn cho 5 role có sẵn.

* DATA-001: Tạo bộ seed data demo và lệnh CLI cài đặt.

* UX-001 & UX-005: Chuẩn hóa thông báo lỗi và validation client-side.

* FEAT-001: Hoàn thiện chức năng Import Excel \+ template mẫu.

### **Sprint 3 (3-4 tuần) \- Mở rộng & sẵn sàng vận hành thực tế**

* FEAT-003: Hoàn thiện Audit Trail đạt chuẩn ngành y.

* FEAT-004: Notification cảnh báo lô hết hạn qua Email/SMS/Zalo.

* PERF-001: Stress test với dữ liệu lớn (50K+ items), bổ sung index DB.

* UX-002, UX-003, UX-004, FEAT-002, FEAT-005: gom vào polish release.

# **4\. Phụ lục \- Kết quả các test case đã chạy**

| Mã TC | Kịch bản | Kết quả | Ghi chú |
| :---- | :---- | :---- | :---- |
| TC-01 | Tạo UOM "Hộp" | **PASS** | OK |
| TC-02 | Submit UOM với role User | **FAIL (expected)** | Permission đúng |
| TC-03 | Tạo nhiều UOM (Hộp/Viên/Chai) | **PASS** | 3 records OK |
| TC-04 | Validation form Supplier trống | **PASS** | Báo lỗi đúng |
| TC-05 | Tạo Supplier đầy đủ | **FAIL** | BUG-002 (thiếu UI Loại NCC) |
| TC-06 | Tạo Department "Khoa Nội" | **PASS** | OK |
| TC-07 | Tạo Item Group | **FAIL** | BUG-001 (lft) |
| TC-08 | Tạo Warehouse | **FAIL** | BUG-001 (lft) |
| TC-09 | Tạo Item Amoxicillin 500mg | **PASS partial** | Không gán được Group do BUG-001 |
| TC-10 | Tạo Material Request | **BLOCKED** | Phụ thuộc TC-08 |
| TC-11 | Dashboard theo role Thủ kho | **PASS** | Hiển thị đúng 3 KPI |
| TC-12 | Stock Balance hiển thị item mới | **PASS** | OK |

 

# **5\. Kết luận**

SupplyCore có thiết kế nghiệp vụ rất đầy đủ và phù hợp với đặc thù bệnh viện (đơn vị kép Hộp/Viên, BHYT, truy xuất lô, cảnh báo hạn dùng, phân quyền theo vai trò). Tuy nhiên, ở phiên bản v0.1.0, một số lỗi nền tảng cần được xử lý để có thể demo và đưa vào vận hành. Với lộ trình 3 sprint đã đề xuất, sản phẩm có thể sẵn sàng cho UAT trong khoảng 6-8 tuần.

 

*Trân trọng đề nghị Bộ phận Phát triển sản phẩm xem xét, lên kế hoạch và phản hồi tiến độ xử lý từng vấn đề.*

 

*\-- HẾT \--*