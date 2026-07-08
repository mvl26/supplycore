# SupplyCore Mobile (Capacitor) — Thiết kế

- **Ngày**: 2026-06-29
- **Trạng thái**: Đã duyệt thiết kế, chờ lập kế hoạch triển khai
- **Mục tiêu**: App điện thoại native (App Store / CH Play) cho SupplyCore, **dùng chung dữ liệu** với web app Frappe hiện tại, cho phép xem và thực hiện vài thao tác đơn giản khi đi lại trong kho/khoa.

## 1. Bối cảnh & ràng buộc

- SupplyCore hiện là **Vue 3 SPA + Frappe backend**, phục vụ tại `/supplycore`, đã có sẵn hạ tầng PWA (service worker, `vite-plugin-pwa`).
- Frontend gọi API qua `frontend/src/api.js`: `fetch` **same-origin** (`/api/...`), `credentials: 'include'` (session cookie), **CSRF token lấy từ trang shell do Frappe render** (`{{ csrf_token }}` qua `window.sc_csrf` / meta tag).
- Triển khai **on-prem từng bệnh viện** (Docker / Windows installer) → mỗi bệnh viện một server riêng.
- Yêu cầu người dùng: app chạy được trên web **và** là app native, dùng chung 1 dữ liệu, chỉ cần "xem + vài thao tác đơn giản" trên điện thoại.

### Quyết định đã chốt (qua brainstorming)

| Vấn đề | Quyết định |
|---|---|
| Hình thức | App native lên App Store / CH Play |
| Cách dựng | **Capacitor bọc app Vue sẵn có** (1 codebase cho cả web lẫn native) |
| Kết nối server | App **nhập URL server lúc đăng nhập** (linh hoạt nhiều bệnh viện dùng chung 1 bản app) |
| Auth | **Token auth** (Frappe API key) — bỏ qua CSRF/CORS |
| Phạm vi v1 | 4 luồng: tra cứu tồn/lô, duyệt phiếu, tiếp nhận, dashboard+cảnh báo — **online-only** |
| Push notification | **Giai đoạn riêng sau v1** |
| Ghi offline / đồng bộ | **Ngoài phạm vi** (dự án riêng) |

## 2. Kiến trúc tổng thể

**Một codebase duy nhất** — cùng project Vue hiện tại (`frontend/`). Capacitor đóng gói chính bundle Vue đó thành app native (Android `.apk/.aab`, iOS `.ipa`).

- **Web**: chạy y như cũ tại `/supplycore`, **không đổi** trải nghiệm hay cơ chế auth.
- **Native**: cùng code, nhận diện `Capacitor.isNativePlatform()` để bật lớp mobile (mobile shell + base URL cấu hình + token auth).

**Dùng chung**: stores (Pinia), `api.js`, `actions.js`, `schemas.js`, `i18n.js`, `modules.js`.
**Làm mới**: một **"mobile shell" gọn** (thanh tab dưới đáy, 4 màn hình + màn cấu hình/đăng nhập). **KHÔNG** nhồi giao diện desktop (sidebar, datatable rộng) vào webview điện thoại.

## 3. Kết nối server & Auth (phần lõi)

### 3.1 Cấu hình server + đăng nhập

1. **Màn hình cấu hình lần đầu** (chỉ hiện ở native, khi chưa có cấu hình): nhập URL server (vd `https://bv-abc.example.com`). Validate định dạng URL. Lưu bằng `@capacitor/preferences`.
2. **Đăng nhập**: app POST `usr`/`pwd` tới endpoint backend mới **`supplycore.api.mobile.mobile_login`**:
   - Server xác thực credentials (dùng `frappe.auth` / `frappe.local.login_manager` hoặc kiểm tra password hợp lệ).
   - Sinh (nếu chưa có) hoặc đọc cặp **`api_key` + `api_secret`** của user và trả về app. (Secret chỉ vào được lúc sinh, nên **phải vend từ server**.)
   - Trả thêm thông tin tối thiểu: tên user, roles/persona để dựng nav.
3. App lưu `serverUrl`, `api_key`, `api_secret` qua `@capacitor/preferences` (cân nhắc secure storage cho secret ở bản sau).

### 3.2 `api.js` dual-mode

`api.js` phân nhánh theo `Capacitor.isNativePlatform()`:

- **Native** → `baseURL = serverUrl` đã cấu hình; header `Authorization: token <api_key>:<api_secret>`; **không gửi CSRF**; dùng **CapacitorHttp** (bật trong `capacitor.config`) để request native bỏ qua rào CORS của webview.
- **Web** → `baseURL = ''` (same-origin) + `credentials:'include'` + CSRF **y như hiện tại** (KHÔNG đổi, tránh regress 11 module web).

> **Ràng buộc bắt buộc**: việc thêm base URL cấu hình **không được phá** đường same-origin của web. Nhánh web phải giữ nguyên hành vi hiện tại.

