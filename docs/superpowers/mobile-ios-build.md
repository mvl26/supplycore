# SupplyCore Mobile — Build cho iPhone (iOS)

> ⚠️ **iPhone KHÔNG cài được file `.apk`** (đó là của Android). iOS dùng file **`.ipa`**.
> ⚠️ **Build iOS BẮT BUỘC máy Mac + Xcode** — ràng buộc tuyệt đối của Apple, KHÔNG
> build được trên Linux/Windows. Project iOS đã được scaffold sẵn (`frontend/ios/`),
> chỉ cần build trên Mac (hoặc CI macOS).

Codebase dùng chung Android — KHÔNG phải viết lại. Mọi màn hình / tính năng giống hệt.

---

## Bạn cần gì để cài lên iPhone

| Mục | Bắt buộc? | Ghi chú |
|---|---|---|
| Máy **Mac** + **Xcode** (hoặc CI macOS) | ✅ Bắt buộc | Apple chỉ cho build iOS trên macOS |
| **CocoaPods** (`sudo gem install cocoapods`) | ✅ | Cài thư viện native |
| **Apple ID** (miễn phí) | Tối thiểu | Sideload qua Xcode, app **hết hạn sau 7 ngày**, tối đa 3 app/thiết bị |
| **Apple Developer** ($99/năm) | Để dùng lâu dài | TestFlight / phân phối nội bộ / lên App Store; app không hết hạn 7 ngày |

> Không có Mac **và** không có Apple Developer → iOS trên iPhone thật KHÔNG khả thi.
> (Có thể dùng tạm web app trên Safari, nhưng KHÔNG có giao diện mobile native.)

---

## Cách 1 — Build trên máy Mac (đơn giản nhất)

```bash
# 1. Lấy code về Mac, vào frontend/
cd frontend
npm install

# 2. Build bundle web + đồng bộ vào iOS
npm run build:native        # CAP_BUILD=1 → dist/
npx cap sync ios            # copy dist/ + cài CocoaPods (pod install)

# 3. Mở Xcode
npx cap open ios            # mở ios/App/App.xcworkspace
```

Trong **Xcode**:
1. Chọn target **App** → tab **Signing & Capabilities** → chọn **Team** (Apple ID của bạn) → Xcode tự tạo provisioning.
2. Cắm iPhone qua cáp (bật Developer Mode trên iPhone: Settings → Privacy & Security → Developer Mode).
3. Chọn thiết bị ở thanh trên → bấm **▶ Run**.
4. Lần đầu: trên iPhone vào **Settings → General → VPN & Device Management** → tin tưởng (Trust) chứng chỉ developer.
5. Mở app **SupplyCore** → nhập URL server + đăng nhập.

**Tạo file `.ipa` để gửi người khác:** Xcode → **Product → Archive** → **Distribute App** → Ad Hoc / Development (cần Apple Developer + thiết bị đã đăng ký UDID), hoặc TestFlight.

> iPhone test cùng cách Android: nhập URL server (vd `https://blockishly-unvowed-anglea.ngrok-free.dev`) + tài khoản. ATS đã bật cho http:// LAN (Info.plist).

---

## Cách 2 — Không có Mac: CI macOS (GitHub Actions)

GitHub Actions có **macOS runner** → build `.ipa` mà không cần Mac vật lý. **Vẫn cần Apple
Developer ($99/năm)** để ký (signing certificate + provisioning profile) — CI chỉ thay
cái máy, không thay được chữ ký của Apple.

Khung workflow (cần thêm secrets: certificate .p12, provisioning profile, App Store Connect API key):

```yaml
# .github/workflows/ios.yml
name: Build iOS IPA
on: workflow_dispatch
jobs:
  build:
    runs-on: macos-14
    defaults: { run: { working-directory: frontend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 18 }
      - run: npm ci
      - run: npm run build:native
      - run: npx cap sync ios
      # — Ký + archive (cần import cert/profile từ secrets) —
      - run: |
          cd ios/App && pod install
          xcodebuild -workspace App.xcworkspace -scheme App \
            -configuration Release -archivePath build/App.xcarchive archive
          xcodebuild -exportArchive -archivePath build/App.xcarchive \
            -exportPath build -exportOptionsPlist ExportOptions.plist
      - uses: actions/upload-artifact@v4
        with: { name: SupplyCore-ipa, path: frontend/ios/App/build/*.ipa }
```

(Bảo tôi nếu muốn dựng đầy đủ workflow này — cần bạn cung cấp thông tin Apple Developer.)

---

## Đã chuẩn bị sẵn trong repo (Linux)
- `frontend/ios/` — project Xcode (App.xcworkspace, Podfile, plugins) qua `cap add ios`.
- `Info.plist`: **NSCameraUsageDescription** (quét mã) + **NSAppTransportSecurity** (http LAN).
- `appId = vn.com.miyano.supplycore`, `appName = SupplyCore`, `webDir = dist`.
- Trên Mac chỉ còn: `pod install` (tự chạy khi `cap sync ios`) → mở Xcode → Run.

## Khác biệt Android vs iOS (đã xử lý cùng codebase)
| | Android | iOS |
|---|---|---|
| File cài | `.apk` (đã có) | `.ipa` (build trên Mac) |
| Quyền camera | AndroidManifest CAMERA | Info.plist NSCameraUsageDescription ✅ |
| http LAN | usesCleartextTraffic ✅ | NSAppTransportSecurity ✅ |
| Quét mã | startScan (ML Kit) | startScan (ML Kit) — giống nhau |
