# UAT — M1 — Hợp đồng khung

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 7 steps — 7 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | [Validation] FC reject supplier không tồn tại | PASS | OK — FC từ chối supplier không tồn tại đúng kỳ vọng |
| 2 | Tạo Framework Contract (POST) | PASS | SC-FC-2026-01108 |
| 3 | Submit Framework Contract | PASS | {"name": "SC-FC-2026-01108", "owner": "Administrator", "creation": "2026-05-08 11:26:44.774263", "modified": "2026-05-08 11:26:44.867320", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược Hậu Giang", "contract_number": "UAT-FC-17 |
| 4 | Đọc lại FC, kiểm tra status=Active | PASS | status=Active, total=50000000.0 |
| 5 | Tạo Release Order từ FC | PASS | SC-RO-2026-01109 |
| 6 | Submit Release Order | PASS | {"name": "SC-RO-2026-01109", "owner": "Administrator", "creation": "2026-05-08 11:26:44.963001", "modified": "2026-05-08 11:26:45.023182", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "framework_contract": "SC-FC-2026-01108", "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược |
| 7 | FC.used_value tăng sau RO submit | PASS | used_value=0.0, remaining=45000000.0 |
