# PHƯƠNG ÁN — Tách SC Purchase Receipt thành 2 bước (Tiếp nhận → Nhập kho) · ✅ ĐÃ TRIỂN KHAI

> **Chốt:** Approach A (hoãn SLE) · QC hỏng → Trả NCC (is_return) · toàn phiếu · cho huỷ→đảo SLE.
> **Kết quả:** 110/110 Python (gồm 7 test mvl_pr_2step T1–T8) + 13/13 UI (thêm T9) + smoke_m3/uc09 xanh.
> Migrate sạch, backfill 34 phiếu cũ → "Đã nhập kho", **snapshot tồn TRƯỚC=SAU 100% khớp (0 lệch)**.

## SƠ ĐỒ TRẠNG THÁI CUỐI
```
Draft ─submit─▶ Đã tiếp nhận ──(QC Pass)──▶ Chờ nhập kho ──[Xác nhận nhập kho]──▶ Đã nhập kho
                    │  (tạo lô + QI, CHƯA post SLE, tồn=0)          (post SLE @ ngày xác nhận, vào tồn)
                    └──(QC Fail)──▶ Chờ xử lý ──▶ Trả NCC (is_return) / Huỷ
Phiếu TRẢ (is_return): submit = xuất kho ngay (không qua 2 bước).
```

## FILE/HÀM ĐÃ SỬA
- `sc_purchase_receipt.py`: `on_submit` (phiếu thường KHÔNG post SLE, set receipt_status="Đã tiếp nhận");
  `confirm_warehouse_in()` (nút, post SLE @ ngày xác nhận, gate QC Pass + role + idempotent);
  `before_cancel` (huỷ QI liên kết); `on_cancel` (đảo SLE chỉ khi "Đã nhập kho", chặn nếu đã tiêu thụ);
  `_post_stock_ledger(posting_date=…)`.
- `sc_purchase_receipt.json`: +field `receipt_status`, `confirmed_by`, `warehouse_in_date`.
- `sc_quality_inspection.py::_rollup_pr_status`: QC Fail → receipt_status="Chờ xử lý"; bỏ auto set officially_received_at ở QC Pass (chuyển sang bước xác nhận).
- Frontend: `actions.js` (+nút "Xác nhận nhập kho"), `detail-configs.js`/`modules.js`/`i18n.js` (nhãn "Phiếu tiếp nhận tạm" + badge lifecycle + cột "Nhập kho").
- Patch `v0_12/backfill_pr_warehouse_in.py` (backfill phiếu cũ) + `create_pr_print_formats.py` (2 print format).
- Test: `mvl_pr_2step_test.py` (T1–T8) + `ui_tests/specs/T9_pr_warehouse_in.spec.js`.

## ROLLBACK
1. Code: revert các file trên (git) + build lại frontend.
2. Patch backfill: `receipt_status/confirmed_by/warehouse_in_date` chỉ là field mới — để nguyên vô hại,
   hoặc set NULL: `UPDATE tabSC Purchase Receipt SET receipt_status=NULL, confirmed_by=NULL, warehouse_in_date=NULL`.
   **KHÔNG đụng SC Stock Ledger Entry** — patch chưa từng ghi SLE nên tồn không đổi.
3. Print format: xoá 2 Print Format "PR - *".
4. Sau revert code: phiếu đang "Đã tiếp nhận" (chưa post SLE) cần bấm... — nên revert khi không có phiếu treo giữa 2 bước.

## CHECKLIST DEPLOY
- [ ] `bench migrate` (sync field + backfill + print format) — chạy trên bản sao trước.
- [ ] Đối chiếu snapshot tồn từng item TRƯỚC/SAU = khớp.
- [ ] `bench build` frontend + **reload web workers** (gunicorn preload không tự nạp code Python).
- [ ] Kiểm role thủ kho/quản lý bấm được "Xác nhận nhập kho"; QC Officer/khác bị 403.

---



## 1. Khảo sát hiện trạng (đã đọc code)

### 1.1 Chỗ ghi sổ kho
- `sc_purchase_receipt.py::on_submit` (dòng 117) gọi **`_post_stock_ledger()`** → post SC Stock Ledger Entry
  `+qty` NGAY tại `posting_date` khi submit. Đây là chỗ "hàng vào tồn".
