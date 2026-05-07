# UAT — M3 — Tiếp nhận & QC

**Ngày test:** 2026-05-07  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 4 steps — 4 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | Tạo SC Batch (master) | PASS | {"name": "UAT-M3-BATCH-1778150264", "owner": "Administrator", "creation": "2026-05-07 17:37:44.398943", "modified": "2026-05-07 17:37:44.398943", "modified_by": "Administrator", "docstatus": 0, "idx": 0, "batch_id": "UAT-M3-BATCH-1778150264", "item": "VTTH-MASK-3PLY", "item_name": "Khẩu trang y tế 3 |
| 2 | Tạo SC Purchase Receipt từ PO | PASS | SC-PR-2026-00750 |
| 3 | Submit PR (auto-create QI nếu cần) | PASS | {"name": "SC-PR-2026-00750", "owner": "Administrator", "creation": "2026-05-07 17:37:44.424814", "modified": "2026-05-07 17:37:44.453920", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược Hậu Giang", "purchase_order": "SC-PO-2026 |
| 4 | PR có qc_status | PASS | qc_status=Pending, status=None |
