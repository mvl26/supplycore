# UAT — M8 — Kế toán & 3-way match

**Ngày test:** 2026-05-07  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 2 steps — 2 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | API three_way_match cho 1 PI giả định | PASS | status=Match, po_total=150000.0, pr_total=150000.0, var=0.0% |
| 2 | API supplier_balance | PASS | supplier=SC-SUP-00055, outstanding=0.0, overdue=0.0 |
