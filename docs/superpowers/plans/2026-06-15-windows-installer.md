# Windows 1-File Installer (QEMU nhúng) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Đóng gói SupplyCore thành **một file `SupplyCore-Setup-vX.exe`** cài trên Windows bệnh viện (offline), chạy app trong một VM Linux ẩn (QEMU+WHPX → Docker Engine → image SupplyCore), không bắt IT tự cài Docker/Linux.

**Architecture:** QEMU portable nhúng trong installer chạy headless một VM Ubuntu (disk0 = OS+Docker+image, disk1 = dữ liệu bền). Trong VM, `docker compose` chạy image SupplyCore đã build ở `feat/docker-packaging`. WinSW chạy QEMU như Windows Service. Inno Setup gói tất cả thành 1 `.exe`. CI (GitHub Actions) build disk0 bằng Packer trên runner Linux+KVM, smoke test, rồi gói `.exe` trên runner Windows.

**Tech Stack:** QEMU (qemu-w64), Ubuntu 22.04 cloud image, cloud-init, Docker Engine + compose, systemd, WinSW v2.12.0, Inno Setup 6, Packer, GitHub Actions, bats (shell test), PowerShell Pester.

**Spec:** `docs/superpowers/specs/2026-06-15-windows-installer-design.md`

**Reuse từ `feat/docker-packaging`:** `deploy/compose.yml`, `docker/Containerfile`, image SupplyCore. Quyết định "site trống + Administrator, không seed".

---

## File Structure

```
installer/
├── supplycore.iss                    # Inno Setup: wizard, bung file, WHPX, tạo disk1, service, browser
├── whpx-check.ps1                    # phát hiện + bật WHPX (DISM), xử lý reboot-resume
├── winsw/
│   └── supplycore-service.xml        # định nghĩa Windows Service chạy launcher
└── launcher/
    ├── run-vm.ps1                    # dựng dòng lệnh QEMU (accel, disks, hostfwd) + chạy headless
    └── wait-healthy.ps1              # poll http://127.0.0.1:<PORT>/supplycore tới khi 200

guest/
├── packer/
│   └── supplycore.pkr.hcl           # build disk0.qcow2 từ Ubuntu cloud image
├── cloud-init/
│   ├── user-data                    # cloud-init: tạo user, copy units, kích hoạt first-boot
│   └── meta-data
├── first-boot.sh                    # idempotent: tạo site, set admin pw, bind volumes /data, migrate
├── first-boot.service              # systemd oneshot gọi first-boot.sh
├── backup.sh                        # bench backup --with-files → /data/backups
├── backup.service + backup.timer   # systemd timer hằng ngày
└── compose.override.yml            # map volumes MariaDB + sites vào /data (disk1)

tests/installer/
├── test_first_boot.bats            # idempotency + migrate-on-update của first-boot.sh
├── test_backup.bats                # backup.sh ghi đúng /data/backups
└── test_run_vm.Tests.ps1           # run-vm.ps1 dựng đúng dòng lệnh QEMU (Pester)

.github/workflows/
└── build-installer.yml             # build image → disk0 (Packer) → smoke → .exe (Windows) → release
```

---

## Task 1: compose.override.yml — bind volumes vào /data (persistence)

**Files:**
- Create: `guest/compose.override.yml`
- Test: thủ công trong CI smoke (Task 9); ở đây validate cú pháp

- [ ] **Step 1: Viết override map volumes ra /data**

```yaml
# guest/compose.override.yml
# Chồng lên deploy/compose.yml: ép dữ liệu bền nằm trên disk1 (/data), KHÔNG trên disk0.
services:
  db:
    volumes:
      - /data/mariadb:/var/lib/mysql
  backend:
    volumes:
      - /data/sites:/home/frappe/frappe-bench/sites
  # các service dùng chung sites (nginx, queue, scheduler) cũng map /data/sites
  websocket:
    volumes:
      - /data/sites:/home/frappe/frappe-bench/sites
  queue-short:
    volumes:
      - /data/sites:/home/frappe/frappe-bench/sites
  queue-long:
    volumes:
      - /data/sites:/home/frappe/frappe-bench/sites
  scheduler:
    volumes:
      - /data/sites:/home/frappe/frappe-bench/sites
  frontend:
    volumes:
      - /data/sites:/home/frappe/frappe-bench/sites
```

> Trước khi viết: mở `deploy/compose.yml` để lấy ĐÚNG tên service + đường dẫn mount `sites` thực tế, sửa danh sách trên cho khớp. Không đoán.

- [ ] **Step 2: Validate cú pháp YAML**

Run: `docker compose -f deploy/compose.yml -f guest/compose.override.yml config -q` (chạy ở môi trường có docker; nếu dev box không có, dùng `python -c "import yaml,sys; yaml.safe_load(open('guest/compose.override.yml'))"`)
Expected: không lỗi cú pháp.

- [ ] **Step 3: Commit**

```bash
git add guest/compose.override.yml
git commit -m "feat(installer): compose override ép dữ liệu bền vào /data (disk1)"
```

---

## Task 2: first-boot.sh — khởi tạo idempotent + migrate-on-update

**Files:**
- Create: `guest/first-boot.sh`
- Test: `tests/installer/test_first_boot.bats`

- [ ] **Step 1: Viết test thất bại (bats)**

