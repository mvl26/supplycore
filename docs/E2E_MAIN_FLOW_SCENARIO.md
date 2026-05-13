# Kịch bản kiểm thử luồng chính SupplyCore (E2E)

> **Ngày viết:** 2026-05-13
> **Mục đích:** Hướng dẫn người kiểm thử/QA chạy luồng nghiệp vụ chính từ **Dữ liệu nền → Hợp đồng → Mua hàng → Nhập kho → Cấp phát → Kế toán** sau khi đã xoá sạch dữ liệu giao dịch. Môi trường thử nghiệm (sandbox): `http://supplycore`.

---

## 0. Tiền điều kiện — Dữ liệu nền đã có sẵn

Sau lần xoá gần nhất, sandbox còn **đúng các dữ liệu nền sau** (không cần khởi tạo lại):

| Loại | Số lượng | Ví dụ |
|---|---|---|
| **Vật tư** (`SC Item`) | 12 | `DTRC-RL`, `DTRC-NACL09`, `VTPT-IODINE` |
| **Nhà cung cấp** (`SC Supplier`) | 12 | `SC-SUP-03163` Roche Diagnostics Vietnam, `SC-SUP-03162` Vật tư Y tế Sài Gòn |
| **Kho** (`SC Warehouse`) | 15 | `Kho Tổng Bệnh viện` (kho chính, nhóm), `Kho Khoa Dược`, `Kho Phòng Mổ`, `Kho Cách ly QC` (kho cách ly), `Kho Trung chuyển` |
| **Bệnh nhân** (`SC Patient`) | 13 | `BN010` Trương Thị Kim (BHYT Trái tuyến), `BN009` Đỗ Văn Inh (BHYT Đúng tuyến) |
| **Đơn vị tính** (`SC UOM`) | 18 | Chai, Bộ, Cái, Gói, Cuộn, Đôi |
| **Khoa phòng** (`SC Department`) | 33 | Khoa Dược, Phòng Khám tổng hợp, Phòng Vật tư-TTBYT |
| **Nhóm vật tư** (`SC Item Group`) | 23 | Dịch truyền, Vật tư tiêu hao, Vật tư phẫu thuật |

**Toàn bộ doctype giao dịch (Phiếu nhập / Đơn mua / Phiếu chuyển kho / Lô / Bút toán kho / Yêu cầu mua / Phiếu KCS / Yêu cầu chuyển kho / Cấp phát BN / Yêu cầu cấp phát / Hoá đơn / Phiếu thanh toán / Bút toán sổ cái / Đối soát kho / Phiếu kiểm kê / Phiếu thu hồi / Báo cáo điều tra) = 0 bản ghi.**

**Đăng nhập:** `Administrator` / `admin`.

---

## 1. Sơ đồ luồng

```
Dữ liệu nền
   │
   ├─→ [M1] Hợp đồng khung (Framework Contract)
   │         │
   │         └─→ Tạo Yêu cầu mua hàng
   │
   ├─→ [M2] Yêu cầu mua hàng (Material Request)
   │         │
   │         ├─→ Tạo Đơn mua
   │         └─→ Gửi duyệt
   │
   ├─→ [M2] Đơn mua (Purchase Order)
   │         │
   │         ├─→ Gửi duyệt → trạng thái: Đã gửi NCC
   │         └─→ Tạo Phiếu nhập
   │
   ├─→ [M3] Phiếu nhập (Purchase Receipt)
   │         │
   │         ├─→ Gửi duyệt → Bút toán kho +qty, trạng thái: Đã nhận
   │         ├─→ Tạo Lô (sinh lô theo từng dòng)
   │         ├─→ Tạo Phiếu KCS (sinh phiếu KCS nháp)
   │         └─→ Chuyển sang /putaway (xếp hàng lên kệ)
   │
   ├─→ [M3] Phiếu KCS (Quality Inspection)
   │         │
   │         ├─→ Đạt tất cả tiêu chí
   │         └─→ Gửi duyệt → Kết quả tổng: Đạt → Lô.QC = Đạt
   │
   ├─→ [M4/M5] Xếp lên kệ + Gán vị trí lưu trữ theo FEFO
   │
   ├─→ [M6] Yêu cầu chuyển kho (Transfer Request)
   │         │
   │         ├─→ Gửi duyệt → trạng thái: Đã duyệt
   │         └─→ Tạo Phiếu chuyển kho (tự chọn lô theo FEFO)
   │
   ├─→ [M6] Phiếu chuyển kho (Stock Entry)
   │         │
   │         └─→ Gửi duyệt → Bút toán kho ghi nhận chuyển kho, YCCK chuyển: Đã nhận
   │
   ├─→ [M7] Cấp phát bệnh nhân (Patient Dispensing)
   │         │
   │         └─→ Gửi duyệt → Bút toán kho xuất kho, áp tỷ lệ BHYT
   │
   ├─→ [M8] Hoá đơn mua + Phiếu thanh toán
   │         │
   │         ├─→ Gửi duyệt Hoá đơn (đối soát 3 chiều: PO + PN)
   │         └─→ Gửi duyệt Phiếu thanh toán
   │
   └─→ [M9] Đối soát kho (Stock Reconciliation — định kỳ)
```