- Cùng on_submit: tạo lô (`_create_batches_if_needed`), auto-tạo QC (`_auto_create_qi`), cập nhật
  `PO.received_qty`. Cancel → `_reverse_stock_ledger` (post đối ứng, append-only).

### 1.2 QC đã có sẵn
- Doctype **`SC Quality Inspection`** (auto-tạo mỗi item khi PR submit nếu `qc_required=1`).
- QI `on_submit` → set **`SC Batch.qc_status`** = Accepted/Rejected/Conditional + rollup `PR.qc_status`.
- Kết luận QC chỉ **QC Officer / Manager** (BRU-QC-002). PR có field `qc_status`
  (Pending/Accepted/Rejected/Conditional) + `officially_received_at` (đã có, hiện chưa dùng) + `return_status`.

### 1.3 ⭐ Cơ chế tồn 2 tầng ĐÃ TỒN TẠI MỘT PHẦN
- **`SC Batch.qc_status` default = "Pending"**. `get_available_qty` (SCStockLedgerEntry) **LOẠI** batch
  qc_status ∈ {Pending, Rejected} + blocked. FEFO `get_suggested_batches` cũng chỉ lấy {Accepted, Conditional}.
- ⇒ **Hàng CÓ quản lý lô: submit PR xong VẪN CHƯA khả dụng** cho tới khi QC Accepted. Đã đúng ý tưởng!
- **NHƯNG**: hàng **KHÔNG quản lý lô** (SLE không batch) → **khả dụng NGAY** khi submit (không có lô để gate).

### 1.4 Mọi nơi tiêu thụ số tồn (phạm vi ảnh hưởng)
| Nhóm | Nơi | Hàm dùng | Có loại "chờ QC" không? |
|---|---|---|---|
| **Bán hàng (điểm gặp)** | SO portal (BRU-INV-002) · DN (BRU-INV-001) | `get_available_qty` | ✅ loại Pending (batch) |
| Xuất kho | SC Stock Entry | `get_available_qty` | ✅ |
| FEFO pick (DN) | `get_suggested_batches` | join batch | ✅ chỉ Accepted/Conditional |
| Chuyển kho | SC Transfer Request | **raw SUM(qty_change)** | ❌ tính cả Pending |
| Kiểm kê | Count Sheet / Stock Recon | **raw SUM** | ❌ |
| Kế hoạch | Procurement Plan | **raw SUM** | ❌ |
| Báo cáo/Dashboard | kpi.py · trace.py · recall · batch_expiry_alert · fefo_picker | **raw SUM** | ❌ (hiển thị tồn vật lý) |

## 2. Khoảng cách so với mục tiêu
1. **Item không quản lý lô** vào tồn khả dụng ngay khi submit (chưa gate).
2. **Chưa có trạng thái phiếu + nút "Xác nhận nhập kho" tường minh** — hiện gating ẩn qua batch qc_status.
3. SLE post ở thời điểm **tiếp nhận** (posting_date), không phải thời điểm **xác nhận nhập kho**.
4. Báo cáo raw-SUM hiển thị hàng chờ QC lẫn vào tồn (chưa tách "chờ nhập kho").

## 3. PHƯƠNG ÁN ĐỀ XUẤT — Approach A: hoãn ghi SLE tới lúc "Xác nhận nhập kho" (khuyến nghị)

Khớp đúng mô tả của bạn, xử lý ĐỒNG NHẤT cả item có/không quản lý lô.

### 3.1 Sơ đồ trạng thái (field mới `receipt_status`, đổi qua controller — cấm sửa tay)
```
Draft ──submit──▶ Đã tiếp nhận ──(QC Accepted)──▶ [nút] Xác nhận nhập kho ──▶ Đã nhập kho
  │                   │  (batch tạo, QI auto-tạo, CHƯA post SLE)                    (post SLE @ ngày xác nhận)
  │                   └──(QC Rejected)──▶ Chờ xử lý ──▶ Trả NCC (is_return sẵn có) / Huỷ
```
- **Đã tiếp nhận** (submit): tạo lô + QI + cập nhật PO.received_qty; **KHÔNG post SLE** → tồn khả dụng KHÔNG tăng, kể cả item không lô.
- **Xác nhận nhập kho** (nút): post SLE tại `posting_date = ngày xác nhận`, set `officially_received_at` + `confirmed_by` + `receipt_status="Đã nhập kho"`. Idempotent (đã "Đã nhập kho" → chặn post lần 2).
- Rà lại điểm 1.4: vì SLE chỉ có SAU xác nhận → mọi consumer (kể cả raw-SUM) tự động đúng, không cần sửa từng nơi. Thêm **báo cáo/cột "Chờ nhập kho"** đọc từ PR `Đã tiếp nhận` (không từ SLE).

