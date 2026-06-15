# SupplyCore — Bộ cài Windows 1-file (QEMU nhúng) — Design Spec

**Ngày:** 2026-06-15
**Branch:** `feat/windows-installer`
**Mục tiêu:** Đóng gói SupplyCore thành **một file `.exe` cài đặt duy nhất** cho máy **Windows** của bệnh viện. IT chỉ double-click → đợi → mở trình duyệt. **Không phải tự cài Docker, không phải tự cài Linux/VirtualBox.** Chạy được **offline**.

---

## 1. Sự thật nền tảng (ràng buộc bất biến)

- SupplyCore xây trên **Frappe v15** — **không chạy native trên Windows** (cần MariaDB + Redis + bench/gunicorn + nginx trong môi trường Linux). Không có đường "chạy thẳng Windows".
- Do đó **bắt buộc có một lớp Linux** ở đâu đó. Quyết định: lớp Linux này **nhúng trong một VM ẩn**, người cài không bao giờ thấy hay phải cài thủ công.
- Phân biệt rõ với người dùng:
  - "IT không phải tự tay cài Docker/Linux" → **đáp ứng được**.
  - "Trong máy hoàn toàn không có Linux nào" → **không thể** (và spec này không hứa điều đó).

## 2. Quyết định kiến trúc (đã chốt với người dùng)

| Hạng mục | Lựa chọn | Ghi chú |
|---|---|---|
| Lớp chạy | **QEMU nhúng** (Cách A) | Hypervisor portable, không cài; VM Linux ẩn |
| Tăng tốc | **A1: WHPX** (Windows Hypervisor Platform) | Nhanh gần native; **đánh đổi**: cần admin bật feature + có thể reboot 1 lần |
| App trong VM | **Docker Engine + compose + image SupplyCore đã build** | Tái dùng 100% pipeline GHCR hiện có |
| Định dạng phân phối | **1 file `.exe`** (Inno Setup) + `.sha256` | Offline-capable |
| Dịch vụ nền | **WinSW** (Windows Service wrapper) | Auto-start, auto-restart, chạy ẩn |
| Dữ liệu ban đầu | **Site trống + app** (Administrator), không seed | Giữ nguyên quyết định spec docker-packaging |

**Tinh thần Cách A1:** ưu tiên hiệu năng (WHPX) hơn là "tuyệt đối không đụng host". Người dùng đã chấp nhận bật WHPX + reboot 1 lần khi cần.

## 3. Kiến trúc runtime

```
Windows host (IT chỉ thấy phần này)
├── SupplyCore-Setup-vX.exe       ← 1 file cài duy nhất (Inno Setup)
├── Windows Service (WinSW)        ← tự khởi động cùng máy, auto-restart, chạy ẩn
└── QEMU portable (win64, đi kèm — không cài)
        │ headless, accel=whpx, hostfwd tcp:127.0.0.1:<PORT>-:80
        ▼
   VM Linux ẩn hoàn toàn (Ubuntu Server cloud image, headless)
   ├── Docker Engine (Apache-2.0, miễn phí — KHÔNG phải Docker Desktop)
   │     └── docker compose up  →  image SupplyCore (nginx + gunicorn + workers)
   │           ├── MariaDB         (volume → /data trên disk1)
   │           └── Redis           (cache/queue)
   ├── disk0  (OS + Docker + image SupplyCore)   ← THAY khi update
   └── disk1  (/data: MariaDB + sites + backups) ← KHÔNG đụng khi update
```

**Luồng người dùng cuối:** double-click `.exe` → wizard → đợi healthy → mở `http://localhost:<PORT>` → đăng nhập Administrator.

### 3.1 Mạng
- QEMU **user-mode networking** (`-netdev user`) + `hostfwd` `127.0.0.1:<PORT>` (host) → `:80` (guest nginx).
- Mặc định `<PORT>=80`; wizard cho đổi nếu cổng bận. Chỉ bind `127.0.0.1` (không lộ ra LAN trừ khi cấu hình thêm — quyết định sau, ngoài phạm vi v1).

### 3.2 Hiệu năng / WHPX
- QEMU chạy `-accel whpx,kernel-irqchip=off` (fallback `-accel tcg` nếu WHPX không bật được, kèm cảnh báo chậm trong log + UI).
- Wizard kiểm tra WHPX; nếu thiếu → `DISM /Enable-Feature /FeatureName:HypervisorPlatform` (cần admin) → có thể yêu cầu reboot rồi tiếp tục cài sau reboot.

## 4. Các thành phần (đơn vị tách bạch)