```bash
# tests/installer/test_first_boot.bats
setup() {
  export TEST_DIR="$(mktemp -d)"
  export DATA_DIR="$TEST_DIR/data"
  mkdir -p "$DATA_DIR"
  # stub các lệnh ngoài để không cần docker thật
  export STUB_LOG="$TEST_DIR/calls.log"
  export PATH="$TEST_DIR/bin:$PATH"
  mkdir -p "$TEST_DIR/bin"
  for cmd in docker bench; do
    cat > "$TEST_DIR/bin/$cmd" <<EOF
#!/usr/bin/env bash
echo "$cmd \$*" >> "$STUB_LOG"
EOF
    chmod +x "$TEST_DIR/bin/$cmd"
  done
  export ADMIN_PASSWORD="secret123"
  export SITE_NAME="supplycore.local"
}
teardown() { rm -rf "$TEST_DIR"; }

@test "lần đầu: tạo site + cài app khi marker chưa tồn tại" {
  run bash guest/first-boot.sh
  [ "$status" -eq 0 ]
  grep -q "new-site" "$STUB_LOG"
  grep -q "install-app supplycore" "$STUB_LOG"
  [ -f "$DATA_DIR/.provisioned" ]
}

@test "lần sau: KHÔNG tạo lại site, chạy migrate" {
  touch "$DATA_DIR/.provisioned"
  run bash guest/first-boot.sh
  [ "$status" -eq 0 ]
  ! grep -q "new-site" "$STUB_LOG"
  grep -q "migrate" "$STUB_LOG"
}
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: `bats tests/installer/test_first_boot.bats`
Expected: FAIL — `guest/first-boot.sh` chưa tồn tại.

- [ ] **Step 3: Viết first-boot.sh tối thiểu cho test pass**

```bash
#!/usr/bin/env bash
# guest/first-boot.sh — idempotent provisioning chạy bởi systemd oneshot mỗi lần boot.
set -euo pipefail

DATA_DIR="${DATA_DIR:-/data}"
SITE_NAME="${SITE_NAME:-supplycore.local}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?ADMIN_PASSWORD bắt buộc}"
MARKER="$DATA_DIR/.provisioned"
COMPOSE_DIR="${COMPOSE_DIR:-/opt/supplycore}"

mkdir -p "$DATA_DIR/mariadb" "$DATA_DIR/sites" "$DATA_DIR/backups"

# Đưa stack lên (compose chính + override /data)
docker compose -f "$COMPOSE_DIR/compose.yml" -f "$COMPOSE_DIR/compose.override.yml" up -d

if [ ! -f "$MARKER" ]; then
  # Lần đầu: site trống + cài app (không seed) — theo spec docker-packaging
  bench new-site "$SITE_NAME" --admin-password "$ADMIN_PASSWORD" --no-mariadb-socket --force
  bench --site "$SITE_NAME" install-app supplycore
  bench use "$SITE_NAME"
  touch "$MARKER"
else
  # Lần sau (kể cả sau update disk0): chỉ migrate
  bench --site "$SITE_NAME" migrate
fi
```

> Lưu ý: trong VM thật, `bench` chạy qua `docker compose exec backend bench ...`. Giữ tên lệnh `bench`/`docker` ở mức cho test stub bắt được; khi tích hợp Task 8 thay bằng wrapper gọi `docker compose exec`. Ghi rõ wrapper trong Task 8.

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: `bats tests/installer/test_first_boot.bats`
Expected: PASS (2 test).

- [ ] **Step 5: Commit**

```bash
git add guest/first-boot.sh tests/installer/test_first_boot.bats
git commit -m "feat(installer): first-boot.sh idempotent (tạo site lần đầu, migrate khi update)"
```

---

## Task 3: backup.sh — sao lưu vào /data/backups

**Files:**
- Create: `guest/backup.sh`
- Test: `tests/installer/test_backup.bats`

- [ ] **Step 1: Viết test thất bại**

```bash
# tests/installer/test_backup.bats
setup() {
  export TEST_DIR="$(mktemp -d)"
  export DATA_DIR="$TEST_DIR/data"; mkdir -p "$DATA_DIR"
  export STUB_LOG="$TEST_DIR/calls.log"
  export PATH="$TEST_DIR/bin:$PATH"; mkdir -p "$TEST_DIR/bin"
  cat > "$TEST_DIR/bin/bench" <<EOF
#!/usr/bin/env bash
echo "bench \$*" >> "$STUB_LOG"
EOF
  chmod +x "$TEST_DIR/bin/bench"
  export SITE_NAME="supplycore.local"
}
teardown() { rm -rf "$TEST_DIR"; }

@test "gọi bench backup --with-files vào /data/backups" {
  run bash guest/backup.sh
  [ "$status" -eq 0 ]
  grep -q "backup --with-files" "$STUB_LOG"
  [ -d "$DATA_DIR/backups" ]
}
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: `bats tests/installer/test_backup.bats`
Expected: FAIL — file chưa có.

- [ ] **Step 3: Viết backup.sh**

```bash
#!/usr/bin/env bash
# guest/backup.sh — chạy bởi systemd timer; sao lưu site vào /data/backups (đĩa bền).
set -euo pipefail
DATA_DIR="${DATA_DIR:-/data}"
SITE_NAME="${SITE_NAME:-supplycore.local}"
mkdir -p "$DATA_DIR/backups"
bench --site "$SITE_NAME" backup --with-files --backup-path "$DATA_DIR/backups"
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: `bats tests/installer/test_backup.bats`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add guest/backup.sh tests/installer/test_backup.bats
git commit -m "feat(installer): backup.sh ghi bench backup vào /data/backups"
```