### 3.2 Nút & quyền
- Nút "Xác nhận nhập kho" trên form + action API; **chỉ hiện khi `qc_status = Accepted`** (xem Q5 về Conditional),
  **chỉ role**: SupplyCore Storekeeper / Warehouse Officer / SupplyCore Manager / System Manager (đúng nhóm submit PR hiện tại). QC Officer KHÔNG bấm (chỉ kết luận QC).
- API chặn: sai trạng thái QC / không quyền → throw (403).

### 3.3 Dữ liệu cũ (patch idempotent v0_12)
- Mọi PR đã submit TRƯỚC thay đổi (đã có SLE): set `receipt_status="Đã nhập kho"`, `confirmed_by=Administrator`,
  `officially_received_at = posting_date cũ`. **TUYỆT ĐỐI không post SLE lại**.
- Idempotent (chỉ set khi field trống). Snapshot tồn từng (item,warehouse,batch) TRƯỚC/SAU = khớp 100% → in bảng đối chiếu.

### 3.4 Print format
- "Phiếu tiếp nhận tạm" (trạng thái Đã tiếp nhận): tiêu đề + dòng chữ đỏ **"HÀNG CHƯA NHẬP KHO — CHỜ QC"**.
- "Phiếu nhập kho" (Đã nhập kho): mẫu TT99 chính thức. 2 print format tiêu đề phân biệt rõ.

### 3.5 Đổi nhãn (KHÔNG rename doctype)
- Giữ tên kỹ thuật `SC Purchase Receipt`. Đổi **label hiển thị** → "Phiếu tiếp nhận tạm" ở: doctype label,
  sidebar (nav-blocks "Tiếp nhận & QC"), list view, form title, print title. Route/URL giữ nguyên.

## 4. Approach B (thay thế — KHÔNG khuyến nghị)
Giữ post SLE ở submit, thêm cờ "đã xác nhận nhập kho" mà MỌI consumer phải tôn trọng (kể cả ~7 chỗ raw-SUM +
non-batch). Phải sửa nhiều nơi tính tồn, dễ sót, rủi ro cao hơn. Approach A gọn và an toàn hơn.

## 5. Ràng buộc & rollback
- Không rename doctype / route / fixture / report. Thay đổi ghi CHANGELOG + cách revert patch (unset field, không đụng SLE).
- Test nối bộ hiện có (103 unit + 12 UI) + T1–T9 theo yêu cầu; regression sửa trước.

## 6. CẦN BẠN CHỐT (Giai đoạn 0)
- **Q1** — Chọn **Approach A** (hoãn SLE tới xác nhận, khuyến nghị) hay B (giữ SLE ở submit + gate)?
- **Q2** — QC **Không đạt**: nhánh "Chờ xử lý" → dùng luồng **Trả NCC (is_return)** sẵn có, hay chỉ Huỷ phiếu?
- **Q3** — Nhập kho **một phần** hay **toàn phiếu**? (đề xuất: toàn phiếu; dòng QC hỏng tách sang phiếu trả riêng).
- **Q4** — **Huỷ phiếu đã nhập kho**: cho phép (đảo SLE như hiện tại) hay CẤM huỷ sau khi đã nhập kho?
- **Q5** — Cho "Xác nhận nhập kho" khi QC = **Conditional** (đạt có điều kiện) không, hay chỉ **Accepted**?
- **Q6** — Báo cáo raw-SUM (chuyển kho/kiểm kê/kpi): với Approach A tự đúng; có cần thêm **cột "Chờ nhập kho"** ở dashboard/list PR không?
