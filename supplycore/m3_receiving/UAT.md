# UAT — M3 — Tiếp nhận & QC

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 4 steps — 4 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | Tạo SC Batch (master) | PASS | {"name": "UAT-M3-BATCH-1778214835", "owner": "Administrator", "creation": "2026-05-08 11:33:57.138169", "modified": "2026-05-08 11:33:57.138169", "modified_by": "Administrator", "docstatus": 0, "idx": 0, "batch_id": "UAT-M3-BATCH-1778214835", "item": "VTTH-MASK-3PLY", "item_name": "Khẩu trang y tế 3 |
| 2 | Tạo SC Purchase Receipt từ PO | PASS | SC-PR-2026-01250 |
| 3 | Submit PR (auto-create QI nếu cần) | PASS | {"name": "SC-PR-2026-01250", "owner": "Administrator", "creation": "2026-05-08 11:33:57.278761", "modified": "2026-05-08 11:33:57.370154", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược Hậu Giang", "purchase_order": "SC-PO-2026 |
| 4 | PR có qc_status | PASS | qc_status=Pending, status=None |
