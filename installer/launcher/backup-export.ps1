# installer/launcher/backup-export.ps1
# Sao lưu (export) TOÀN BỘ dữ liệu SupplyCore ra ngoài Windows — mức file, đơn giản & chắc chắn.
#
# Bản chất: dừng dịch vụ "SupplyCore" (nhả khoá file qcow2 + VM tắt sạch → ổ đĩa nhất quán trên
# đĩa), copy ổ dữ liệu bền `disk1.qcow2` (MariaDB + sites + backup hằng ngày trong guest) ra một
# thư mục đích, rồi khởi động lại dịch vụ nếu trước đó nó đang chạy. KHÔNG cần shell vào VM.
#
# Chạy từ Start Menu ("Sao lưu SupplyCore") không cần tham số: DestDir mặc định = <SC_DATA>\exports.
# Cần quyền Administrator (điều khiển dịch vụ) — script tự nâng quyền (UAC) nếu chưa có.
#
#   backup-export.ps1 [-DestDir <thư-mục-đích>]

param(
  [string]$DestDir
)

$ErrorActionPreference = 'Stop'

# --- 0) Tự nâng quyền Administrator (UAC) nếu chưa có ---
$identity  = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Write-Host "Cần quyền Administrator — đang yêu cầu nâng quyền (UAC)..."
  $relaunch = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath)
  if ($PSBoundParameters.ContainsKey('DestDir')) { $relaunch += @('-DestDir', $DestDir) }
  Start-Process -FilePath 'powershell.exe' -ArgumentList $relaunch -Verb RunAs
  exit
}

# MessageBox: shortcut Start Menu tự nâng quyền → mở cửa sổ powershell MỚI rồi tự đóng khi script
# kết thúc, nên Write-Host sẽ biến mất. MsgBox đảm bảo IT luôn thấy kết quả/lỗi cuối cùng.
Add-Type -AssemblyName System.Windows.Forms

# --- 1) Phân giải thư mục dữ liệu + disk1 ---
$dataDir = if ($env:SC_DATA) { $env:SC_DATA } else { 'C:\ProgramData\SupplyCore' }
$disk1   = Join-Path $dataDir 'disk1.qcow2'
if (-not (Test-Path -LiteralPath $disk1)) {
  throw "Không tìm thấy ổ dữ liệu: $disk1 — chưa cài SupplyCore hoặc SC_DATA sai?"
}

# DestDir mặc định = <dataDir>\exports (để shortcut chạy không cần tham số).
if (-not $DestDir) { $DestDir = Join-Path $dataDir 'exports' }
if (-not (Test-Path -LiteralPath $DestDir)) {
  New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
}

$serviceName = 'SupplyCore'
$svc = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if (-not $svc) { throw "Không tìm thấy dịch vụ Windows '$serviceName' — chưa cài SupplyCore?" }
$wasRunning = ($svc.Status -eq 'Running')

try {
  # --- 2) Dừng dịch vụ + chờ Stopped (nhả khoá qcow2 → copy nhất quán) ---
  if ($svc.Status -ne 'Stopped') {
    Write-Host "Dừng dịch vụ $serviceName để sao lưu nhất quán..."
    Stop-Service -Name $serviceName -Force -ErrorAction Stop
    $deadline = (Get-Date).AddSeconds(120)
    do {
      Start-Sleep -Seconds 2
      $svc.Refresh()
    } while ($svc.Status -ne 'Stopped' -and (Get-Date) -lt $deadline)
    if ($svc.Status -ne 'Stopped') {
      throw "Dịch vụ $serviceName không dừng được trong 120 giây (trạng thái: $($svc.Status))."
    }
  }

  # --- 3) Copy disk1.qcow2 → tên có dấu thời gian ---
  $stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
  $dest   = Join-Path $DestDir "supplycore-data-$stamp.qcow2"
  Write-Host "Đang sao chép $disk1 -> $dest (có thể mất vài phút)..."
  Copy-Item -LiteralPath $disk1 -Destination $dest -Force
  if (-not (Test-Path -LiteralPath $dest)) {
    throw "Sao chép thất bại — không thấy file đích: $dest"
  }
  Write-Host ""
  Write-Host "Sao lưu thành công:"
  Write-Host "  $dest"
  Write-Host "Hãy chép file này sang nơi an toàn (USB / ổ mạng) để giữ ngoài máy."
  [System.Windows.Forms.MessageBox]::Show(
    "Sao lưu thành công.`n`nFile:`n$dest`n`nHãy chép file này sang nơi an toàn (USB / ổ mạng).",
    'SupplyCore - Sao lưu', 'OK', 'Information') | Out-Null
}
catch {
  [System.Windows.Forms.MessageBox]::Show(
    "Sao lưu THẤT BẠI:`n`n$($_.Exception.Message)",
    'SupplyCore - Sao lưu', 'OK', 'Error') | Out-Null
  throw
}
finally {
  # --- 4) Luôn khởi động lại dịch vụ NẾU trước đó nó đang chạy ---
  if ($wasRunning -and $svc.Status -ne 'Running') {
    Write-Host "Khởi động lại dịch vụ $serviceName..."
    Start-Service -Name $serviceName -ErrorAction SilentlyContinue
  }
}