| Đơn vị | Nhiệm vụ | Phụ thuộc |
|---|---|---|
| `installer/supplycore.iss` | Script Inno Setup: wizard, bung file, gọi WHPX check, tạo disk1, đăng ký service, mở browser | Inno Setup |
| `installer/whpx-check.ps1` | Phát hiện + bật WHPX, xử lý reboot-resume | DISM |
| `installer/winsw/supplycore-service.xml` | Định nghĩa service chạy QEMU launcher | WinSW.exe |
| `installer/launcher/run-vm.ps1` (hoặc `.cmd`) | Build dòng lệnh QEMU (accel, disks, hostfwd), chạy headless, log | QEMU portable |
| `installer/launcher/wait-healthy.ps1` | Poll `http://127.0.0.1:<PORT>/supplycore` tới khi 200 | — |
| `guest/packer/supplycore.pkr.hcl` | Build disk0: Ubuntu cloud + Docker + load image + compose + first-boot | Packer, QEMU/KVM (CI) |
| `guest/first-boot.sh` | Idempotent (xem §4b): đảm bảo DB_PASSWORD bền → `compose up -d` → chờ backend healthy → `bench migrate`. Compose lo tạo site. | cloud-init / systemd oneshot |
| `guest/backup.timer` + `guest/backup.sh` | `bench backup --with-files` → `/data/backups` | systemd timer |
| `.github/workflows/build-installer.yml` | CI: build image → build disk0 → đóng `.exe` → publish artifact | GHCR build hiện có |

Mỗi đơn vị test độc lập được: launcher test bằng disk giả + port; first-boot test trong CI Linux; installer test trên runner Windows.

## 4b. Integration contract (chỉnh 2026-06-15, sau khi đọc kỹ `deploy/compose.yml`)

Phát hiện: `deploy/compose.yml` **đã tự lo provisioning** — service `configurator` (set common_site_config) + `create-site` (`bench new-site --install-app supplycore`, idempotent qua `[ -d sites/$SITE_NAME ]`), và `backend` `depends_on: create-site: service_completed_successfully`. Vì vậy:

- **Compose sở hữu provisioning.** `first-boot.sh` **KHÔNG** được `bench new-site`/`install-app` nữa (sẽ drop site create-site vừa tạo, install-app lần 2 lỗi → `set -e` → re-provision vô hạn). `first-boot.sh` thu gọn còn: đảm bảo `DB_PASSWORD` bền trên disk1 → `docker compose up -d` (có env) → chờ `backend` healthy → `bench migrate`. **Bỏ marker** (`create-site` + `migrate` đều idempotent).
- **Offline (bắt buộc):** `compose.yml` mặc định `pull_policy: always` → air-gapped sẽ fail dù đã `docker load`. Guest env **phải** đặt `PULL_POLICY=never`.
- **Tag image phải khớp:** compose resolve `${IMAGE:-ghcr.io/mvl26/supplycore}:${IMAGE_TAG:-latest}`. Image `docker load` trong disk0 **phải** mang đúng tag đó (tag-on-save về `ghcr.io/mvl26/supplycore:latest`), nếu không `pull_policy:never` không tìm thấy → VM không lên. **Smoke test Task 9 là cổng kiểm tra điều này.**
- **Cổng:** `frontend` publish `${HTTP_PORT:-8080}:8080`. Guest env đặt `HTTP_PORT=80` để khớp hostfwd `…-:80` của run-vm.ps1 (run-vm/wait-healthy **không** cần sửa).
- **SITE_NAME chuẩn hoá = `supplycore.localhost`** (mặc định của compose; nuôi `FRAPPE_SITE_NAME_HEADER`). Phải đồng nhất ở cloud-init + first-boot.
- **`/data/supplycore.env`** (systemd `EnvironmentFile`, được compose interpolate qua env của first-boot.sh) mang: `DATA_DIR`, `COMPOSE_DIR`, `SITE_NAME=supplycore.localhost`, `HTTP_PORT=80`, `PULL_POLICY=never`, `ADMIN_PASSWORD=__…__`. **KHÔNG** chứa `DB_PASSWORD`.
- **`DB_PASSWORD` bền theo disk1:** sinh 1 lần trong guest (`first-boot.sh`) nếu `/data/.db_password` thiếu, đọc lại nếu đã có (mariadb root password gắn với data trên disk1 — đổi password khi data đã init → auth fail). KHÔNG inject từ host (vì update thay disk0 → `/var/lib/cloud` mới → cloud-init coi là instance mới → write_files chạy lại, có thể clobber).

## 5. Xử lý 4 yêu cầu ẩn

### 5.1 Lưu dữ liệu qua update (quan trọng nhất)
- **Hai đĩa ảo tách biệt.** `disk0` = OS + Docker + image (thay được). `disk1` = dữ liệu, mount vào guest `/data`.
- `compose.yml` map volume MariaDB + thư mục `sites` của Frappe vào bind-mount dưới `/data` (không để trên overlay của Docker mặc định → không nằm trên disk0).
- Update = thay disk0, **giữ disk1**. Cài lại / gỡ-cài lại **không xoá disk1** trừ khi người dùng chủ động chọn "xoá dữ liệu".

### 5.2 Update offline (re-runnable)
- Phát hành `.exe` phiên bản mới (hoặc gói update nhỏ chỉ chứa disk0 + launcher).
- Quy trình: stop service → backup tự động trước update → thay `disk0` → start → `first-boot.sh` phát hiện site đã tồn tại → chạy `bench migrate` → healthy.
- Hoàn toàn offline (không pull registry). Re-runnable, idempotent.

