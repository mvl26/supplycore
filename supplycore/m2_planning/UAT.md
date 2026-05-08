# UAT — M2 — Kế hoạch & Đặt hàng

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 6 steps — 6 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | Tạo SC Material Request (Khoa) | PASS | SC-MR-2026-01248 |
| 2 | Submit MR | PASS | {"name": "SC-MR-2026-01248", "owner": "Administrator", "creation": "2026-05-08 11:33:56.668409", "modified": "2026-05-08 11:33:56.764886", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "request_type": "Purchase", "transaction_date": "2026-05-08", "schedule_date": "2026-05-15", "departmen |
| 3 | Đọc MR status=Submitted | PASS | status=Approved, docstatus=1 |
| 4 | Tạo SC Purchase Order trực tiếp (không qua FC) | PASS | SC-PO-2026-01249 |
| 5 | Submit Purchase Order | PASS | {"name": "SC-PO-2026-01249", "owner": "Administrator", "creation": "2026-05-08 11:33:56.893825", "modified": "2026-05-08 11:33:56.995789", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược Hậu Giang", "transaction_date": "2026-05- |
| 6 | PO grand_total tính đúng | PASS | grand_total=2600000.0 |