---

## Task 4: systemd units (first-boot oneshot + backup timer)

**Files:**
- Create: `guest/first-boot.service`, `guest/backup.service`, `guest/backup.timer`
- Test: validate bằng `systemd-analyze verify` (Task 9 trong CI); ở đây chỉ commit

- [ ] **Step 1: Viết first-boot.service**

```ini
# guest/first-boot.service
[Unit]
Description=SupplyCore first-boot provisioning
After=docker.service network-online.target
Requires=docker.service
[Service]
Type=oneshot
RemainAfterExit=yes
EnvironmentFile=/data/supplycore.env
ExecStart=/opt/supplycore/first-boot.sh
[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Viết backup.service + backup.timer**

```ini
# guest/backup.service
[Unit]
Description=SupplyCore daily backup
[Service]
Type=oneshot
EnvironmentFile=/data/supplycore.env
ExecStart=/opt/supplycore/backup.sh
```

```ini
# guest/backup.timer
[Unit]
Description=Chạy SupplyCore backup hằng ngày
[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
[Install]
WantedBy=timers.target
```

- [ ] **Step 3: Commit**

```bash
git add guest/first-boot.service guest/backup.service guest/backup.timer
git commit -m "feat(installer): systemd units cho first-boot + backup hằng ngày"
```

---

## Task 5: cloud-init — nhận admin password + site name từ host

**Files:**
- Create: `guest/cloud-init/user-data`, `guest/cloud-init/meta-data`

- [ ] **Step 1: Viết meta-data**

```yaml
# guest/cloud-init/meta-data
instance-id: supplycore-vm
local-hostname: supplycore
```

- [ ] **Step 2: Viết user-data (template — installer điền ADMIN_PASSWORD)**

```yaml
## guest/cloud-init/user-data
#cloud-config
write_files:
  - path: /data/supplycore.env
    permissions: '0600'
    content: |
      DATA_DIR=/data
      SITE_NAME=supplycore.local
      COMPOSE_DIR=/opt/supplycore
      ADMIN_PASSWORD=__ADMIN_PASSWORD__
runcmd:
  - mkdir -p /data
  - systemctl enable --now first-boot.service
  - systemctl enable --now backup.timer
```

> `__ADMIN_PASSWORD__` được installer (Task 11) thay bằng giá trị wizard, ghi vào cloud-init seed ISO (`cidata`). KHÔNG log plaintext.

- [ ] **Step 3: Commit**

```bash
git add guest/cloud-init/user-data guest/cloud-init/meta-data
git commit -m "feat(installer): cloud-init seed nhận admin password từ host"
```

---

## Task 6: run-vm.ps1 — dựng dòng lệnh QEMU (logic có test)

**Files:**
- Create: `installer/launcher/run-vm.ps1`
- Test: `tests/installer/test_run_vm.Tests.ps1`

- [ ] **Step 1: Viết test Pester thất bại**

```powershell
# tests/installer/test_run_vm.Tests.ps1
BeforeAll {
  . "$PSScriptRoot/../../installer/launcher/run-vm.ps1" -DryRun
}
Describe "Build-QemuArgs" {
  It "dùng accel whpx khi -Accel whpx" {
    $args = Build-QemuArgs -Accel 'whpx' -Disk0 'd0.qcow2' -Disk1 'd1.qcow2' -Port 80 -SeedIso 'seed.iso'
    ($args -join ' ') | Should -Match 'accel=whpx'
  }
  It "fallback tcg khi -Accel tcg" {
    $args = Build-QemuArgs -Accel 'tcg' -Disk0 'd0.qcow2' -Disk1 'd1.qcow2' -Port 80 -SeedIso 'seed.iso'
    ($args -join ' ') | Should -Match 'accel=tcg'
  }
  It "forward host port tới guest 80" {
    $args = Build-QemuArgs -Accel 'whpx' -Disk0 'd0.qcow2' -Disk1 'd1.qcow2' -Port 8080 -SeedIso 'seed.iso'
    ($args -join ' ') | Should -Match 'hostfwd=tcp:127.0.0.1:8080-:80'
  }
  It "gắn cả disk0 và disk1" {
    $args = Build-QemuArgs -Accel 'whpx' -Disk0 'd0.qcow2' -Disk1 'd1.qcow2' -Port 80 -SeedIso 'seed.iso'
    ($args -join ' ') | Should -Match 'd0.qcow2'
    ($args -join ' ') | Should -Match 'd1.qcow2'
  }
}
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: `pwsh -c "Invoke-Pester tests/installer/test_run_vm.Tests.ps1"`
Expected: FAIL — `run-vm.ps1` chưa có.

- [ ] **Step 3: Viết run-vm.ps1**

```powershell
# installer/launcher/run-vm.ps1
param(
  [string]$Accel = 'whpx',
  [string]$Disk0,
  [string]$Disk1,
  [int]$Port = 80,
  [string]$SeedIso,
  [string]$QemuExe = "$PSScriptRoot\qemu\qemu-system-x86_64.exe",
  [switch]$DryRun
)

function Build-QemuArgs {
  param($Accel, $Disk0, $Disk1, $Port, $SeedIso)
  return @(
    '-machine', "type=q35,accel=$Accel"
    '-cpu', 'max'
    '-smp', '2'
    '-m', '4096'
    '-drive', "file=$Disk0,if=virtio,format=qcow2"
    '-drive', "file=$Disk1,if=virtio,format=qcow2"
    '-drive', "file=$SeedIso,if=virtio,format=raw,readonly=on"
    '-netdev', "user,id=n0,hostfwd=tcp:127.0.0.1:$Port-:80"
    '-device', 'virtio-net-pci,netdev=n0'
    '-display', 'none'
    '-serial', 'file:supplycore-vm.log'
  )
}

if ($DryRun) { return }   # cho Pester dot-source mà không chạy QEMU

$qemuArgs = Build-QemuArgs -Accel $Accel -Disk0 $Disk0 -Disk1 $Disk1 -Port $Port -SeedIso $SeedIso
& $QemuExe @qemuArgs
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: `pwsh -c "Invoke-Pester tests/installer/test_run_vm.Tests.ps1"`
Expected: PASS (4 test).

- [ ] **Step 5: Commit**

```bash
git add installer/launcher/run-vm.ps1 tests/installer/test_run_vm.Tests.ps1
git commit -m "feat(installer): run-vm.ps1 dựng dòng lệnh QEMU (whpx/tcg, hostfwd, 2 đĩa)"
```

---

## Task 7: wait-healthy.ps1 — poll cho tới khi site phản hồi

**Files:**
- Create: `installer/launcher/wait-healthy.ps1`

- [ ] **Step 1: Viết wait-healthy.ps1**

```powershell
# installer/launcher/wait-healthy.ps1
param([int]$Port = 80, [int]$TimeoutSec = 600)
$deadline = (Get-Date).AddSeconds($TimeoutSec)
$url = "http://127.0.0.1:$Port/supplycore"
while ((Get-Date) -lt $deadline) {
  try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
    if ($r.StatusCode -eq 200) { Write-Host "SupplyCore sẵn sàng."; exit 0 }
  } catch { Start-Sleep -Seconds 5 }
}
Write-Error "Hết thời gian chờ SupplyCore khởi động."
exit 1
```

- [ ] **Step 2: Smoke kiểm tra cú pháp**

Run: `pwsh -NoProfile -Command "Get-Command -Syntax { . './installer/launcher/wait-healthy.ps1' }" ` (hoặc `pwsh -c "[scriptblock]::Create((Get-Content -Raw installer/launcher/wait-healthy.ps1))"`)
Expected: parse không lỗi.

- [ ] **Step 3: Commit**

```bash
git add installer/launcher/wait-healthy.ps1
git commit -m "feat(installer): wait-healthy.ps1 poll /supplycore tới khi HTTP 200"
```

---

## Task 8: backend wrapper — bench/docker qua compose exec

**Files:**
- Create: `guest/bin/bench`, `guest/bin/docker-compose-exec.sh`
- Modify: `guest/first-boot.sh`, `guest/backup.sh` (dùng wrapper)

- [ ] **Step 1: Viết wrapper bench**

```bash
#!/usr/bin/env bash
# guest/bin/bench — gọi bench thật trong container backend.
set -euo pipefail
COMPOSE_DIR="${COMPOSE_DIR:-/opt/supplycore}"
exec docker compose -f "$COMPOSE_DIR/compose.yml" -f "$COMPOSE_DIR/compose.override.yml" \
  exec -T backend bench "$@"