### 3.3 Backend mới — phạm vi tối thiểu

- **Chỉ thêm đúng 1 surface mới**: `supplycore/api/mobile.py` với `@frappe.whitelist(allow_guest=True)` `mobile_login`.
- Toàn bộ `/api/resource`, `/api/method/*`, và các action trong `actions.js` chạy **y nguyên** dưới token auth (Frappe REST hỗ trợ sẵn `Authorization: token`).
- Cần xác nhận CORS phía Frappe (`allow_cors` trong `site_config`) phù hợp — nhưng CapacitorHttp giảm phụ thuộc vào CORS browser.

## 4. Phạm vi v1 — 4 luồng (online-only)

Thanh tab dưới đáy, 4 màn hình tối giản, tái dùng stores/api có sẵn:

1. **Tra cứu tồn kho / lô** — tìm vật tư; xem tồn + hạn dùng (FEFO) + vị trí lô. Có **quét barcode** (`@capacitor-mlkit/barcode-scanning`) để tra nhanh.
2. **Duyệt / ký phiếu** — danh sách phiếu chờ (PO, chuyển kho, cấp phát, thanh toán...) → mở xem gọn → **Duyệt / Từ chối** (gọi action submit/approve đã có trong `actions.js`).
3. **Tiếp nhận / nhập kho** — quét mã xác nhận nhận hàng, nhập số lượng thực nhận. Validation FEFO/lô **do server lo** → cần online.
4. **Dashboard & Cảnh báo** — tóm tắt + danh sách cảnh báo (sắp hết hạn, tồn thấp, phiếu chờ) lấy bằng **polling / in-app** (mở app là cập nhật), **không** push.

RBAC: tái dùng `personas.js` + `access` store; nav mobile lọc theo quyền y như web.

## 5. Ngoài phạm vi v1 (ghi rõ, không âm thầm bỏ)

- **Push notification thật** (FCM Android + APNs iOS + bộ gửi *từng server* on-prem hoặc relay trung tâm) → **giai đoạn riêng sau v1**. Lý do: nặng + vướng mô hình mỗi bệnh viện 1 server (mỗi server cần credential push hoặc relay chung).
- **Ghi offline / đồng bộ** (kể cả ý tưởng "PDA offline IndexedDB" ở Phase 3 design) → tách dự án riêng (cần giải xung đột + FEFO/lô phía server). v1 **yêu cầu online**.

## 6. Cấu trúc thư mục dự kiến

```
frontend/
  src/
    mobile/                    # MỚI — shell + màn hình mobile
      MobileShell.vue          # bottom-tab layout
      ServerConfig.vue         # nhập URL server (first-run)
      MobileLogin.vue
      screens/
        StockLookup.vue        # + barcode
        ApproveDocs.vue
        Receiving.vue          # + barcode
        MobileDashboard.vue
      mobileRouter.js          # hoặc nhánh trong router.js
    api.js                     # SỬA — dual-mode base URL + token
    platform.js                # MỚI — wrapper Capacitor (isNative, preferences, http, scanner)
  capacitor.config.ts          # MỚI
  android/                     # MỚI (sinh bởi `npx cap add android`)
  ios/                         # MỚI (chỉ build trên Mac)
supplycore/
  api/
    mobile.py                  # MỚI — endpoint mobile_login
```

## 7. Phụ thuộc & điều kiện build

- npm: `@capacitor/core`, `@capacitor/cli`, `@capacitor/android` (+ `@capacitor/ios`), `@capacitor/preferences`, `@capacitor-mlkit/barcode-scanning`.
- **Android**: Android Studio + JDK; Play Console ($25 một lần) để phát hành.
- **iOS**: **bắt buộc máy Mac + Xcode**; Apple Developer ($99/năm) để phát hành.
- Ghi chú: nếu sau này chỉ cần "cài lên điện thoại" (không cần store), hạ tầng **PWA sẵn có** lo được ~90% mà khỏi pipeline iOS/Android.

## 8. Tiêu chí thành công v1

- Cài bản native trên 1 điện thoại Android, nhập URL server thật, đăng nhập bằng tài khoản SupplyCore.
- Thực hiện được trọn 4 luồng v1 với dữ liệu thật (cùng dữ liệu web).
- Web app 11 module **không regress** (auth same-origin + CSRF giữ nguyên).
- Quét barcode tra cứu được ít nhất 1 vật tư.

## 9. Rủi ro & điểm cần xác minh khi triển khai

- **CORS/CapacitorHttp**: xác minh request native tới Frappe qua CapacitorHttp hoạt động với token (không cần CSRF).
- **Vend api_secret**: xác nhận cách lấy/sinh secret an toàn trong `mobile_login` (Frappe chỉ trả secret lúc generate).
- **Base URL không phá web**: test kỹ nhánh web sau khi refactor `api.js`.
- **Barcode plugin**: quyền camera (Android/iOS manifest) + định dạng mã thực tế dùng trong kho.
