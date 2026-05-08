# UAT — M10 — Truy xuất & Recall

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 3 steps — 3 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | API get_batch_trace | PASS | batch=ALRTACT-EXP-ly2gqU, movements=1, remaining=30.0 |
| 2 | API get_audit_trail | PASS | entries=0 |
| 3 | Tạo SC Recall Notice | PASS | SC-RCL-2026-01258 |
