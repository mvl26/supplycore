# installer/ci/fetch-deps.ps1
# ---------------------------------------------------------------------------
# Tải các build-dependency PINNED của installer, verify SHA256, đặt vào dist\
# theo đúng forward-dependency contract mà installer/supplycore.iss [Files] cần
# tại thời điểm ISCC compile (relative repo root):
#
#   dist\qemu\qemu-system-x86_64.exe   (run-vm.ps1   -> {app}\launcher\qemu\...)
#   dist\qemu\qemu-img.exe             (make-data.ps1 -> {app}\launcher\qemu\...)
#   dist\WinSW.exe                     (-> {app}\SupplyCore-service.exe)
#
# (make-data.ps1 tạo cidata ISO bằng IMAPI2FS — COM Windows sẵn có, KHÔNG cần
#  oscdimg/ADK, nên không có build-dep ISO nào ở đây.)
#
# (dist\disk0.qcow2 KHÔNG phải việc của script này — do Packer Task 9 / CI Task 12.)
#
# Nguyên tắc (spec "no silent caps"): mọi dependency tải từ URL PINNED + verify
# SHA256 PINNED, mismatch -> THROW. KHÔNG bao giờ bỏ qua verify (build phải
# offline-reproducible). Nếu một giá trị PIN còn là placeholder <<...>> thì
# script FAIL NGAY (fail-loud) trước khi chạm mạng — half-pinned không được pass.
#
# Chạy trên Windows CI runner (pwsh). KHÔNG chạy được trên dev box Linux.
# ---------------------------------------------------------------------------
$ErrorActionPreference = 'Stop'

# Repo root = hai cấp trên thư mục script (installer\ci\ -> repo root).
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$DistDir  = Join-Path $RepoRoot 'dist'
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

# ---------------------------------------------------------------------------
# Bảng dependency PINNED.
#
# CÁC PLACEHOLDER Task 12 / release-eng PHẢI ĐIỀN trước khi build thật:
#   - QEMU:  <<PIN-QEMU-VERSION>> trong Url  +  <<PIN-QEMU-SHA256>>
#   - WinSW: <<PIN-WINSW-SHA256>>            (Url đã pin sẵn v2.12.0)
#
# (Không còn build-dep ISO: cidata ISO do make-data.ps1 tạo bằng IMAPI2FS — COM
#  Windows sẵn có — nên KHÔNG cần oscdimg/ADK/mkisofs pinned ở đây.)
# ---------------------------------------------------------------------------
$deps = @(
  [pscustomobject]@{
    Name   = 'QEMU for Windows (w64, NSIS installer)'
    Url    = 'https://qemu.weilnetz.de/w64/qemu-w64-setup-<<PIN-QEMU-VERSION>>.exe'
    Sha256 = '<<PIN-QEMU-SHA256>>'
    Out    = (Join-Path $DistDir 'qemu-setup.exe')
    Kind   = 'qemu'
  }
  [pscustomobject]@{
    Name   = 'WinSW v2.12.0 (x64)'
    Url    = 'https://github.com/winsw/winsw/releases/download/v2.12.0/WinSW-x64.exe'
    Sha256 = '<<PIN-WINSW-SHA256>>'
    Out    = (Join-Path $DistDir 'WinSW.exe')
    Kind   = 'file'
  }
)

# --- Fail-loud placeholder guard (TRƯỚC mọi I/O mạng) ---------------------
# Nếu URL hoặc SHA256 còn chứa placeholder <<...>>, dừng ngay và liệt kê đủ để
# release-eng biết phải điền gì. Half-pinned script KHÔNG được chạy tiếp.
$unpinned = @()
foreach ($d in $deps) {
  if ($d.Url    -like '*<<*>>*') { $unpinned += "  - $($d.Name): URL chưa pin    -> $($d.Url)" }
  if ($d.Sha256 -like '*<<*>>*') { $unpinned += "  - $($d.Name): SHA256 chưa pin -> $($d.Sha256)" }
}
if ($unpinned.Count -gt 0) {
  throw ("fetch-deps: còn placeholder chưa điền (half-pinned, không an toàn). " +
         "Release-eng phải pin các giá trị sau:`n" + ($unpinned -join "`n"))
}