---

## 2. Kịch bản kiểm thử chính (Luồng thuận)

### Bước 1 — M1: Tạo Hợp đồng khung

**Mục đích:** Ký HĐ khung với NCC `SC-SUP-03162` cho 2 mặt hàng dịch truyền, hiệu lực 12 tháng.

**Thao tác:**
1. SPA → `M1 Hợp đồng` → `+ Tạo mới Hợp đồng khung`
2. Nhập:
   - Nhà cung cấp: `SC-SUP-03162` (Vật tư Y tế Sài Gòn)
   - Hiệu lực từ: hôm nay
   - Hết hạn: hôm nay + 12 tháng
   - Loại HĐ: `Thường quy`
   - Dòng chi tiết:
     - `DTRC-RL` × 100 Chai × 35.000 đ
     - `DTRC-NACL09` × 200 Chai × 30.000 đ
3. **Lưu** → trạng thái `Nháp`
4. **Gửi duyệt** → `Manager duyệt` → `Lãnh đạo duyệt` → trạng thái: `Hoạt động`

**Kiểm tra:**
- ✔ Mã HĐ dạng `FC-...`
- ✔ Tổng giá trị HĐ = 100×35.000 + 200×30.000 = 9.500.000 đ
- ✔ Nhãn trạng thái = "Hoạt động"

---

### Bước 2 — M2: Tạo Yêu cầu mua hàng từ HĐ

**Mục đích:** Sinh Yêu cầu mua hàng (YCMH) gắn với HĐ khung ở Bước 1.

**Thao tác:**
1. Mở HĐ khung đang Hoạt động → bấm **`Tạo Yêu cầu mua hàng`**
2. SPA tự chuyển sang YCMH nháp với các dòng đã được điền sẵn từ HĐ
3. Điều chỉnh số lượng nếu cần (ví dụ: chỉ mua 50/100 RL)
4. **Lưu** → **Gửi duyệt**
5. Trên YCMH đã gửi duyệt → bấm **`Duyệt YCMH`** → trạng thái: `Đã duyệt`

**Kiểm tra:**
- ✔ Mã YCMH `SC-MR-2026-00001` (bộ đếm số chuỗi đã đặt lại sau lần xoá)
- ✔ Trường `framework_contract` trỏ về HĐ ở Bước 1
- ✔ Trạng thái = `Đã duyệt`

---

### Bước 3 — M2: Tạo Đơn mua từ YCMH

**Mục đích:** Chuyển YCMH thành Đơn mua (ĐM) để gửi NCC.

**Thao tác:**
1. Trên YCMH đã duyệt → bấm **`Tạo Đơn mua`**
2. ĐM mới ở trạng thái `Nháp`, NCC và các dòng đã điền sẵn từ YCMH
3. **Gửi duyệt** ĐM trực tiếp (bỏ qua bước phê duyệt) → trạng thái: `Đã gửi NCC`

**Kiểm tra:**
- ✔ Mã ĐM `SC-PO-2026-00001`
- ✔ Trường `material_request` trỏ về YCMH ở Bước 2
- ✔ Trạng thái = `Đã gửi NCC`
- ✔ Nút **`Tạo Phiếu nhập`** xuất hiện

---

### Bước 4 — M3: Tạo Phiếu nhập từ Đơn mua

**Mục đích:** NCC giao hàng → nhập vào Kho Trung chuyển.

**Thao tác:**
1. Trên ĐM đã duyệt → bấm **`Tạo Phiếu nhập`**
2. Phiếu nhập (PN) nháp mở ra, điền sẵn từ ĐM. Điều chỉnh:
   - Kho đích: `Kho Trung chuyển`
   - Số lô NCC + ngày sản xuất / hạn dùng cho từng dòng có `has_batch_no=1`:
     - Số lô NCC: `LOT-DTRC-2026A` / Ngày SX: 2026-04-01 / Hạn dùng: 2028-04-01
3. **Lưu** → **Gửi duyệt**
4. SPA tự chuyển sang `/putaway?warehouse=Kho Trung chuyển`

