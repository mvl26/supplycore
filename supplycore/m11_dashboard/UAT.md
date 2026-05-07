# UAT — M11 — Dashboard & Alert

**Ngày test:** 2026-05-07  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 5 steps — 5 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | API get_executive_dashboard | PASS | stock_value=395750000.0, pending_pos=19, expiring=0, top=3 |
| 2 | API get_warehouse_dashboard | PASS | qty_total=3930.0, expiring=0, dr=9 |
| 3 | Tạo SC Alert Rule (UAT) | PASS | SC-AR-00866 |
| 4 | [Edge] KPI period=invalid_value (default fallback) | PASS | period_label=abcxyz, fallback ok=True |
| 5 | [Negative] KPI reject warehouse invalid | PASS | OK — KPI reject warehouse invalid |