# --- Helper: tải + verify SHA256 (mismatch -> throw) ----------------------
function Get-Verified {
  param(
    [Parameter(Mandatory)][string]$Name,
    [Parameter(Mandatory)][string]$Url,
    [Parameter(Mandatory)][string]$Sha256,
    [Parameter(Mandatory)][string]$Out
  )
  Write-Host "Đang tải $Name"
  Write-Host "  từ: $Url"
  Invoke-WebRequest -Uri $Url -OutFile $Out -UseBasicParsing
  $actual = (Get-FileHash -Path $Out -Algorithm SHA256).Hash
  # -ne là case-insensitive trong PowerShell: Get-FileHash trả HOA, pin có thể
  # thường — vẫn so đúng. KHÔNG đổi sang -cne.
  if ($actual -ne $Sha256) {
    throw "fetch-deps: SHA256 KHÔNG khớp cho $Name ($Out)`n  mong đợi: $Sha256`n  thực tế: $actual"
  }
  Write-Host "  OK SHA256 đã verify: $actual"
}

# --- Tải + verify tất cả --------------------------------------------------
foreach ($d in $deps) {
  Get-Verified -Name $d.Name -Url $d.Url -Sha256 $d.Sha256 -Out $d.Out
}

# --- QEMU: bung portable vào dist\qemu qua silent NSIS install ------------
# qemu-w64-setup là NSIS: /S = silent, /D = thư mục đích. NSIS yêu cầu /D PHẢI
# là tham số CUỐI, đường dẫn TUYỆT ĐỐI, và KHÔNG đặt trong dấu nháy (kể cả khi
# có space). Vì vậy truyền nguyên một chuỗi ArgumentList, không tách mảng.
$qemuSetup = Join-Path $DistDir 'qemu-setup.exe'
$qemuDir   = Join-Path $DistDir 'qemu'
if (Test-Path -LiteralPath $qemuDir) { Remove-Item -LiteralPath $qemuDir -Recurse -Force }
Write-Host "Bung QEMU portable vào: $qemuDir"
$p = Start-Process -FilePath $qemuSetup -ArgumentList "/S /D=$qemuDir" -Wait -PassThru -NoNewWindow
if ($p.ExitCode -ne 0) {
  throw "fetch-deps: QEMU silent install thất bại (exit $($p.ExitCode))."
}

# --- ASSERT layout (guard chống layout drift của bộ cài QEMU) -------------
# Contract: cả hai exe phải nằm Ở ĐỈNH dist\qemu (không trong subfolder), nếu
# không run-vm.ps1 và make-data.ps1 đều gãy.
$mustExist = @(
  (Join-Path $qemuDir 'qemu-system-x86_64.exe'),
  (Join-Path $qemuDir 'qemu-img.exe')
)
foreach ($f in $mustExist) {
  if (-not (Test-Path -LiteralPath $f)) {
    throw ("fetch-deps: thiếu $f sau khi bung QEMU. Bộ cài có thể đã đổi layout " +
           "(exe nằm trong subfolder). Contract yêu cầu cả hai exe Ở ĐỈNH dist\qemu.")
  }
  Write-Host "  OK $f"
}

# --- Dọn installer trung gian (không cần đóng gói) ------------------------
Remove-Item -LiteralPath $qemuSetup -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "fetch-deps HOÀN TẤT. dist\ đã sẵn sàng cho ISCC:"
Write-Host "  dist\qemu\qemu-system-x86_64.exe"
Write-Host "  dist\qemu\qemu-img.exe"
Write-Host "  dist\WinSW.exe"
Write-Host "  (dist\disk0.qcow2 do Packer/CI cung cấp riêng — không thuộc script này.)"