**Kiểm tra:**
- ✔ Mã PN `SC-PR-2026-00001`
- ✔ Sau khi gửi duyệt → có Bút toán kho (+qty cho mỗi dòng)
- ✔ Trạng thái = `Đã nhận`
- ✔ Nút **`Tạo Lô`** + **`Tạo Phiếu KCS`** xuất hiện

---

### Bước 5 — M3: Tạo Lô từ PN

**Thao tác:** Trên PN đã nhận → bấm **`Tạo Lô`**.

**Kiểm tra:**
- ✔ 2 Lô được tạo (vì có 2 dòng dịch truyền `has_batch_no=1`)
- ✔ Các trường Lô đầy đủ: `batch_id`, `item`, `supplier`, `manufacturing_date`, `expiry_date`, `qc_status = Chờ`
- ✔ Nút **`Xem Lô đã tạo`** hiển thị danh sách 2 lô

---

### Bước 6 — M3: Phiếu kiểm soát chất lượng (KCS)

**Mục đích:** Kiểm tra chất lượng → Đạt → lô hết cách ly.

**Thao tác:**
1. Trên PN → bấm **`Tạo Phiếu KCS`** → Phiếu KCS nháp
2. Form Phiếu KCS mở **trực tiếp ở chế độ chỉnh sửa** (tự bật cho phiếu nháp). PN + Vật tư + NCC đã được tải sẵn.
3. Chọn Lô trong danh sách — hoặc bấm **`+ Tạo mới Lô`** nếu chưa có
4. Trong bảng "Tiêu chí kiểm tra" → bấm **`✓ Đạt tất cả`** → mọi tiêu chí → Đạt
5. Đặt `Kết quả tổng` = `Đạt`
6. **Gửi duyệt**

**Kiểm tra:**
- ✔ Mã Phiếu KCS `SC-QI-2026-00001`
- ✔ Lô.qc_status = `Đạt`
- ✔ Lô hết cách ly, có thể được FEFO chọn

---

### Bước 7 — M4/M5: Xếp hàng lên kệ + Gán vị trí lưu trữ

**Mục đích:** Gán Vị trí lưu trữ cho hàng vừa nhận (nếu cần — sandbox đã có Vị trí lưu trữ `TEST-*` từ bộ kiểm thử số 25).

**Thao tác:**
1. Vào `/putaway?warehouse=Kho Trung chuyển`
2. Mỗi dòng PN hiển thị danh sách chọn Vị trí đích (lọc theo kho)
3. Chọn vị trí cho từng dòng, **Lưu**

**Kiểm tra:**
- ✔ Bút toán kho có gán `target_bin`
- ✔ Số lượng hiện tại trong Vị trí lưu trữ tăng lên

---

### Bước 8 — M6: Tạo Yêu cầu chuyển kho

**Mục đích:** Chuyển từ `Kho Trung chuyển` → `Kho Khoa Dược` cho 50 Chai `DTRC-RL`.

**Thao tác:**
1. SPA → `M6 Chuyển kho` → **`+ Tạo mới Yêu cầu chuyển kho`**
2. Điền:
   - Ngày yêu cầu = hôm nay (tự điền)
   - Cần trước ngày = hôm nay + 3 (mặc định: hôm nay)
   - Loại yêu cầu = `Bổ sung`
   - Kho nguồn: `Kho Trung chuyển`
   - Kho đích: `Kho Khoa Dược`
   - Dòng chi tiết: `DTRC-RL` × 50 Chai / SL yêu cầu = 50
3. **Lưu** → **Gửi duyệt** → trạng thái: `Đã duyệt` (Manager bỏ qua khi không xuyên cấp)

**Kiểm tra:**
- ✔ Mã YCCK `SC-TR-2026-00001`
- ✔ `available_at_source` (tồn kho nguồn) ≥ 50 (do PN Bước 4 đã +100)
- ✔ Nút **`Tạo phiếu chuyển kho`** xuất hiện

---

### Bước 9 — M6: Tạo Phiếu chuyển kho từ YCCK

**Mục đích:** YCCK → Phiếu chuyển kho (tự chọn lô theo FEFO nếu YCCK không chỉ định).

**Thao tác:**
1. Trên YCCK đã duyệt → bấm **`Tạo phiếu chuyển kho`**
2. Backend `make_stock_entry`:
   - Sao chép kho nguồn/đích, các dòng chi tiết
   - Tự chọn lô theo FEFO từ `Kho Trung chuyển` (vì dòng YCCK không chỉ định lô)
   - Tách dòng nếu cần nhiều lô
