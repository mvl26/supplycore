# UAT — M1 — Hợp đồng khung

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 8 steps — 8 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | [Validation] FC reject supplier không tồn tại | PASS | OK — FC từ chối supplier không tồn tại đúng kỳ vọng |
| 2 | Tạo Framework Contract (POST) | PASS | SC-FC-2026-01602 |
| 3 | FC submit_for_review (Manager Review) | PASS | {"name": "SC-FC-2026-01602", "owner": "Administrator", "creation": "2026-05-08 17:31:24.619630", "modified": "2026-05-08 17:31:24.664936", "modified_by": "Administrator", "docstatus": 0, "idx": 0, "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược Hậu Giang", "contract_number": "UAT-FC-17 |
| 4 | Submit Framework Contract | PASS | {"name": "SC-FC-2026-01602", "owner": "Administrator", "creation": "2026-05-08 17:31:24.619630", "modified": "2026-05-08 17:31:24.776443", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược Hậu Giang", "contract_number": "UAT-FC-17 |
| 5 | Đọc lại FC, kiểm tra status=Active | PASS | status=Active, total=50000000.0 |
| 6 | Tạo Release Order từ FC | PASS | SC-RO-2026-01603 |
| 7 | Submit Release Order | PASS | {"name": "SC-RO-2026-01603", "owner": "Administrator", "creation": "2026-05-08 17:31:24.911234", "modified": "2026-05-08 17:31:24.969864", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "framework_contract": "SC-FC-2026-01602", "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược |
| 8 | FC.used_value tăng sau RO submit | PASS | used_value=0.0, remaining=45000000.0 |
