# GĐ4 — Rebrand Miyano + UI (Portal www + Sales SPA) + Dashboard công nợ + Hardening

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. UI task: đọc frontend-design skill trước khi dựng trang khách. Steps `- [ ]`.

**Goal:** Hoàn thiện "thành phẩm" MVL: đổi nhận diện sang Miyano, dựng trang Portal khách (www/portal, tiêu thụ api/portal.py), đưa M7 Sales vào SPA nội bộ, dashboard công nợ phải thu, đóng residual hardening /api/resource.

**Architecture:** Portal khách = trang Frappe web riêng `supplycore/www/portal/` (tách khỏi SPA nội bộ — quyết định user 2026-07-07). Sales nội bộ = thêm vào SPA modules/schemas hiện có (DocView generic). Rebrand = sửa default/seed/prose. Hardening = request-level guard cho /api/resource child.

**Tech Stack:** Frappe v15, Vue SPA (nội bộ), Frappe web pages (portal khách), Python.

## Global Constraints
- Nhánh `feat/mvl-distributor`. Site `supplycore-miyano.local`. Bench `/home/hoangvietyeuem/frappe-bench-yhct`. Pkg `.../apps/supplycore/supplycore`.
- INVARIANT sau mỗi task: `bench migrate` + (nếu đụng SPA) `bench build --app supplycore` sạch + `frappe.ping`→pong.
- Không phá cô lập RSK-01 (GĐ3) và không hồi quy GĐ1/GĐ2. Chạy lại portal_isolation_test + sales suites sau task đụng permission/portal.
- cwd reset sau bench — absolute path. Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- Rebrand: công ty = **Công ty Miyano Việt Nam (MVL)**, lĩnh vực **phân phối vật tư/hóa chất y tế**. Không tái nhập thuật ngữ bệnh viện.

---

### Task 1: Rebrand + reseed sang Miyano (dọn prose/data bệnh viện còn sót)
**Files:** `supplycore/api/warehouse_map.py`, `supplycore/setup/seed_warehouse_map.py`, `supplycore/setup/seed_master_data.py`, `supplycore/setup/seed_10_*.py`, `supplycore/setup/seed_uc_scenario.py`, `supplycore/api/users.py`, `supplycore/supplycore/doctype/supplycore_settings/supplycore_settings.json` (site_name/site_address default), `README.md`, `FLOW.md`, và các chuỗi VN bệnh viện trong `frontend/src` (i18n, personas, labels).
- Đổi `site_name` default "Bệnh viện Y học cổ truyền Bộ Công an" → "Công ty Miyano Việt Nam"; địa chỉ tương ứng.
- `warehouse_map.py` SITE_NAME + docstring → Miyano; bản đồ khuôn viên → kho phân phối (giữ cơ chế, đổi nhãn).
- seed warehouses/departments: đổi "Kho Khoa Dược", "Khoa Cấp cứu"... → kho phân phối MVL (Kho Tổng, Kho Trung chuyển, Kho Giao hàng, phòng Thương Mại/Kho/Kế Toán). Giữ cấu trúc seed hợp lệ.
- `users.py` role-guide: bỏ "bệnh viện", "cấp phát BN" → thuật ngữ phân phối.
- README/FLOW: cập nhật mô tả sản phẩm + sơ đồ (chuỗi bán thay cấp phát).
- frontend VN prose bệnh viện → phân phối.
- [ ] Step 1: grep rộng `cấp phát|bệnh nhân|bệnh viện|khoa dược|Bộ Công an|YHCT` trên `supplycore/` + `frontend/src` (trừ backups) → liệt kê.
- [ ] Step 2: sửa từng nhóm sang Miyano/phân phối; giữ seed/test chạy được.
- [ ] Step 3: `bench migrate` + `bench build` sạch; grep lại → 0 (trừ lịch sử patch). Chạy 1 seed thử (nếu có runner an toàn) hoặc compile. **Commit** `chore(mvl): rebrand Miyano + reseed kho/phòng phân phối`

---

### Task 2: Đóng residual hardening — chặn /api/resource child cho portal
**Files:** `supplycore/hooks.py` (thêm `before_request` hoặc override), `supplycore/utils/permissions.py` hoặc `api/portal.py`; test `supplycore/tests/portal_isolation_test.py`.
- Vector còn hở: `/api/resource/<child doctype>/<name>` (SO Item/DN Item/SI Item/SFC Item) đọc 1 row nếu biết docname (hash). Đóng bằng `before_request` hook: nếu path khớp `/api/resource/{4 child doctype}` và user có role Portal → raise PermissionError. Hoặc dùng cơ chế Frappe phù hợp (kiểm tra `frappe.local.request.path`).
- [ ] Step 1 (RED): test `test_portal_rest_resource_child_denied()` — mô phỏng request path tới /api/resource child với portal user → PermissionError (hoặc test hàm guard trực tiếp). Chạy → FAIL.
- [ ] Step 2 (GREEN): implement guard. migrate/clear-cache. Run → PASS. Đảm bảo internal + /api/resource cho parent của chính khách vẫn OK.
- [ ] Step 3: portal_isolation_test + portal_api_test vẫn pass. **Commit** `fix(mvl-portal): đóng residual /api/resource child (hardening RSK-01)`

