# UAT — M7 — Cấp phát & BHYT

**Ngày test:** 2026-05-08  
**Mode:** REST API qua HTTP (giả lập user UI)  
**Tổng:** 3 steps — 3 PASS, 0 FAIL  

| # | Step | Status | Detail / Error |
|---|---|---|---|
| 1 | Tạo SC Patient | PASS | {"name": "UAT-PAT-1778232585", "owner": "Administrator", "creation": "2026-05-08 16:29:47.126944", "modified": "2026-05-08 16:29:47.126944", "modified_by": "Administrator", "docstatus": 0, "idx": 0, "patient_id": "UAT-PAT-1778232585", "patient_name": "Nguyễn Văn UAT", "gender": "Nam", "disabled": 0, |
| 2 | Tạo SC Dispensing Request | PASS | SC-DR-2026-01469 |
| 3 | Submit DR | PASS | {"name": "SC-DR-2026-01469", "owner": "Administrator", "creation": "2026-05-08 16:29:47.157825", "modified": "2026-05-08 16:29:47.189765", "modified_by": "Administrator", "docstatus": 1, "idx": 0, "request_date": "2026-05-08", "purpose": "Routine", "required_by": null, "department": "Khoa Nhi", "pat |