```

- [ ] **Step 2: Đảm bảo first-boot.sh/backup.sh tìm wrapper trước**

Sửa đầu `guest/first-boot.sh` và `guest/backup.sh`, thêm sau dòng `set -euo pipefail`:

```bash
export PATH="/opt/supplycore/bin:$PATH"
```

- [ ] **Step 3: Chạy lại bats — vẫn PASS (stub vẫn bắt 'bench ...')**

Run: `bats tests/installer/test_first_boot.bats tests/installer/test_backup.bats`
Expected: PASS — wrapper không phá test vì test set PATH bin stub riêng (đặt trước, ưu tiên hơn /opt).

> Kiểm tra: test set `PATH="$TEST_DIR/bin:$PATH"` SAU khi script export `/opt/supplycore/bin`. Vì script chạy trong subshell `run bash ...`, biến PATH của test được kế thừa và script prepend `/opt/...` lên trước → stub bị che. **Sửa:** trong cả 2 script, chỉ prepend nếu thư mục tồn tại: `[ -d /opt/supplycore/bin ] && export PATH="/opt/supplycore/bin:$PATH"`. Trong CI test, `/opt/supplycore/bin` không tồn tại → stub thắng.

- [ ] **Step 4: Áp sửa điều kiện và chạy lại test**

Run: `bats tests/installer/test_first_boot.bats tests/installer/test_backup.bats`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add guest/bin/bench guest/first-boot.sh guest/backup.sh
git commit -m "feat(installer): bench wrapper qua docker compose exec backend"
```

---

## Task 9: Packer build disk0 + smoke test (CI Linux)

**Files:**
- Create: `guest/packer/supplycore.pkr.hcl`, `guest/packer/install.sh`

- [ ] **Step 1: Viết install.sh (provisioner chạy trong VM build)**

