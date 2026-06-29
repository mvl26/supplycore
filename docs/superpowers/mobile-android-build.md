# SupplyCore Mobile — Build & chạy trên Android (thủ công)

> Phần này KHÔNG chạy được trên máy CI/dev hiện tại (không có Android SDK/Java).
> Làm trên máy có **Android Studio + JDK 17**. Toàn bộ code/web đã sẵn sàng;
> đây chỉ là bước đóng gói + kiểm thử thiết bị.

## 0. Yêu cầu
- Android Studio (kèm Android SDK, Platform-Tools) + JDK 17.
- Một thiết bị Android (bật USB debugging) hoặc emulator có camera.
- Một server SupplyCore truy cập được từ điện thoại (LAN hoặc HTTPS công khai),
  và endpoint `supplycore.api.mobile.mobile_login` đã deploy (Task 1).

## 1. Build bundle native + sync
```bash
cd frontend
npm install                 # nếu chưa cài deps
npm run cap:sync            # = build:native (CAP_BUILD=1 vite build → dist/) + cap sync
```
`cap:sync` đã định nghĩa trong `package.json`. Nó tạo `dist/` (base `./`, có
`dist/index.html` do plugin `nativeIndexHtml` sinh) rồi copy vào `android/`.

## 2. Mở & chạy
```bash
npx cap open android        # mở Android Studio
```
Trong Android Studio: chọn thiết bị → ▶ Run. (Gradle sync lần đầu sẽ tải dependencies.)

## 3. Quyền
`android/app/src/main/AndroidManifest.xml` đã khai báo `INTERNET` + `CAMERA`.
Lần đầu quét mã, Android sẽ hỏi quyền camera — chọn Cho phép.

## 4. Checklist kiểm thử 4 luồng (đối chiếu web — cùng dữ liệu)
Đăng nhập: nhập URL server thật + tài khoản SupplyCore (token auth qua mobile_login).

- [ ] **Cấu hình + đăng nhập**: nhập URL + user/pwd → vào tab Tra cứu. Sai mật khẩu → báo lỗi rõ.
- [ ] **Tra cứu tồn/lô**: tìm 1 vật tư có thật → hiện tồn/lô/HSD (FEFO). Quét 1 barcode → ra kết quả.
- [ ] **Duyệt phiếu**: thấy phiếu chờ duyệt thật (HĐ khung / Đơn mua / YCMH) → Duyệt/Từ chối → kiểm tra trạng thái đổi trên web.
- [ ] **Tiếp nhận**: mở 1 phiếu nhập Draft → nhập SL (`qty`) + quét lô NCC → Xác nhận → kiểm tra web đã nhập kho.
- [ ] **Dashboard**: KPI (sắp hết hạn/tồn thấp/PO chờ) + cảnh báo khớp web; "Làm mới" hoạt động; "Đăng xuất" về màn cấu hình.
- [ ] **Không lỗi CORS/CSRF** trong Logcat (token auth + CapacitorHttp).
- [ ] **Web KHÔNG regress**: mở `/supplycore` trên desktop, đăng nhập + thao tác vài module → như cũ.

## 5. Đóng gói phát hành (sau khi kiểm thử)
- **Android**: Build → Generated Signed Bundle/APK (cần keystore); upload `.aab` lên Play Console ($25 một lần).
- **iOS**: cần máy **Mac + Xcode** (`npx cap add ios` + `npx cap open ios`) và Apple Developer ($99/năm). Chưa scaffold ở đây.

## Ghi chú kiến trúc (đã triển khai)
- Auth native = token (`Authorization: token key:secret`) từ `mobile_login`; web giữ session+CSRF.
- `api.js` dual-mode: native → base URL cấu hình + token + CapacitorHttp; web → same-origin.
- Router history base `/` khi native, `/supplycore/` khi web. App.vue bỏ AppShell desktop cho route mobile.
- Spec: `docs/superpowers/specs/2026-06-29-supplycore-mobile-capacitor-design.md`
- Plan: `docs/superpowers/plans/2026-06-29-supplycore-mobile-capacitor.md`
