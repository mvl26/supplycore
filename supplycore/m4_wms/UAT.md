# UAT — M4 — WMS / Stock Entry

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 5 steps — 5 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | Tạo SC Batch | PASS | {"name": "UAT-M4-BATCH-1778214835", "owner": "Administrator", "creation": "2026-05-08 11:33:57.512583", "modified": "2026-05-08 11:33:57.512583", "modified_by": "Administrator", "docstatus": 0, "idx": 0, "batch_id": "UAT-M4-BATCH-1778214835", "item": "VTTH-MASK-3PLY", "item_name": "Khẩu trang y tế 3 |
| 2 | Tạo SC Stock Entry — Material Receipt 30 hộp | PASS | SC-SE-2026-01253 |
| 3 | Submit SE | PASS | {"name": "SC-SE-2026-01253", "owner": "Administrator", "creation": "2026-05-08 11:33:57.588018", "modified": "2026-05-08 11:33:57.642776", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "entry_type": "Material Receipt", "posting_date": "2026-05-08", "posting_time": "11:33:57.57963", "from |
| 4 | SLE đã tạo balance_qty=30 | PASS | sle_count=1, first={'name': 'SC-SLE-2026-00001254', 'qty_change': 30.0, 'balance_qty': 30.0} |
| 5 | [Negative] SE không batch cho item batch-tracked phải bị reject | PASS | OK — SE từ chối item batch-tracked không có batch |