```bash
#!/usr/bin/env bash
# guest/packer/install.sh — cài Docker Engine + nạp image + đặt file app vào disk0.
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu jammy stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable docker

mkdir -p /opt/supplycore /opt/supplycore/bin
# Các file dưới đây được Packer file-provisioner copy vào /tmp trước:
cp /tmp/compose.yml /tmp/compose.override.yml /opt/supplycore/
cp /tmp/first-boot.sh /tmp/backup.sh /opt/supplycore/
cp /tmp/bench /opt/supplycore/bin/bench
chmod +x /opt/supplycore/*.sh /opt/supplycore/bin/bench
cp /tmp/first-boot.service /tmp/backup.service /tmp/backup.timer /etc/systemd/system/
systemctl enable first-boot.service backup.timer

# Nạp image SupplyCore đã build (Packer copy supplycore-image.tar vào /tmp)
docker load -i /tmp/supplycore-image.tar
# Pre-pull các base image của compose để chạy offline
docker compose -f /opt/supplycore/compose.yml -f /opt/supplycore/compose.override.yml pull || true

# Trim để nén nhỏ
apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/*
fstrim -av || true
```

- [ ] **Step 2: Viết supplycore.pkr.hcl**

```hcl
# guest/packer/supplycore.pkr.hcl
packer {
  required_plugins {
    qemu = { source = "github.com/hashicorp/qemu", version = "~> 1.1" }
  }
}
variable "ubuntu_image_url" {
  default = "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
}
variable "ubuntu_image_sha256" { default = "" }  # PIN trước khi build, không để rỗng ở CI
source "qemu" "supplycore" {
  iso_url           = var.ubuntu_image_url
  iso_checksum      = "sha256:${var.ubuntu_image_sha256}"
  disk_image        = true
  disk_size         = "20000M"
  format            = "qcow2"
  accelerator       = "kvm"
  ssh_username      = "ubuntu"
  ssh_password      = "ubuntu"
  ssh_timeout       = "20m"
  headless          = true
  output_directory  = "output-disk0"
  vm_name           = "disk0.qcow2"
  cd_files          = ["guest/cloud-init/user-data", "guest/cloud-init/meta-data"]
  cd_label          = "cidata"
  shutdown_command  = "sudo shutdown -P now"
}
build {
  sources = ["source.qemu.supplycore"]
  provisioner "file" {
    sources     = [
      "deploy/compose.yml", "guest/compose.override.yml",
      "guest/first-boot.sh", "guest/backup.sh", "guest/bin/bench",
      "guest/first-boot.service", "guest/backup.service", "guest/backup.timer",
      "supplycore-image.tar"
    ]
    destination = "/tmp/"
  }
  provisioner "shell" {
    execute_command = "sudo -E bash '{{.Path}}'"
    script          = "guest/packer/install.sh"
  }
}
```

> `ubuntu_image_sha256` PHẢI pin (lấy từ `SHA256SUMS` của bản jammy đang dùng). CI fail nếu rỗng.

- [ ] **Step 3: Viết job smoke trong CI (sẽ hoàn thiện ở Task 10) — kiểm thử disk0**

Smoke (chạy trong build-installer.yml, runner Linux+KVM, SAU Packer):
```bash
# boot disk0 + disk1 trống, đợi healthy, assert
qemu-img create -f qcow2 disk1.qcow2 30G
qemu-system-x86_64 -machine accel=kvm -m 4096 -smp 2 \
  -drive file=output-disk0/disk0.qcow2,if=virtio,format=qcow2 \
  -drive file=disk1.qcow2,if=virtio,format=qcow2 \
  -drive file=seed.iso,if=virtio,format=raw,readonly=on \
  -netdev user,id=n0,hostfwd=tcp:127.0.0.1:8080-:80 -device virtio-net-pci,netdev=n0 \
  -display none -daemonize -pidfile vm.pid
# poll
for i in $(seq 1 120); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/supplycore || true)
  [ "$code" = "200" ] && break; sleep 10
done
[ "$code" = "200" ] || { echo "smoke FAIL"; exit 1; }
curl -fs http://127.0.0.1:8080/ >/dev/null
```

- [ ] **Step 4: Commit**

```bash
git add guest/packer/supplycore.pkr.hcl guest/packer/install.sh
git commit -m "feat(installer): Packer build disk0 (Ubuntu+Docker+image) + provisioner"
```

---

## Task 10: WinSW service + whpx-check.ps1

**Files:**
- Create: `installer/winsw/supplycore-service.xml`, `installer/whpx-check.ps1`

- [ ] **Step 1: Viết service XML**

```xml
<!-- installer/winsw/supplycore-service.xml -->
<service>
  <id>SupplyCore</id>
  <name>SupplyCore</name>
  <description>SupplyCore (Frappe) chạy trong VM ẩn qua QEMU.</description>
  <executable>powershell.exe</executable>
  <arguments>-NoProfile -ExecutionPolicy Bypass -File "%BASE%\launcher\run-vm.ps1" -Accel "%SC_ACCEL%" -Disk0 "%BASE%\disk0.qcow2" -Disk1 "%SC_DATA%\disk1.qcow2" -Port %SC_PORT% -SeedIso "%SC_DATA%\seed.iso"</arguments>
  <onfailure action="restart" delay="10 sec"/>
  <log mode="roll-by-size"><sizeThreshold>10240</sizeThreshold><keepFiles>5</keepFiles></log>
  <startmode>Automatic</startmode>
</service>
```

- [ ] **Step 2: Viết whpx-check.ps1**

```powershell
# installer/whpx-check.ps1
# Trả exit 0 nếu WHPX sẵn sàng; bật nếu thiếu (cần admin); exit 2 nếu cần reboot.
$feature = Get-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -ErrorAction SilentlyContinue
if ($null -eq $feature) { Write-Warning "Không có WHPX trên máy này — sẽ fallback TCG (chậm)."; exit 3 }
if ($feature.State -eq 'Enabled') { Write-Host "WHPX đã bật."; exit 0 }
Write-Host "Đang bật Windows Hypervisor Platform..."
$r = Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -NoRestart
if ($r.RestartNeeded) { Write-Host "Cần khởi động lại để hoàn tất WHPX."; exit 2 }
exit 0
```

