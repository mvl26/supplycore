# UAT — M11 — Dashboard & Alert

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 5 steps — 5 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | API get_executive_dashboard | PASS | stock_value=488457750.0, pending_pos=22, expiring=2, top=3 |
| 2 | API get_warehouse_dashboard | PASS | qty_total=6225.0, expiring=1, dr=13 |
| 3 | Tạo SC Alert Rule (UAT) | PASS | SC-AR-01259 |
| 4 | [Edge] KPI period=invalid_value (default fallback) | PASS | period_label=abcxyz, fallback ok=True |
| 5 | [Negative] KPI reject warehouse invalid | PASS | OK — KPI reject warehouse invalid |