---

### Task 3: Trang Portal khách (www/portal) — tiêu thụ api/portal.py [UI — đọc frontend-design]
**Files:** Create `supplycore/www/portal/` (index.py + index.html + assets inline), có thể nhiều route (`portal/orders`, `portal/order/<name>`). ĐỌC skill `frontend-design` trước.
- Trang khách (chỉ role Portal; guest → redirect login): 
  - Đăng nhập (Frappe login) → trang chủ khách.
  - `catalog`: bảng giá theo HĐ khung (gọi `portal_catalog`).
  - `contracts`: HĐ khung hiệu lực (`portal_contracts`).
  - Đặt hàng: form giỏ hàng theo HĐ (gọi `portal_order_place`).
  - Theo dõi đơn: list (`portal_order_history`) + chi tiết tracker **4 cột mốc** (`portal_order_track`) dạng timeline.
  - Tải chứng từ (`portal_document_download`).
- Design: sạch, mobile-first (BA có khung điện thoại), nhất quán màu (navy #1F4E79 theo UI spec BA). KHÔNG để lộ dữ liệu/menu nội bộ.
- Guard: `get_context` kiểm role Portal; mọi data qua api/portal.py (đã cô lập backend).
- [ ] Step 1: đọc frontend-design; dựng khung trang + get_context guard role Portal.
- [ ] Step 2: các màn catalog/contracts/order/track gọi API; render tracker 4 cột mốc.
- [ ] Step 3: `bench build`/clear-cache; thử tải trang (curl /portal khi guest → login redirect; khi portal user → 200). **Commit** `feat(mvl-portal): trang Portal khách www/portal (catalog/đặt hàng/4 cột mốc)`

---

### Task 4: Đưa M7 Sales vào SPA nội bộ + Dashboard công nợ phải thu
**Files:** `frontend/src/modules.js` (thêm module M7 Sales + 7 doctype), `frontend/src/schemas.js`/`detail-configs.js` (cấu hình list/form cho SC Customer/Sales Order/Delivery Note/Sales Invoice/Sales Receipt/SFC), `supplycore/api/kpi.py` hoặc `m8_accounting/api/financial_reports.py` (AR aging theo khách), 1 dashboard view.
- SPA nội bộ: thêm "M7 Sales" vào modules.js (mirror module khác) → 7 doctype hiện trong SPA list/form (DocView generic). Nhân sự nội bộ thao tác Sales trong SPA.
- Dashboard công nợ phải thu: API `ar_aging_by_customer()` (mirror `bhyt`-đã-xóa/ap_aging) → tổng phải thu theo khách + tuổi nợ + cảnh báo vượt credit_limit (BRU-AR-001). Hiển thị trong dashboard M11 hoặc M8.
- [ ] Step 1: thêm module + doctype vào SPA (modules.js/schemas/detail-configs) — mirror pattern hiện có.
- [ ] Step 2: API AR aging + số liệu dashboard; test `run` cơ bản.
- [ ] Step 3: `bench build` sạch; SPA load M7 Sales; dashboard trả số. **Commit** `feat(mvl-sales): M7 Sales trong SPA nội bộ + dashboard công nợ phải thu`

---

### Task 5: Regression tổng thể + tài liệu hoàn tất
- [ ] Step 1: `bench migrate` + `bench build --app supplycore` + `frappe.ping` sạch.
- [ ] Step 2: chạy TẤT CẢ suite (GĐ2 sales + GĐ3 portal + isolation + smoke_m8/m10 + uc26) → pass; grep hospital → 0.
- [ ] Step 3: cập nhật `docs/ba-miyano/PHAN_TICH_HUONG_THIET_KE_MVL.md` mục tiến độ (GĐ1-4 done); README.
- [ ] Step 4: **Commit** `docs(mvl): hoàn tất GĐ4 — thành phẩm SupplyCore MVL theo BA`

---

## Định nghĩa Done (GĐ4 = thành phẩm)
- [ ] Không còn nhận diện/data bệnh viện; sản phẩm là MVL phân phối.
- [ ] Trang Portal khách chạy (catalog/đặt hàng/4 cột mốc), cô lập giữ nguyên.
- [ ] M7 Sales dùng được trong SPA nội bộ; dashboard công nợ phải thu.
- [ ] Residual hardening đóng. Toàn bộ test pass, build/migrate sạch.
- [ ] Sẵn sàng bàn giao / merge `feat/mvl-distributor`.