- [ ] **Step 3: Smoke parse cả hai**

Run: `pwsh -c "[scriptblock]::Create((Get-Content -Raw installer/whpx-check.ps1)); [xml](Get-Content installer/winsw/supplycore-service.xml)"`
Expected: parse không lỗi (PS script + XML hợp lệ).

- [ ] **Step 4: Commit**

```bash
git add installer/winsw/supplycore-service.xml installer/whpx-check.ps1
git commit -m "feat(installer): WinSW service + whpx-check (bật WHPX, xử lý reboot/fallback)"
```

---

## Task 11: Inno Setup script (supplycore.iss)

**Files:**
- Create: `installer/supplycore.iss`

- [ ] **Step 1: Viết supplycore.iss**

```pascal
; installer/supplycore.iss
#define AppName "SupplyCore"
#define AppVersion GetEnv("SC_VERSION")

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={commonpf}\SupplyCore
PrivilegesRequired=admin
OutputBaseFilename=SupplyCore-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\qemu\*";            DestDir: "{app}\launcher\qemu"; Flags: recursesubdirs
Source: "installer\launcher\*";   DestDir: "{app}\launcher";      Flags: recursesubdirs
Source: "dist\WinSW.exe";         DestDir: "{app}";               DestName: "SupplyCore-service.exe"
Source: "installer\winsw\supplycore-service.xml"; DestDir: "{app}"; DestName: "SupplyCore-service.xml"
Source: "dist\disk0.qcow2";       DestDir: "{app}"
Source: "installer\whpx-check.ps1"; DestDir: "{app}"

[Code]
var AdminPwPage: TInputQueryWizardPage; PortPage: TInputQueryWizardPage;
procedure InitializeWizard;
begin
  AdminPwPage := CreateInputQueryPage(wpSelectDir, 'Mật khẩu Administrator',
    'Đặt mật khẩu cho tài khoản Administrator của SupplyCore', '');
  AdminPwPage.Add('Mật khẩu:', True);
  PortPage := CreateInputQueryPage(AdminPwPage.ID, 'Cổng truy cập',
    'Cổng localhost để mở SupplyCore (mặc định 80)', '');
  PortPage.Add('Cổng:', False);
  PortPage.Values[0] := '80';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = AdminPwPage.ID) and (AdminPwPage.Values[0] = '') then
  begin MsgBox('Vui lòng nhập mật khẩu Administrator.', mbError, MB_OK); Result := False; end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var rc: Integer; dataDir, port, pw: String;
begin
  if CurStep = ssPostInstall then
  begin
    dataDir := ExpandConstant('{commonappdata}\SupplyCore');
    port := PortPage.Values[0];
    pw := AdminPwPage.Values[0];
    ForceDirectories(dataDir);
    // 1) WHPX
    Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\whpx-check.ps1') + '"',
      '', SW_HIDE, ewWaitUntilTerminated, rc);
    // rc=2: cần reboot -> đăng ký RunOnce tiếp tục (chi tiết: tạo task tiếp tục cài). rc=3: fallback tcg.
    // 2) tạo disk1 nếu thiếu + seed.iso chứa admin pw
    Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\launcher\make-data.ps1') +
      '" -DataDir "' + dataDir + '" -AdminPassword "' + pw + '"', '', SW_HIDE, ewWaitUntilTerminated, rc);
    // 3) đăng ký + chạy service
    Exec(ExpandConstant('{app}\SupplyCore-service.exe'), 'install', '', SW_HIDE, ewWaitUntilTerminated, rc);
    Exec(ExpandConstant('{app}\SupplyCore-service.exe'), 'start', '', SW_HIDE, ewWaitUntilTerminated, rc);
    // 4) chờ healthy + mở browser
    Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\launcher\wait-healthy.ps1') +
      '" -Port ' + port, '', SW_NORMAL, ewWaitUntilTerminated, rc);
    if rc = 0 then ShellExec('open', 'http://127.0.0.1:' + port, '', '', SW_SHOW, ewNoWait, rc);
  end;
end;

[UninstallRun]
Filename: "{app}\SupplyCore-service.exe"; Parameters: "stop";      Flags: runhidden; RunOnceId: "stopsvc"
Filename: "{app}\SupplyCore-service.exe"; Parameters: "uninstall"; Flags: runhidden; RunOnceId: "rmsvc"
; LƯU Ý: KHÔNG xoá {commonappdata}\SupplyCore (disk1) khi gỡ cài — giữ dữ liệu.
```

- [ ] **Step 2: Viết make-data.ps1 (tạo disk1 + seed.iso)**

