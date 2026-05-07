# UAT — M5 — FEFO + Lô

**Ngày test:** 2026-05-07  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 4 steps — 4 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | API get_suggested_batches | PASS | batches=5, total_avail=150.0, fully=True |
| 2 | API check_batch_status | PASS | batch=M11SMK-EXPIRE-3fbO expired=False severity=Critical |
| 3 | [Edge] FEFO với qty=0 (only listing) | PASS | batches=21, total_avail=1335.0 |
| 4 | [Negative] FEFO với warehouse invalid | PASS | Note: API không validate warehouse tồn tại — trả empty |
