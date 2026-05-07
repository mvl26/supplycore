# UAT — M6 — Luân chuyển nội bộ

**Ngày test:** 2026-05-07  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 3 steps — 3 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | Tạo SC Transfer Request → Kho Khoa Nhi | PASS | SC-TR-2026-00755 |
| 2 | Submit TR | PASS | {"name": "SC-TR-2026-00755", "owner": "Administrator", "creation": "2026-05-07 17:37:44.646304", "modified": "2026-05-07 17:37:44.674682", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "request_date": "2026-05-07", "transfer_type": "Replenishment", "required_by": "2026-05-10", "requested |
| 3 | TR status sau submit | PASS | status=Approved |