3. Phiếu chuyển kho (PCK) mới `Nháp`, chuyển sang trang chi tiết
4. **Gửi duyệt** PCK

**Kiểm tra:**
- ✔ PCK loại giao tác = `Chuyển kho`
- ✔ PCK.transfer_request → YCCK ở Bước 8
- ✔ Mỗi dòng đã được tự chọn lô theo FEFO
- ✔ Sau khi gửi duyệt → 2 Bút toán kho: −qty ở Kho Trung chuyển, +qty ở Kho Khoa Dược
- ✔ YCCK.trạng thái = `Đang vận chuyển` → khi PCK gửi duyệt → `Đã nhận`

---

### Bước 10 — M7: Cấp phát cho Bệnh nhân

**Mục đích:** Cấp phát 5 Chai `DTRC-RL` cho `BN010` (Trương Thị Kim, BHYT Trái tuyến).

**Thao tác:**
1. SPA → `M7 Cấp phát` → **`+ Tạo mới Cấp phát bệnh nhân`**
2. Điền:
   - Ngày cấp phát = hôm nay
   - Bệnh nhân: `BN010`
   - Khoa hiện tại: tự tải từ bệnh nhân
   - Loại: `Theo bệnh nhân`
   - Kho xuất: `Kho Khoa Dược`
   - Dòng chi tiết: `DTRC-RL` × 5 Chai
     - Tự tải: Đơn vị tính, Đơn giá, Lô theo FEFO (qua API `pd_item_autofetch`)
3. **Lưu** → **Gửi duyệt**

**Kiểm tra:**
- ✔ Mã CPBN `SC-PD-2026-00001`
- ✔ Tự tải lô hoạt động (cùng lô FEFO ở Bước 9)
- ✔ Sau khi gửi duyệt → Bút toán kho −5 ở Kho Khoa Dược
- ✔ Tỷ lệ chi trả BHYT đúng theo `bhyt_type` của BN010

---

### Bước 11 — M8: Hoá đơn mua + Phiếu thanh toán

**Mục đích:** PN đã nhận → Hoá đơn → Phiếu thanh toán (đối soát 3 chiều).

**Thao tác:**
1. Quay về ĐM ở Bước 3 → bấm **`Tạo Hoá đơn`** (nếu có) HOẶC tạo thủ công `/doc/SC Purchase Invoice/new`
2. Tham chiếu Hoá đơn: ĐM + PN
3. Thuế VAT 8% / 10%
4. **Gửi duyệt** → Bút toán sổ cái tự sinh (đối soát 3 chiều theo ngưỡng ±1%)
5. Tạo `/doc/SC Payment Entry/new`:
   - Phương thức: `Chuyển khoản`
   - Số tiền: tổng giá trị Hoá đơn
   - Tham chiếu: Hoá đơn từ bước trên
6. **Gửi duyệt** Phiếu thanh toán

**Kiểm tra:**
- ✔ Mã Hoá đơn `SC-PI-2026-00001`
- ✔ Mã Phiếu thanh toán `SC-PE-2026-00001`
- ✔ Bút toán sổ cái tạo đúng tài khoản (Tài sản / Chi phí / Nợ phải trả)
- ✔ Nếu chênh lệch > ngưỡng 50 triệu → cần Lãnh đạo phê duyệt

---

### Bước 12 — M9: Đối soát kho

**Mục đích:** Đối soát định kỳ tồn kho thực tế và Bút toán kho.

**Thao tác:**
1. SPA → `M9 Kiểm kê` → **`+ Tạo mới Đối soát kho`**
2. Kho: `Kho Khoa Dược`
3. Loại: `Định kỳ`
4. Quét/nhập số lượng thực tế cho từng vật tư
5. **Gửi duyệt** → tạo Bút toán điều chỉnh nếu lệch

**Kiểm tra:**
- ✔ Mã Đối soát `SC-SR-2026-00001`
- ✔ Nếu thực tế = hệ thống → 0 Bút toán điều chỉnh
- ✔ Nếu lệch > 0 → cần Manager phê duyệt

---

## 3. Bảng kiểm tổng quát sau khi chạy E2E