### 5.3 Backup / restore
- Trong guest: systemd timer chạy `bench backup --with-files` định kỳ (mặc định hằng ngày) → `/data/backups` (trên disk1, sống qua update).
- Host: shortcut "Sao lưu SupplyCore" copy `/data/backups` ra thư mục Windows do người dùng chọn (qua QEMU shared folder / scp tới guest).
- Restore: README ghi rõ `bench restore <file>` trong guest; v1 thực hiện thủ công có hướng dẫn.

### 5.4 Khởi tạo Administrator
- Wizard Inno Setup có trường **mật khẩu Administrator** (bắt buộc, có xác nhận).
- Truyền vào guest an toàn qua cloud-init user-data (không log plaintext). `first-boot.sh`: `bench new-site --admin-password <pw> --no-mariadb-socket` (site trống) → `bench install-app supplycore`.
- Nếu để trống: sinh mật khẩu ngẫu nhiên mạnh, hiển thị 1 lần cuối wizard + ghi vào file bảo mật cục bộ.

## 6. Build & phân phối (CI)

`.github/workflows/build-installer.yml` — trigger: push tag `v*` + `workflow_dispatch`.

1. **Build image SupplyCore** (job hiện có / reuse) → image local.
2. **Build disk0** (runner Linux có KVM): Packer + QEMU dựng Ubuntu Server cloud image → cài Docker Engine → `docker load` image SupplyCore → copy `compose.yml`, `first-boot.sh`, backup units → cấu hình systemd oneshot → nén `qcow2`.
3. **Smoke test guest** (CI Linux): boot disk0 + disk1 trống → chờ healthy → `curl -f` site root + `/supplycore` = 200 → assert `supplycore` trong `apps.txt`.
4. **Đóng gói** (runner Windows): tải QEMU portable win64 (pinned version + checksum), WinSW (pinned), `disk0.qcow2` → Inno Setup compile → `SupplyCore-Setup-vX.exe`.
5. **Test installer** (runner Windows): cài im lặng → service lên → `curl http://localhost` 200 → gỡ cài sạch (giữ tùy chọn dữ liệu).
6. Publish artifact `.exe` + `.sha256` (GitHub Release của tag).

**Pin & checksum bắt buộc:** QEMU portable, WinSW, Ubuntu cloud image — tất cả pin phiên bản + verify SHA256 (offline-reproducible, không phụ thuộc nguồn online lúc cài).

## 7. Kiểm thử

| Mức | Nơi chạy | Kiểm tra |
|---|---|---|
| Guest smoke | CI Linux + KVM | site root 200, `/supplycore` 200, `supplycore` in `apps.txt` |
| Persistence | CI Linux | tạo dữ liệu → thay disk0 (giả update) → dữ liệu còn |
| First-boot idempotent | CI Linux | boot 2 lần không tạo lại site, lần 2 chạy migrate |
| Installer | CI Windows | cài im lặng, service Running, `localhost` 200, gỡ cài sạch |
| WHPX fallback | thủ công | tắt WHPX → launcher fallback tcg + cảnh báo |

## 8. Phạm vi v1 / Ngoài phạm vi (YAGNI)

**Trong v1:** 1 file `.exe`, WHPX (A1), site trống + admin, persistence 2-đĩa, update offline re-runnable, backup theo lịch, restore có hướng dẫn thủ công, bind `127.0.0.1`.

**Ngoài v1 (ghi nhận, không làm):**
- Lộ ra LAN cho nhiều máy trạm (multi-client) — v1 chỉ localhost.
- UI restore 1-click (v1 dùng CLI có hướng dẫn).
- Auto-update kiểm tra phiên bản (v1 update thủ công bằng `.exe` mới).
- Seed dữ liệu mẫu.
- HTTPS/chứng chỉ (v1 HTTP localhost).

## 9. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| WHPX không bật được (policy/CPU cũ) | Fallback TCG + cảnh báo rõ; tài liệu yêu cầu phần cứng |
| Xung đột với Hyper-V/WSL2 đang chạy (cùng dùng hypervisor platform) | Kiểm tra & tài liệu; WHPX đồng tồn với Hyper-V được trên Win 10/11 mới |
| File `.exe` quá nặng (~1.5–3GB) | Nén qcow2, dùng SDelete trim trước nén; phát hành qua Release/USB |
| Mất dữ liệu khi gỡ cài nhầm | Mặc định GIỮ disk1; xoá dữ liệu là lựa chọn riêng, có cảnh báo |
| Quyền admin để bật WHPX/đăng ký service | Wizard yêu cầu elevation; ghi rõ trong README cho IT |

---

## Phụ lục: tái dùng từ branch `feat/docker-packaging`
- `deploy/compose.yml`, `docker/Containerfile`, image SupplyCore (GHCR) — dùng nguyên trong guest.
- Quyết định "site trống + Administrator, không seed" — giữ.
- Logic build Vue SPA trong builder stage — đã nằm trong image, không lặp lại.