```powershell
# installer/launcher/make-data.ps1
param([string]$DataDir, [string]$AdminPassword, [string]$SiteName = 'supplycore.local')
$qemuImg = "$PSScriptRoot\qemu\qemu-img.exe"
$disk1 = Join-Path $DataDir 'disk1.qcow2'
if (-not (Test-Path $disk1)) { & $qemuImg create -f qcow2 $disk1 30G }
# render user-data từ template (thay __ADMIN_PASSWORD__) rồi gói cidata ISO
$tpl = Get-Content "$PSScriptRoot\cloud-init\user-data" -Raw
$tpl = $tpl -replace '__ADMIN_PASSWORD__', $AdminPassword
$tmp = Join-Path $env:TEMP 'sc-cidata'; New-Item -ItemType Directory -Force $tmp | Out-Null
Set-Content "$tmp\user-data" $tpl -NoNewline
Copy-Item "$PSScriptRoot\cloud-init\meta-data" "$tmp\meta-data"
# tạo ISO nhãn cidata (oscdimg đi kèm, hoặc genisoimage trong build)
& "$PSScriptRoot\oscdimg.exe" -lcidata -j2 $tmp (Join-Path $DataDir 'seed.iso')
```

> Installer Task 12 phải copy `cloud-init/` và `oscdimg.exe` (Windows ADK redistributable, hoặc thay bằng tool tạo ISO khác đã pin) vào `{app}\launcher`.

- [ ] **Step 3: Smoke kiểm tra ISCC parse (trên runner Windows / máy có Inno Setup)**

Run: `iscc /O- installer\supplycore.iss` (cần các file dist; ở giai đoạn dev có thể `iscc /DSkipFiles` — nhưng tối thiểu xác nhận `[Code]` compile)
Expected: compile `[Code]` không lỗi cú pháp Pascal.

- [ ] **Step 4: Commit**

```bash
git add installer/supplycore.iss installer/launcher/make-data.ps1
git commit -m "feat(installer): Inno Setup script (wizard admin pw, WHPX, disk1, service, browser)"
```

---

## Task 12: CI workflow build-installer.yml

**Files:**
- Create: `.github/workflows/build-installer.yml`

- [ ] **Step 1: Viết workflow**

```yaml
# .github/workflows/build-installer.yml
name: build-installer
on:
  push: { tags: ['v*'] }
  workflow_dispatch:
jobs:
  guest:
    runs-on: ubuntu-latest   # KVM khả dụng trên larger runner; nếu không, dùng self-hosted/nested
    steps:
      - uses: actions/checkout@v4
      - name: Build image SupplyCore
        run: |
          # reuse pipeline GHCR: build image rồi save ra tar
          docker build ... -t supplycore:ci    # lấy lệnh đúng từ build-image.yml hiện có
          docker save supplycore:ci -o supplycore-image.tar
      - name: Cài Packer + QEMU
        run: |
          sudo apt-get update && sudo apt-get install -y qemu-system-x86 qemu-utils ovmf
          curl -fsSL https://releases.hashicorp.com/packer/1.11.2/packer_1.11.2_linux_amd64.zip -o packer.zip
          unzip packer.zip && sudo mv packer /usr/local/bin/
      - name: Packer build disk0
        run: packer init guest/packer/ && packer build -var ubuntu_image_sha256=$UBUNTU_SHA guest/packer/supplycore.pkr.hcl
        env: { UBUNTU_SHA: '<<PIN>>' }
      - name: Smoke test disk0
        run: bash guest/packer/smoke.sh   # script ở Task 9 Step 3, tách ra file
      - uses: actions/upload-artifact@v4
        with: { name: disk0, path: output-disk0/disk0.qcow2 }
  installer:
    needs: guest
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { name: disk0, path: dist }
      - name: Tải QEMU win64 + WinSW (pinned + checksum)
        shell: pwsh
        run: |
          # QEMU: https://qemu.weilnetz.de/w64/  — PIN bản + verify SHA256
          # WinSW v2.12.0: https://github.com/winsw/winsw/releases — verify SHA256
          ./installer/ci/fetch-deps.ps1   # script tải + verify (tạo ở step riêng)
      - name: Pester tests
        shell: pwsh
        run: Invoke-Pester tests/installer/ -CI
      - name: Compile Inno Setup
        shell: pwsh
        run: |
          choco install innosetup -y
          & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DSC_VERSION=${{ github.ref_name }} installer/supplycore.iss
        env: { SC_VERSION: ${{ github.ref_name }} }
      - name: Test cài im lặng + gỡ
        shell: pwsh
        run: ./installer/ci/test-install.ps1   # cài /SILENT, chờ service, curl localhost, gỡ
      - name: Checksum + Release
        shell: pwsh
        run: |
          Get-FileHash Output\SupplyCore-Setup-*.exe -Algorithm SHA256 | Out-File Output\SHA256.txt
      - uses: softprops/action-gh-release@v2
        with: { files: "Output/SupplyCore-Setup-*.exe\nOutput/SHA256.txt" }
```

> Các chỗ `<<PIN>>`, `...`, `fetch-deps.ps1`, `test-install.ps1`, `smoke.sh` là file/giá trị phải điền ở task con khi thực thi — KHÔNG để rỗng khi merge. Lấy lệnh build image đúng từ `.github/workflows/build-image.yml` của branch `feat/docker-packaging`.