| Doctype | Số bản ghi mong đợi | Ghi chú |
|---|---|---|
| Hợp đồng khung | 1 (Hoạt động) | Bước 1 |
| Yêu cầu mua hàng | 1 (Đã duyệt) | Bước 2 |
| Đơn mua | 1 (Đã gửi NCC) | Bước 3 |
| Phiếu nhập | 1 (Đã nhận) | Bước 4 |
| Lô | 2 (QC = Đạt) | Bước 5+6 |
| Phiếu KCS | 1 (Đạt) | Bước 6 |
| Yêu cầu chuyển kho | 1 (Đã nhận) | Bước 8 |
| Phiếu chuyển kho | 1 (Đã duyệt) | Bước 9 |
| Cấp phát bệnh nhân | 1 (Đã duyệt) | Bước 10 |
| Hoá đơn mua | 1 (Đã duyệt) | Bước 11 |
| Phiếu thanh toán | 1 (Đã duyệt) | Bước 11 |
| Bút toán sổ cái | ≥ 3 | Bước 11 |
| Đối soát kho | 1 (Đã duyệt) | Bước 12 |
| Bút toán kho | ≥ 8 | Tổng các giao tác +/− qty |

---

## 4. Chạy tự động qua Playwright

Bộ kiểm thử Playwright tương ứng:

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore/frontend

# Kiểm thử riêng từng module:
npm run test:uc:m1     # Tạo + duyệt Hợp đồng khung
npm run test:uc:m2     # Luồng YCMH + ĐM
npm run test:uc:m3     # PN + Phiếu KCS + Lô
npm run test:uc:m4m5   # Xếp lên kệ + FEFO
npm run test:uc:m6     # YCCK + Phiếu chuyển kho
npm run test:uc:m7     # Cấp phát BN
npm run test:uc:m8     # Hoá đơn + Phiếu thanh toán
npm run test:uc:m9     # Đối soát kho

# Chạy chuỗi hành động (HĐ khung → YCMH → ĐM → PN):
node tests/sandbox/runner.mjs 08_chained_actions

# Luồng thuận E2E (1 lệnh):
npm run e2e
npm run e2e:headed     # mở trình duyệt để xem
```

Ảnh chụp màn hình kết quả: `/tmp/sc-sandbox/`.

---

## 5. Đặt lại sandbox về chỉ-có-dữ-liệu-nền

Nếu cần chạy lại từ đầu (xoá dữ liệu giao dịch, giữ dữ liệu nền):

```bash
cd /home/hoangvietyeuem/frappe-bench

# Xoá PN/ĐM/PCK/Lô/Bút toán kho
bench --site supplycore execute supplycore.api.wipe.wipe_transactions \
  --kwargs '{"confirm": "YES-WIPE-ALL-TRANSACTIONS"}'

# Xoá giao dịch M1/M2/M3/M6/M7 (HĐ khung / YCMH / Phiếu KCS / YCCK / CPBN / Yêu cầu cấp phát)
bench --site supplycore execute supplycore.api.wipe.wipe_modules \
  --kwargs '{"confirm": "YES-WIPE-MODULES-1-2-3-6-7"}'

# Xoá M8/M9/M10 (Hoá đơn / Thanh toán / Bút toán sổ cái / Đối soát kho / Phiếu kiểm kê / Phiếu thu hồi / Báo cáo điều tra)
bench --site supplycore execute supplycore.api.wipe.wipe_modules_8_10 \
  --kwargs '{"confirm": "YES-WIPE-MODULES-8-9-10"}'
```

Toàn bộ dữ liệu nền (Vật tư / Nhà cung cấp / Kho / Bệnh nhân / Đơn vị tính / Khoa phòng / Nhóm vật tư) sẽ **không bị động** — đã xác minh qua các bộ kiểm thử 27/28/29 trên Playwright (`masters_unchanged: true`).

---

## 6. Tiêu chí nghiệm thu

Luồng E2E được coi là ĐẠT khi:

1. **Mỗi bước không có thông báo lỗi đỏ** (cảnh báo vàng chấp nhận được)
2. **Nút hành động xuất hiện đúng theo điều kiện `when()`** trong `actions.js`
3. **Bút toán kho chính xác**: tổng `qty_change` tại mỗi kho khớp với chuyển động thực tế
4. **FEFO**: Phiếu chuyển kho Bước 9 chọn lô gần hết hạn trước nhất
5. **Đối soát 3 chiều Hoá đơn**: chênh lệch ≤ ngưỡng (mặc định ±1%) → tự động đạt; > ngưỡng → cần phê duyệt
6. **BHYT**: Cấp phát BN Bước 10 áp đúng tỷ lệ chi trả theo `bhyt_type` (Đúng tuyến 100% / Trái tuyến 40% / Không có 0%)
7. **Việt hoá**: tất cả danh sách chọn hiển thị tiếng Việt (đã xác minh ở bộ kiểm thử 26)

---

**Liên hệ:** Nếu gặp lỗi backend, kiểm tra `frappe.log_error` và `logs/web.error.log`. Cần khởi động lại sau khi sửa Python: `sudo supervisorctl restart frappe-bench-frappe-web`.
