# UAT — M7 — Cấp phát & BHYT

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 3 steps — 3 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | Tạo SC Patient | PASS | {"name": "UAT-PAT-1778214835", "owner": "Administrator", "creation": "2026-05-08 11:33:58.113468", "modified": "2026-05-08 11:33:58.113468", "modified_by": "Administrator", "docstatus": 0, "idx": 0, "patient_id": "UAT-PAT-1778214835", "patient_name": "Nguyễn Văn UAT", "gender": "Nam", "disabled": 0, |
| 2 | Tạo SC Dispensing Request | PASS | SC-DR-2026-01256 |
| 3 | Submit DR | PASS | {"name": "SC-DR-2026-01256", "owner": "Administrator", "creation": "2026-05-08 11:33:58.179402", "modified": "2026-05-08 11:33:58.266946", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "request_date": "2026-05-08", "purpose": "Routine", "required_by": null, "department": "Khoa Nhi", "pat |
