# UAT — M1 — Hợp đồng khung

**Ngày test:** 2026-05-07  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 7 steps — 6 PASS, 1 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | [Validation] FC reject supplier không tồn tại | FAIL | AssertionError: BUG-M1-01: FC chấp nhận supplier không tồn tại — sai Link integrity |
| 2 | Tạo Framework Contract (POST) | PASS | SC-FC-2026-00746 |
| 3 | Submit Framework Contract | PASS | {"name": "SC-FC-2026-00746", "owner": "Administrator", "creation": "2026-05-07 17:37:44.119341", "modified": "2026-05-07 17:37:44.142498", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược Hậu Giang", "contract_number": "UAT-FC-17 |
| 4 | Đọc lại FC, kiểm tra status=Active | PASS | status=Active, total=50000000.0 |
| 5 | Tạo Release Order từ FC | PASS | SC-RO-2026-00747 |
| 6 | Submit Release Order | PASS | {"name": "SC-RO-2026-00747", "owner": "Administrator", "creation": "2026-05-07 17:37:44.180746", "modified": "2026-05-07 17:37:44.211137", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "framework_contract": "SC-FC-2026-00746", "supplier": "SC-SUP-00055", "supplier_name": "Công ty CP Dược |
| 7 | FC.used_value tăng sau RO submit | PASS | used_value=0.0, remaining=45000000.0 |

## Lỗi cần fix

- **[Validation] FC reject supplier không tồn tại**: AssertionError: BUG-M1-01: FC chấp nhận supplier không tồn tại — sai Link integrity
