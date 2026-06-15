# installer/ci/test-install.ps1
# ---------------------------------------------------------------------------
# Smoke-test bộ cài đã build: cài im lặng -> assert service Running -> poll
# localhost health -> gỡ cài im lặng -> assert service biến mất.
#
# Chạy trên Windows CI runner (pwsh) SAU bước compile Inno Setup (Task 12).
# KHÔNG chạy được trên dev box Linux.
#
# Exit code TRUNG THỰC (spec "no silent caps"):
#   0  = cài + service Running + health 200 + gỡ sạch  -> smoke đầy đủ PASS.
#   !0 = bất kỳ bước nào fail, KỂ CẢ health không verify được trong timeout.
# Nếu runner thiếu WHPX/nested-virt thì QEMU fallback TCG (rất chậm) và health
# có thể không kịp 200 -> script này VẪN exit non-zero + log LỚN giải thích.
# KHÔNG tự "xanh". Task 12 tự quyết định có đánh continue-on-error hay không.
# ---------------------------------------------------------------------------
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

# --- 1) Tìm bộ cài đã build ------------------------------------------------
# Inno OutputDir mặc định nằm cạnh file .iss (installer\Output\), KHÔNG phải
# CWD. Tìm đệ quy từ repo root để không phụ thuộc OutputDir cụ thể; lấy bản mới
# nhất theo thời gian ghi.
$setup = Get-ChildItem -Path $RepoRoot -Recurse -Filter 'SupplyCore-Setup-*.exe' -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime | Select-Object -Last 1
if (-not $setup) {
  throw "test-install: không tìm thấy SupplyCore-Setup-*.exe dưới $RepoRoot (compile Inno Setup trước?)."
}
Write-Host "Bộ cài: $($setup.FullName)"

# --- 2) Cài im lặng + assert exit code của chính bộ cài --------------------
# /VERYSILENT bỏ cả progress; /SUPPRESSMSGBOXES để không treo chờ dialog;
# /NORESTART để CI tự kiểm soát reboot (WHPX-check có thể yêu cầu).
Write-Host "Cài im lặng..."
$inst = Start-Process -FilePath $setup.FullName `
  -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' `
  -Wait -PassThru
if ($inst.ExitCode -ne 0) {
  throw "test-install: bộ cài exit $($inst.ExitCode) (cài thất bại)."
}
Write-Host "  Cài xong (exit 0)."

# --- 3) Assert service SupplyCore tồn tại + đạt Running --------------------
# Đăng ký service có thể mất chút thời gian sau post-install; poll ngắn.
Write-Host "Chờ service 'SupplyCore' đạt Running..."
$svc = $null
foreach ($i in 1..30) {
  $svc = Get-Service -Name 'SupplyCore' -ErrorAction SilentlyContinue
  if ($svc -and $svc.Status -eq 'Running') { break }
  Start-Sleep -Seconds 2
}
if (-not $svc) { throw "test-install: service 'SupplyCore' không tồn tại sau khi cài." }
if ($svc.Status -ne 'Running') {
  throw "test-install: service 'SupplyCore' trạng thái '$($svc.Status)', không phải Running."
}
Write-Host "  Service Running."

# --- 4) Poll localhost health ----------------------------------------------
# WHPX-less runner -> TCG (chậm) -> để timeout DÀI. Không 200 => KHÔNG fail
# ngay (vẫn dọn dẹp), nhưng đánh dấu để exit non-zero ở cuối.
$port    = 80
$url     = "http://127.0.0.1:$port/supplycore"
$attempts = 90                     # 90 x 10s = ~15 phút (TCG cold boot)
$healthVerified = $false
Write-Host "Poll health: $url (tối đa ~$([math]::Round($attempts*10/60)) phút; TCG có thể chậm)..."
foreach ($i in 1..$attempts) {
  try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
    if ($r.StatusCode -eq 200) { $healthVerified = $true; break }
  } catch {
    Start-Sleep -Seconds 10
  }
}
if ($healthVerified) {
  Write-Host "  Health OK (HTTP 200)."
} else {
  Write-Warning "test-install: localhost KHÔNG trả 200 trong timeout."
  Write-Warning "Smoke ĐẦY ĐỦ cần runner có WHPX/nested-virt; localhost health KHÔNG được verify ở đây."
  Write-Warning "Script sẽ exit NON-ZERO (không tự 'xanh'). Task 12 quyết định continue-on-error."
}

# --- 5) Gỡ cài im lặng (luôn chạy để dọn, kể cả khi health fail) ----------
# DefaultDirName = {commonpf}\SupplyCore -> uninstaller ở $env:ProgramFiles.
$uninst = Join-Path $env:ProgramFiles 'SupplyCore\unins000.exe'
if (-not (Test-Path -LiteralPath $uninst)) {
  throw "test-install: không tìm thấy uninstaller $uninst."
}
Write-Host "Gỡ cài im lặng..."
Start-Process -FilePath $uninst -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait | Out-Null

# --- 6) Assert service biến mất --------------------------------------------
# Uninstaller của Inno chạy BẤT ĐỒNG BỘ (tự copy ra temp rồi return trước khi
# gỡ xong) — Start-Process -Wait KHÔNG thực sự chờ. Poll tới khi service null.
Write-Host "Chờ service 'SupplyCore' biến mất..."
$gone = $false
foreach ($i in 1..30) {
  if ($null -eq (Get-Service -Name 'SupplyCore' -ErrorAction SilentlyContinue)) { $gone = $true; break }
  Start-Sleep -Seconds 2
}
if (-not $gone) { throw "test-install: service 'SupplyCore' vẫn còn sau khi gỡ cài." }
Write-Host "  Service đã gỡ."

# --- 7) Exit trung thực ----------------------------------------------------
if (-not $healthVerified) {
  # Dùng Write-Warning (không Write-Error) để KHÔNG bị $ErrorActionPreference=Stop
  # biến thành terminating preempt mất dòng `exit 1` tường minh bên dưới.
  Write-Warning "test-install: cài/gỡ OK nhưng HEALTH chưa verify (xem cảnh báo WHPX ở trên)."
  exit 1
}
Write-Host ""
Write-Host "test-install HOÀN TẤT: cài + service Running + health 200 + gỡ sạch."
exit 0
