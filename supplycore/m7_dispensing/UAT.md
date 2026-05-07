# UAT — M7 — Cấp phát & BHYT

**Ngày test:** 2026-05-07  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 3 steps — 3 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | Tạo SC Patient | PASS | {"name": "UAT-PAT-1778150264", "owner": "Administrator", "creation": "2026-05-07 17:37:44.711627", "modified": "2026-05-07 17:37:44.711627", "modified_by": "Administrator", "docstatus": 0, "idx": 0, "patient_id": "UAT-PAT-1778150264", "patient_name": "Nguyễn Văn UAT", "gender": "Nam", "disabled": 0, |
| 2 | Tạo SC Dispensing Request | PASS | SC-DR-2026-00756 |
| 3 | Submit DR | PASS | {"name": "SC-DR-2026-00756", "owner": "Administrator", "creation": "2026-05-07 17:37:44.724434", "modified": "2026-05-07 17:37:44.752247", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "request_date": "2026-05-07", "purpose": "Routine", "required_by": null, "department": "Khoa Nhi", "pat |
