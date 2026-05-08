# UAT — M5 — FEFO + Lô

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 4 steps — 4 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | API get_suggested_batches | PASS | batches=5, total_avail=150.0, fully=True |
| 2 | API check_batch_status | PASS | batch=INTEG-BATCH-CLAYOf expired=False severity=OK |
| 3 | [Edge] FEFO với qty=0 (only listing) | PASS | batches=38, total_avail=2570.0 |
| 4 | [Negative] FEFO với warehouse invalid | PASS | Note: API không validate warehouse tồn tại — trả empty |
