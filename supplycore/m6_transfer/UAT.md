# UAT — M6 — Luân chuyển nội bộ

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 3 steps — 3 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | Tạo SC Transfer Request → Kho Khoa Nhi | PASS | SC-TR-2026-01255 |
| 2 | Submit TR | PASS | {"name": "SC-TR-2026-01255", "owner": "Administrator", "creation": "2026-05-08 11:33:57.947417", "modified": "2026-05-08 11:33:58.013218", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "request_date": "2026-05-08", "transfer_type": "Replenishment", "required_by": "2026-05-11", "requested |
| 3 | TR status sau submit | PASS | status=Approved |