- [ ] **Step 2: Validate YAML**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/build-installer.yml'))"`
Expected: parse OK.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/build-installer.yml
git commit -m "feat(installer): CI build disk0 (Packer) -> đóng .exe (Inno Setup) -> release"
```

---

## Task 13: CI helper scripts (fetch-deps, smoke, test-install)

**Files:**
- Create: `installer/ci/fetch-deps.ps1`, `guest/packer/smoke.sh`, `installer/ci/test-install.ps1`

- [ ] **Step 1: fetch-deps.ps1 (tải + verify QEMU/WinSW/oscdimg, pinned)**

```powershell
# installer/ci/fetch-deps.ps1 — tải dependencies pinned + verify SHA256, bung vào dist/
$ErrorActionPreference = 'Stop'
$deps = @(
  @{ Url='https://qemu.weilnetz.de/w64/qemu-w64-setup-<<PIN>>.exe'; Sha256='<<PIN>>'; Out='dist\qemu-setup.exe' },
  @{ Url='https://github.com/winsw/winsw/releases/download/v2.12.0/WinSW-x64.exe'; Sha256='<<PIN>>'; Out='dist\WinSW.exe' }
)
foreach ($d in $deps) {
  Invoke-WebRequest $d.Url -OutFile $d.Out
  $h = (Get-FileHash $d.Out -Algorithm SHA256).Hash
  if ($h -ne $d.Sha256) { throw "Checksum sai cho $($d.Out): $h" }
}
# bung QEMU portable vào dist\qemu (qemu-w64-setup hỗ trợ /S /D=...)
& dist\qemu-setup.exe /S /D=$PWD\dist\qemu
```

> `<<PIN>>` phải điền version + SHA256 thật khi thực thi task này. Nếu URL weilnetz đổi, thay bằng mirror đã pin.

- [ ] **Step 2: smoke.sh** — chuyển khối smoke ở Task 9 Step 3 thành file `guest/packer/smoke.sh` (giữ nguyên nội dung, thêm `set -euxo pipefail` + tạo `seed.iso` bằng `genisoimage -V cidata -o seed.iso -J -r guest/cloud-init/`).

- [ ] **Step 3: test-install.ps1**

```powershell
# installer/ci/test-install.ps1 — cài im lặng, kiểm tra service + localhost, rồi gỡ.
$ErrorActionPreference = 'Stop'
$exe = (Get-ChildItem Output\SupplyCore-Setup-*.exe)[0].FullName
Start-Process $exe -ArgumentList '/SILENT','/SUPPRESSMSGBOXES' -Wait
$svc = Get-Service SupplyCore -ErrorAction Stop
if ($svc.Status -ne 'Running') { throw "Service không chạy" }
# CI Windows runner không có WHPX → launcher fallback tcg (chậm); cho timeout dài
$ok = $false
1..60 | ForEach-Object {
  try { if ((Invoke-WebRequest http://127.0.0.1:80/supplycore -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200) { $script:ok=$true; break } } catch { Start-Sleep 10 }
}
if (-not $ok) { throw "localhost không phản hồi 200" }
Start-Process "$env:ProgramFiles\SupplyCore\unins000.exe" -ArgumentList '/SILENT' -Wait
```

> Nếu nested-virt/TCG quá chậm trên `windows-latest`, đánh dấu test-install là `continue-on-error` + ghi log rõ ("smoke đầy đủ chỉ chạy trên runner có WHPX") — KHÔNG bỏ qua âm thầm (theo spec: no silent caps).

- [ ] **Step 4: Commit**

```bash
git add installer/ci/fetch-deps.ps1 guest/packer/smoke.sh installer/ci/test-install.ps1
git commit -m "feat(installer): CI helpers (fetch-deps pinned, smoke, test-install)"
```

---

## Task 14: README cho IT bệnh viện

**Files:**
- Create: `installer/README.md`

- [ ] **Step 1: Viết README**

Nội dung tối thiểu: yêu cầu phần cứng (CPU hỗ trợ ảo hóa, RAM ≥8GB, đĩa ≥40GB), cách chạy `.exe`, ý nghĩa bước WHPX + reboot, truy cập `http://localhost`, đăng nhập Administrator, **quy trình backup** (file ở `C:\ProgramData\SupplyCore\... /data/backups`, cách copy ra ngoài), **quy trình restore** (`bench restore` trong VM, các lệnh cụ thể), **cách update** (chạy `.exe` mới — dữ liệu giữ nguyên), gỡ cài (dữ liệu KHÔNG bị xoá), xử lý sự cố (xem `supplycore-vm.log`, service không chạy).

- [ ] **Step 2: Commit**

```bash
git add installer/README.md
git commit -m "docs(installer): README cài đặt/backup/restore/update cho IT bệnh viện"
```

---

## Self-Review checklist (đã rà)

- **Spec coverage:** Persistence (Task 1,8,9) ✓ · update offline re-runnable (Task 2 migrate + Task 11 giữ disk1) ✓ · backup/restore (Task 3,4,14) ✓ · admin provisioning (Task 5,11) ✓ · WHPX A1 + fallback (Task 6,10) ✓ · 1 file .exe (Task 11,12) ✓ · build pipeline (Task 9,12,13) ✓ · testing (Task 2,3,6,9,12,13) ✓.
- **Type/tên nhất quán:** `Build-QemuArgs`, `/data/supplycore.env`, `SITE_NAME=supplycore.local`, `disk0.qcow2`/`disk1.qcow2`/`seed.iso`, `/opt/supplycore` đồng nhất xuyên các task.
- **Placeholder còn lại là CỐ Ý:** các `<<PIN>>` (version+SHA256), lệnh build image lấy từ `build-image.yml`, đều được đánh dấu "phải điền khi thực thi" — không phải mô tả mơ hồ về logic.
- **Phụ thuộc môi trường:** dev box Linux không Docker → Task có TDD thật (1,2,3,6,7) chạy được bằng bats/Pester/stub; các task config (.iss, .pkr.hcl, service xml, workflow) verify bằng parse/compile + smoke trong CI.
