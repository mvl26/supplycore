# UAT — M2 — Kế hoạch & Đặt hàng

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 6 steps — 6 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | Tạo SC Material Request (Khoa) | PASS | SC-MR-2026-01604 |
| 2 | Submit MR | PASS | {"name": "SC-MR-2026-01604", "owner": "Administrator", "creation": "2026-05-08 17:31:25.125325", "modified": "2026-05-08 17:31:25.233531", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "request_type": "Purchase", "transaction_date": "2026-05-08", "schedule_date": "2026-05-15", "departmen |
| 3 | Đọc MR status=Submitted | PASS | status=Approved, docstatus=1 |
| 4 | Tạo SC Purchase Order trực tiếp (không qua FC) | PASS | SC-PO-2026-01605 |
| 5 | Submit Purchase Order | PASS | {"name": "SC-PO-2026-01605", "owner": "Administrator", "creation": "2026-05-08 17:31:25.328114", "modified": "2026-05-08 17:31:25.405776", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược Hậu Giang", "transaction_date": "2026-05- |
| 6 | PO grand_total tính đúng | PASS | grand_total=2600000.0 |
